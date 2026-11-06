"""Lifecycle bloccante M6; worker e job asincroni restano in M7."""
from datetime import datetime, timezone
from .contracts import ApplicationState, InvalidInput
from .errors import SourceUnavailable, SnapshotUnavailable
from .ports import (Settings, LastCheck, SyncOutcome, SettingsRepositoryPort,
                    LifecycleSnapshotRepositoryPort, DirectoryResolverPort)
from .synchronization import IndexSynchronizer


class ApplicationLifecycle:
    def __init__(self, settings: SettingsRepositoryPort, snapshots: LifecycleSnapshotRepositoryPort,
                 synchronizer: IndexSynchronizer, resolve_directory: DirectoryResolverPort):
        self.settings = settings
        self.snapshots = snapshots
        self.synchronizer = synchronizer
        self.resolve_directory = resolve_directory
        self.running = False
        self.warning = None

    def _idle(self):
        if self.running:
            raise InvalidInput("Operazione di sincronizzazione in corso")

    def status(self):
        settings = self.settings.load()
        snapshot = self.snapshots.load_active()
        available = snapshot is not None and snapshot.root_directory == settings.active_directory
        return ApplicationState(settings.active_directory, snapshot.snapshot_id if available else None,
                                available, self.warning,
                                settings.last_check.outcome.value if settings.last_check else None)

    def synchronize(self, trigger="manual"):
        self._idle()
        settings = self.settings.load()
        if settings.active_directory is None:
            raise InvalidInput("Nessuna directory selezionata")
        self.running = True
        self.warning = None
        try:
            result = self.synchronizer.execute(settings.active_directory)
            outcome = SyncOutcome.UPDATED if result.changed else SyncOutcome.NO_CHANGES
            self.settings.save(Settings(settings.active_directory,
                               LastCheck(datetime.now(timezone.utc), outcome)))
            return result
        except Exception as exc:
            self.warning = type(exc).__name__
            try:
                self.settings.save(Settings(settings.active_directory,
                                   LastCheck(datetime.now(timezone.utc), SyncOutcome.FAILED,
                                             type(exc).__name__)))
            except Exception as diagnostic_error:
                exc.add_note(f"Salvataggio diagnostica fallito: {diagnostic_error}")
            raise
        finally:
            self.running = False

    def initialize(self):
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
        if settings.active_directory:
            try:
                self.synchronize("startup")
            except SourceUnavailable:
                if self.snapshots.incompatible:
                    raise
        return self.status()

    def select(self, directory):
        self._idle()
        root = self.resolve_directory(directory)
        previous = self.settings.load()
        if root != previous.active_directory:
            self.snapshots.select_directory(root)
            self.settings.save(Settings(root))
        self.synchronize("select")
        return self.status()

    def clear(self):
        self._idle()
        self.snapshots.clear()
        self.warning = None
        return self.status()


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
