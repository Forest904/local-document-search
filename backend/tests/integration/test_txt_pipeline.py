"""Contratti adapter e pipeline reale TXT, con fault injection."""
import os
from pathlib import Path
import stat
import subprocess
from types import SimpleNamespace

import pytest

from local_document_search.application.contracts import InvalidInput, SearchRequest
from local_document_search.application.errors import (
    ExtractionFailure, ResourceFailure, SnapshotUnavailable, SourceUnavailable, StorageFailure,
)
from local_document_search.application.ports import Excluded, ExtractionFailed
from local_document_search.application.search import SearchDocuments
from local_document_search.application.synchronization import BuildIndex
from local_document_search.infrastructure import filesystem
from local_document_search.infrastructure.filesystem import DocumentFileDiscovery, TextFileDiscovery, resolve_directory
from local_document_search.infrastructure.readers.text import TextReader
from local_document_search.infrastructure.snapshot_storage import InMemorySnapshotRepository
from local_document_search.interfaces.composition import compose_cli


def write(root, name, content="roma tre"):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def pipeline():
    repo = InMemorySnapshotRepository()
    return repo, BuildIndex(TextFileDiscovery(), TextReader(), repo), SearchDocuments(repo)


def test_discovery_preserves_paths_and_orders_txt_only(tmp_path):
    for name in ("z.TXT", "sub/a.txt", "a.txt", "caffè.txt", "caffe.txt", "skip.md"):
        write(tmp_path, name)
    found = TextFileDiscovery().discover(str(tmp_path))
    assert [c.metadata.relative_path.value for c in found] == [
        "a.txt", "caffe.txt", "caffè.txt", "sub/a.txt", "z.TXT",
    ]
    assert all(c.root_directory == str(tmp_path.resolve()) for c in found)
    assert all(c.metadata.fingerprint.size_bytes == 8 for c in found)


def test_hard_links_have_distinct_document_ids(tmp_path):
    source = write(tmp_path, "a.txt")
    try:
        os.link(source, tmp_path / "b.txt")
    except OSError as exc:
        pytest.skip(f"Hard link non disponibili: {exc}")
    app = compose_cli(str(tmp_path))
    app.build.execute(app.root_directory)
    results = app.search.execute(SearchRequest("roma")).results
    assert len({r.document_id for r in results}) == 2
    assert [r.relative_path.value for r in results] == ["a.txt", "b.txt"]


@pytest.mark.parametrize("kind", ["file", "directory"])
@pytest.mark.parametrize("discovery_class", [TextFileDiscovery, DocumentFileDiscovery])
def test_symlinks_are_skipped_and_root_links_rejected(tmp_path, discovery_class, kind):
    source = tmp_path / "source"
    source.mkdir()
    file = write(source, "a.txt")
    root = tmp_path / "root"
    root.mkdir()
    link = root / ("link.txt" if kind == "file" else "link")
    try:
        link.symlink_to(file if kind == "file" else source, target_is_directory=kind == "directory")
    except OSError as exc:
        pytest.skip(f"Creazione symlink non consentita: {exc}")
    assert discovery_class().discover(str(root)) == ()
    with pytest.raises(InvalidInput):
        resolve_directory(str(link))
    if kind == "directory":
        with pytest.raises(InvalidInput):
            resolve_directory(str(link / ".."))


@pytest.mark.skipif(os.name != "nt", reason="Junction specifica di Windows")
@pytest.mark.parametrize("discovery_class", [TextFileDiscovery, DocumentFileDiscovery])
def test_junction_is_skipped_and_cannot_be_root(tmp_path, discovery_class):
    source = tmp_path / "source"
    source.mkdir()
    write(source, "a.txt")
    root = tmp_path / "root"
    root.mkdir()
    link = root / "junction"
    # Creazione nativa; rimozione non ricorsiva della sola junction nel finally.
    script = "New-Item -ItemType Junction -Path $env:M3_LINK -Target $env:M3_TARGET | Out-Null"
    env = dict(os.environ, M3_LINK=str(link), M3_TARGET=str(source))
    result = subprocess.run(["powershell", "-NoProfile", "-Command", script], env=env,
                            capture_output=True, text=True)
    if result.returncode:
        pytest.skip(f"Junction non disponibile: {result.stderr}")
    try:
        assert discovery_class().discover(str(root)) == ()
        with pytest.raises(InvalidInput):
            resolve_directory(str(link))
    finally:
        os.rmdir(link)
    assert (source / "a.txt").exists()


def test_reparse_attribute_is_recognized():
    assert filesystem._is_link(SimpleNamespace(
        st_mode=stat.S_IFREG, st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT,
    ))


@pytest.mark.parametrize("names", [("A.txt", "a.txt"), ("é.txt", "e\u0301.txt")])
def test_distinct_case_and_unicode_when_filesystem_supports_it(tmp_path, names):
    for name in names:
        write(tmp_path, name)
    if len(list(tmp_path.iterdir())) != 2:
        pytest.skip("Filesystem non distingue questi nomi")
    assert [c.metadata.relative_path.value for c in TextFileDiscovery().discover(str(tmp_path))] == sorted(names)


def test_reader_bom_empty_and_newlines(tmp_path):
    (tmp_path / "bom.txt").write_bytes(b"\xef\xbb\xbfroma\r\ntre")
    write(tmp_path, "empty.txt", "")
    docs = [TextReader().read(c).document for c in TextFileDiscovery().discover(str(tmp_path))]
    assert [d.content for d in docs] == ["roma\r\ntre", ""]


def test_reader_missing_file_is_failure(tmp_path):
    file = write(tmp_path, "a.txt")
    candidate, = TextFileDiscovery().discover(str(tmp_path))
    file.unlink()
    assert isinstance(TextReader().read(candidate), ExtractionFailed)


def test_empty_directory_publishes_searchable_empty_snapshot(tmp_path):
    app = compose_cli(str(tmp_path))
    report = app.build.execute(app.root_directory)
    response = app.search.execute(SearchRequest("roma"))
    assert (report.discovered, report.indexed, report.excluded, report.processed_bytes) == (0, 0, 0, 0)
    assert response.total_matches == 0
    assert response.snapshot_id == report.snapshot_id


def test_invalid_utf8_preserves_previous_and_allows_retry(tmp_path):
    write(tmp_path, "a.txt")
    repo, build, search = pipeline()
    first = build.execute(str(tmp_path))
    write(tmp_path, "b.txt", "new")
    bad = tmp_path / "z.txt"
    bad.write_bytes(b"\xff")
    with pytest.raises(ExtractionFailure):
        build.execute(str(tmp_path))
    assert repo.load_active().snapshot_id == first.snapshot_id
    assert search.execute(SearchRequest("new")).total_matches == 0
    bad.unlink()
    assert build.execute(str(tmp_path)).indexed == 2


@pytest.mark.parametrize("stage", ["save_candidate", "validate_candidate", "activate"])
def test_publication_failure_preserves_previous_and_discards_candidate(tmp_path, monkeypatch, stage):
    write(tmp_path, "a.txt")
    repo, build, _ = pipeline()
    first = build.execute(str(tmp_path))
    original = getattr(repo, stage)
    def fail(*args):
        if stage == "save_candidate":
            original(*args)
        raise OSError("simulated storage failure")
    monkeypatch.setattr(repo, stage, fail)
    with pytest.raises(StorageFailure):
        build.execute(str(tmp_path))
    assert repo.load_active().snapshot_id == first.snapshot_id
    monkeypatch.setattr(repo, stage, original)
    assert build.execute(str(tmp_path)).snapshot_id != first.snapshot_id


def test_repository_requires_validated_candidate_and_preserves_active(tmp_path):
    write(tmp_path, "a.txt")
    repo, build, _ = pipeline()
    build.execute(str(tmp_path))
    active = repo.load_active()
    other = InMemorySnapshotRepository()
    other.save_candidate(active)
    assert other.load_active() is None
    with pytest.raises(StorageFailure):
        other.activate(active.snapshot_id)
    with pytest.raises(StorageFailure):
        other.save_candidate(active)
    with pytest.raises(StorageFailure):
        other.validate_candidate("wrong")
    other.validate_candidate(active.snapshot_id)
    other.activate(active.snapshot_id)
    other.discard_candidate(active.snapshot_id)
    assert other.load_active() is active


@pytest.mark.parametrize("failure,expected", [(MemoryError, ResourceFailure), (RuntimeError, ExtractionFailure)])
def test_reader_unexpected_failure_preserves_previous(tmp_path, monkeypatch, failure, expected):
    write(tmp_path, "a.txt")
    repo, build, _ = pipeline()
    build.execute(str(tmp_path))
    active = repo.load_active()
    def fail(candidate):
        raise failure("simulated")
    monkeypatch.setattr(build.reader, "read", fail)
    with pytest.raises(expected):
        build.execute(str(tmp_path))
    assert repo.load_active() is active


def test_scanning_error_is_not_silent_exclusion(tmp_path, monkeypatch):
    write(tmp_path, "a.txt")
    repo, build, _ = pipeline()
    build.execute(str(tmp_path))
    active = repo.load_active()
    def fail(path):
        raise PermissionError("simulated")
    monkeypatch.setattr(filesystem.os, "scandir", fail)
    with pytest.raises(SourceUnavailable):
        build.execute(str(tmp_path))
    assert repo.load_active() is active


def test_excluded_result_remains_distinct_from_failure(tmp_path, monkeypatch):
    write(tmp_path, "a.txt")
    repo, build, search = pipeline()
    monkeypatch.setattr(build.reader, "read", lambda candidate: Excluded("synthetic exclusion"))
    result = build.execute(str(tmp_path))
    assert (result.indexed, result.excluded) == (0, 1)
    assert len(repo.load_active().manifest.entries) == 1
    assert search.execute(SearchRequest("a")).total_matches == 0


def test_search_requires_snapshot():
    with pytest.raises(SnapshotUnavailable):
        SearchDocuments(InMemorySnapshotRepository()).execute(SearchRequest("roma"))


@pytest.mark.parametrize("query", ['"', '""', '...', 'roma ""'])
def test_search_translates_invalid_query(tmp_path, query):
    app = compose_cli(str(tmp_path))
    app.build.execute(app.root_directory)
    with pytest.raises(InvalidInput):
        app.search.execute(SearchRequest(query))


def test_pagination_and_search_never_reread_sources(tmp_path):
    for i in range(53):
        write(tmp_path, f"{i:03}.txt")
    app = compose_cli(str(tmp_path))
    app.build.execute(app.root_directory)
    write(tmp_path, "000.txt", "changed")
    (tmp_path / "001.txt").unlink()
    first = app.search.execute(SearchRequest("roma"))
    second = app.search.execute(SearchRequest("roma", offset=50))
    beyond = app.search.execute(SearchRequest("roma", offset=100))
    assert (len(first.results), len(second.results), beyond.results) == (50, 3, ())
    assert first.total_matches == second.total_matches == beyond.total_matches == 53
    assert first.snapshot_id == second.snapshot_id == beyond.snapshot_id
    assert second.results[-1].relative_path.value == "052.txt"
    assert app.search.execute(SearchRequest("changed")).total_matches == 0


def test_search_acquires_active_once(tmp_path):
    write(tmp_path, "a.txt")
    repo, build, _ = pipeline()
    build.execute(str(tmp_path))
    snapshot = repo.load_active()
    class SingleReadRepository:
        calls = 0
        def load_active(self):
            self.calls += 1
            assert self.calls == 1
            return snapshot
    response = SearchDocuments(SingleReadRepository()).execute(SearchRequest("roma"))
    assert response.snapshot_id == snapshot.snapshot_id
    assert response.total_matches == 1


@pytest.mark.parametrize("mode,attributes", [
    (stat.S_IFLNK, 0),
    (stat.S_IFDIR, stat.FILE_ATTRIBUTE_REPARSE_POINT),
    (stat.S_IFREG, stat.FILE_ATTRIBUTE_REPARSE_POINT),
])
@pytest.mark.parametrize("discovery_class", [TextFileDiscovery, DocumentFileDiscovery])
def test_discovery_skips_link_entries_without_traversal(tmp_path, discovery_class, monkeypatch, mode, attributes):
    from contextlib import nullcontext
    entry = SimpleNamespace(stat=lambda **kwargs: SimpleNamespace(
        st_mode=mode, st_file_attributes=attributes,
    ))
    calls = []
    def scan(path):
        calls.append(path)
        return nullcontext(iter([entry]))
    monkeypatch.setattr(filesystem.os, "scandir", scan)
    assert discovery_class().discover(str(tmp_path)) == ()
    assert calls == [tmp_path]


def test_failed_first_build_has_no_active_snapshot(tmp_path):
    write(tmp_path, "a.txt")
    (tmp_path / "z.txt").write_bytes(b"\xff")
    repo, build, _ = pipeline()
    with pytest.raises(ExtractionFailure):
        build.execute(str(tmp_path))
    assert repo.load_active() is None


def test_memory_failure_during_publication_discards_candidate(tmp_path, monkeypatch):
    write(tmp_path, "a.txt")
    repo, build, _ = pipeline()
    build.execute(str(tmp_path))
    previous = repo.load_active()
    original = repo.validate_candidate
    def fail(snapshot_id):
        raise MemoryError
    monkeypatch.setattr(repo, "validate_candidate", fail)
    with pytest.raises(ResourceFailure):
        build.execute(str(tmp_path))
    assert repo.load_active() is previous
    monkeypatch.setattr(repo, "validate_candidate", original)
    build.execute(str(tmp_path))
    assert repo.load_active() is not previous
