"""Lifecycle persistente: ammissione serializzata, lavoro fuori dal chiamante."""
from datetime import datetime, timezone
from .contracts import ApplicationState, InvalidInput, JobState
from .errors import SnapshotUnavailable
from .ports import (Settings, LastCheck, SyncOutcome, SettingsRepositoryPort,
                    LifecycleSnapshotRepositoryPort, DirectoryResolverPort)
from .synchronization import IndexSynchronizer
from .jobs import IndexingJobManager, JobCancelled


class ApplicationLifecycle:
    def __init__(self, settings: SettingsRepositoryPort, snapshots: LifecycleSnapshotRepositoryPort,
                 synchronizer: IndexSynchronizer, resolve_directory: DirectoryResolverPort):
        self.settings = settings
        self.snapshots = snapshots
        self.synchronizer = synchronizer
        self.resolve_directory = resolve_directory
        self.jobs = IndexingJobManager()
        self.warning = None

    def _idle(self):
        self.jobs.ensure_open()
        if self.jobs.active:
            raise InvalidInput("Operazione di sincronizzazione in corso")

    def status(self):
        with self.jobs.lock:
            self.jobs.ensure_open()
            settings = self.settings.load()
            snapshot = self.snapshots.load_active()
            available = snapshot is not None and snapshot.root_directory == settings.active_directory
            return ApplicationState(settings.active_directory, snapshot.snapshot_id if available else None,
                                    available, self.warning,
                                    settings.last_check.outcome.value if settings.last_check else None,
                                    self.jobs.current())

    def request(self, trigger="manual"):
        with self.jobs.lock:
            self.jobs.ensure_open()
            if getattr(getattr(self.snapshots, "allocator", None), "legacy", False):
                raise InvalidInput("Dati precedenti: eseguire Elimina dati locali prima della sincronizzazione")
            if trigger not in ("manual", "startup", "select"):
                raise InvalidInput("Trigger non valido")
            settings = self.settings.load()
            if settings.active_directory is None:
                raise InvalidInput("Nessuna directory selezionata")
            job = self.jobs.request(lambda progress: self._synchronize(settings, progress))
            if not job.reused:
                self.warning = None
            return job

    def synchronize(self, trigger="manual"):
        job = self.request(trigger)
        return self.jobs.wait(job.job_id)

    def _synchronize(self, settings, progress, *, force=False):
        with self.jobs.lock:
            self.warning = None
        try:
            result = self.synchronizer.execute(settings.active_directory, progress, force=force)
            outcome = SyncOutcome.UPDATED if result.changed else SyncOutcome.NO_CHANGES
            self.settings.save(Settings(settings.active_directory,
                               LastCheck(datetime.now(timezone.utc), outcome)))
            return result
        except JobCancelled:
            self.settings.save(Settings(settings.active_directory,
                               LastCheck(datetime.now(timezone.utc), SyncOutcome.CANCELLED)))
            raise
        except Exception as exc:
            with self.jobs.lock:
                self.warning = type(exc).__name__
            try:
                self.settings.save(Settings(settings.active_directory,
                                   LastCheck(datetime.now(timezone.utc), SyncOutcome.FAILED,
                                             type(exc).__name__)))
            except Exception as diagnostic_error:
                exc.add_note(f"Salvataggio diagnostica fallito: {diagnostic_error}")
            raise

    def initialize(self):
        with self.jobs.lock:
            self._idle()
            settings = self.settings.load()
            snapshot = self.snapshots.load_active()
            # Storage M5 non aveva settings: recuperare la directory dal manifest.
            if settings.active_directory is None and snapshot is not None:
                settings = Settings(snapshot.root_directory)
                self.settings.save(settings)
            if snapshot and snapshot.root_directory != settings.active_directory:
                self.snapshots.select_directory(settings.active_directory)
            if settings.active_directory is None and self.snapshots.incompatible:
                raise SnapshotUnavailable("Storage incompatibile senza directory salvata: selezionare la sorgente")
            if (settings.active_directory and not (getattr(self.snapshots, "v2", False)
                    and self.snapshots.recovery_needed)
                    and not getattr(getattr(self.snapshots, "allocator", None), "legacy", False)):
                self.request("startup")
            elif getattr(getattr(self.snapshots, "allocator", None), "legacy", False):
                self.warning = "Dati precedenti: eseguire Elimina dati locali prima della sincronizzazione"
            return self.status()

    def select(self, directory):
        with self.jobs.lock:
            self._idle()
            if getattr(getattr(self.snapshots, "allocator", None), "legacy", False):
                raise InvalidInput("Dati precedenti: eseguire Elimina dati locali prima della sincronizzazione")
            root = self.resolve_directory(directory)
            previous = self.settings.load()
            if root != previous.active_directory:
                self.snapshots.select_directory(root)
                self.settings.save(Settings(root))
            self.request("select")
            return self.status()

    def clear(self):
        with self.jobs.lock:
            self._idle()
            self.snapshots.clear()
            self.warning = None
            self.jobs.forget_current()
            return self.status()

    def rebuild(self):
        with self.jobs.lock:
            self._idle()
            settings = self.settings.load()
            if settings.active_directory is None:
                raise InvalidInput("Nessuna directory selezionata")
            return self.jobs.request(lambda progress: self._synchronize(settings, progress, force=True))

    def recover_previous(self):
        with self.jobs.lock:
            self._idle()
            root = self.settings.load().active_directory
            if root is None:
                raise InvalidInput("Nessuna directory selezionata")
            key = self.snapshots.recover_previous(root)
            self.warning = None
            return key


class InitializeApplication:
    def __init__(self, lifecycle):
        self.lifecycle = lifecycle

    def execute(self):
        return self.lifecycle.initialize()


class SelectDirectory:
    def __init__(self, lifecycle):
        self.lifecycle = lifecycle

    def execute(self, absolute_path):
        return self.lifecycle.select(absolute_path)


class RunSynchronization:
    def __init__(self, lifecycle):
        self.lifecycle = lifecycle

    def execute(self, trigger="manual"):
        return self.lifecycle.synchronize(trigger)


class GetIndexStatus:
    def __init__(self, lifecycle):
        self.lifecycle = lifecycle

    def execute(self):
        return self.lifecycle.status()


class ClearLocalData:
    def __init__(self, lifecycle):
        self.lifecycle = lifecycle

    def execute(self):
        return self.lifecycle.clear()


class RebuildIndex:
    def __init__(self, lifecycle):
        self.lifecycle = lifecycle

    def execute(self):
        return self.lifecycle.rebuild()


class RecoverPreviousSnapshot:
    def __init__(self, lifecycle):
        self.lifecycle = lifecycle

    def execute(self):
        return self.lifecycle.recover_previous()
