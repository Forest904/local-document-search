"""Verifica del cablaggio M1: sostituti locali, nessun adapter operativo."""
from local_document_search.application.ports import (
    Extracted, FileCandidate, Settings,
)
from local_document_search.domain.documents import (
    CanonicalDocument, DocumentFormat, DocumentMetadata, FileFingerprint, RelativePath,
)
from local_document_search.interfaces.composition import compose_application


class DiscoveryStub:
    def __init__(self, candidate):
        self.candidate = candidate
        self.calls = []

    def discover(self, root_directory):
        self.calls.append(root_directory)
        return (self.candidate,)


class ReaderStub:
    def read(self, candidate):
        return Extracted(CanonicalDocument(candidate.metadata, "synthetic"))


class SnapshotsStub:
    def load_active(self):
        raise NotImplementedError("Non usato dal cablaggio")

    def save_candidate(self, snapshot):
        raise NotImplementedError

    def validate_candidate(self, snapshot_id):
        raise NotImplementedError

    def activate(self, snapshot_id):
        raise NotImplementedError

    def discard_candidate(self, snapshot_id):
        raise NotImplementedError


class SettingsStub:
    def load(self):
        return Settings()

    def save(self, settings):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


def test_composition_preserves_explicit_dependencies_without_io():
    root = "C:/synthetic"
    metadata = DocumentMetadata(RelativePath("a.txt"), "a.txt", DocumentFormat.TXT, FileFingerprint(9, 1))
    candidate = FileCandidate(root, metadata)
    discovery = DiscoveryStub(candidate)
    reader, snapshots, settings = ReaderStub(), SnapshotsStub(), SettingsStub()
    dependencies = compose_application(discovery=discovery, reader=reader, snapshots=snapshots, settings=settings)
    assert dependencies.discovery is discovery
    assert dependencies.reader is reader
    assert dependencies.snapshots is snapshots
    assert dependencies.settings is settings
    assert discovery.calls == []
    discovered = dependencies.discovery.discover(root)
    assert dependencies.reader.read(discovered[0]).document.content == "synthetic"
    assert dependencies.settings.load().active_directory is None
