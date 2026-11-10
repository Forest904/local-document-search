"""T26: la destinazione segue le pagine del testo effettivamente indicizzato."""
import sqlite3

from local_document_search.application.contracts import SearchRequest
from local_document_search.application.ports import Extracted
from local_document_search.application.search import SearchDocuments
from local_document_search.application.synchronization import BuildIndex
from local_document_search.domain.queries import SearchField
from local_document_search.infrastructure.filesystem import DocumentFileDiscovery
from local_document_search.infrastructure.readers.pdf import PdfReader
from local_document_search.infrastructure.snapshot_storage import InMemorySnapshotRepository
from local_document_search.infrastructure.v2_snapshot_storage import V2SqliteSnapshotRepository
from local_document_search.interfaces.composition import compose_v2_application

from test_multiformat import make_pdf, candidate


def test_reader_preserves_empty_pages_and_search_destinations(tmp_path):
    make_pdf(tmp_path / "alpha.pdf", ["alpha", None, "beta", "alpha beta"])
    read = PdfReader().read(candidate(tmp_path, "alpha.pdf"))
    assert isinstance(read, Extracted)
    pages = read.document.pdf_pages
    assert len(pages) == 4
    assert pages[1].start == pages[1].end
    assert read.document.content[pages[2].start:pages[2].end].strip() == "beta"

    repo = InMemorySnapshotRepository()
    BuildIndex(DocumentFileDiscovery(), PdfReader(), repo).execute(str(tmp_path))
    search = SearchDocuments(repo)
    def page(query, field=SearchField.CONTENT, wildcards=False):
        return search.execute(SearchRequest(query, field, allow_wildcards=wildcards)).results[0].pdf_target_page

    assert page("beta") == 2
    assert page("alpha beta") == 0
    assert page('"alpha beta"') == 0  # La frase attraversa anche pagine vuote.
    assert page('"beta alpha"') == 2
    assert page("bet*", wildcards=True) == 2
    assert page("*eta", wildcards=True) == 2
    assert page("alpha", SearchField.FILENAME) == 0
    assert page("beta", SearchField.BOTH) == 2


def test_pdf_map_survives_v2_sqlite_round_trip(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    make_pdf(root / "sample.pdf", [None, "middle", None, "last"])
    memory = InMemorySnapshotRepository()
    snapshot = BuildIndex(DocumentFileDiscovery(), PdfReader(), memory).execute(str(root))
    with memory.acquire() as built:
        from dataclasses import replace
        persisted = replace(built, schema_version="3")
    storage = tmp_path / "storage"
    repo = V2SqliteSnapshotRepository(storage)
    try:
        repo.save_candidate(persisted)
        repo.validate_candidate(persisted.snapshot_id)
        repo.activate(persisted.snapshot_id)
    finally:
        repo.close()
    reopened = V2SqliteSnapshotRepository(storage)
    try:
        result = SearchDocuments(reopened).execute(SearchRequest("last")).results[0]
        assert result.pdf_target_page == 3
    finally:
        reopened.close()
    database = storage / "snapshots-v2.sqlite3"
    with sqlite3.connect(database) as db:
        db.execute("UPDATE versions SET pdf_pages='[[0,999999]]'")
    corrupted = V2SqliteSnapshotRepository(storage)
    try:
        assert corrupted.recovery_needed
        assert corrupted.load_active() is None
    finally:
        corrupted.close()


def test_pdf_page_map_tracks_incremental_sync_and_restart(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    path = root / "sample.pdf"
    make_pdf(path, ["alpha", "beta"])
    storage = tmp_path / "data"
    with compose_v2_application(storage, read_workers=1) as app:
        first = app.select_directory.execute(str(root)).job
        app._lifecycle.jobs.wait(first.job_id)
        assert app.search.execute(SearchRequest("beta")).results[0].pdf_target_page == 1
        make_pdf(path, ["beta", None, "alpha", "gamma"])
        second = app.request_synchronization.execute()
        app._lifecycle.jobs.wait(second.job_id)
        assert app.search.execute(SearchRequest("alpha")).results[0].pdf_target_page == 2
    with compose_v2_application(storage, read_workers=1) as reopened:
        reopened.initialize.execute()
        assert reopened.search.execute(SearchRequest("alpha")).results[0].pdf_target_page == 2
