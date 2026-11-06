"""Errori operativi dei casi d'uso e degli adapter."""
class ApplicationError(Exception):
    """Operazione non completata, con diagnostica per l'interfaccia."""


class SourceUnavailable(ApplicationError):
    pass


class ExtractionFailure(ApplicationError):
    pass


class StorageFailure(ApplicationError):
    pass


class ResourceFailure(ApplicationError):
    pass


class SnapshotUnavailable(ApplicationError):
    pass
