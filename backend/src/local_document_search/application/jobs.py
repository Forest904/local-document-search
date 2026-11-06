"""Un solo job di sincronizzazione; la modalità bloccante attende lo stesso lavoro."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from .contracts import InvalidInput, JobPhase, JobRef, JobState, JobStatus, JobReport, JobDiagnostic


class IndexingJobManager:
    def __init__(self):
        self.lock = RLock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="index-sync")
        self._statuses = {}
        self._futures = {}
        self._current = None
        self._closed = False

    @property
    def active(self):
        with self.lock:
            return self._current is not None and self._statuses[self._current].state in (
                JobState.PENDING, JobState.RUNNING)

    def ensure_open(self):
        if self._closed:
            raise InvalidInput("Sessione in chiusura o chiusa")

    def current(self):
        with self.lock:
            if self._current is None:
                return None
            status = self._statuses[self._current]
            return JobRef(status.job_id, status.state)

    def request(self, operation):
        with self.lock:
            self.ensure_open()
            if self.active:
                return replace(self.current(), reused=True)
            key = uuid4().hex
            self._statuses[key] = JobStatus(key, JobState.PENDING, JobPhase.SCANNING,
                                            datetime.now(timezone.utc))
            self._current = key
            try:
                self._futures[key] = self._executor.submit(self._run, key, operation)
            except BaseException:
                del self._statuses[key]
                self._current = None
                raise
            return JobRef(key, JobState.PENDING)

    def _run(self, key, operation):
        self._update(key, state=JobState.RUNNING)
        try:
            result = operation(lambda **changes: self._update(key, **changes))
        except BaseException as exc:
            prior = self.status(key)
            report = prior.report or JobReport((JobDiagnostic(type(exc).__name__, prior.phase,
                      prior.current_file, "Operazione fallita"),), complete=False)
            if report.complete:
                report = replace(report, complete=False, diagnostics=report.diagnostics + (
                    JobDiagnostic(type(exc).__name__, prior.phase, prior.current_file,
                                  "Aggiornamento dello stato operativo fallito"),))
            self._update(key, state=JobState.FAILED, error=type(exc).__name__,
                         report=report, finished_at=datetime.now(timezone.utc))
            raise
        self._update(key, state=JobState.COMPLETED, current_file=None,
                     finished_at=datetime.now(timezone.utc))
        return result

    def _update(self, key, **changes):
        with self.lock:
            self._statuses[key] = replace(self._statuses[key], **changes)

    def status(self, key):
        with self.lock:
            try:
                return self._statuses[key]
            except KeyError:
                raise InvalidInput("Job sconosciuto") from None

    def wait(self, key):
        with self.lock:
            self.status(key)
            future = self._futures[key]
        return future.result()

    def stop_accepting(self):
        with self.lock:
            self._closed = True

    def forget_current(self):
        with self.lock:
            if self.active:
                raise InvalidInput("Operazione di sincronizzazione in corso")
            self._current = None

    def close(self):
        self.stop_accepting()
        self._executor.shutdown(wait=True)


class RequestSynchronization:
    def __init__(self, lifecycle):
        self.lifecycle = lifecycle

    def execute(self, trigger="manual"):
        return self.lifecycle.request(trigger)


class GetJobStatus:
    def __init__(self, manager):
        self.manager = manager

    def execute(self, job_id):
        return self.manager.status(job_id)
