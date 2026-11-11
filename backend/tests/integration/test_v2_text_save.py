from concurrent.futures import ThreadPoolExecutor
from threading import Event
from types import SimpleNamespace
import os

import pytest

from local_document_search.application.text_view import SaveTextDocument, SaveTextRequest
from local_document_search.domain.documents import DocumentFormat, RelativePath
from local_document_search.infrastructure.text_view_source import (
    LocalTextViewSource, TextViewConflict, TextViewTooLarge, TextViewUnsafePath,
    TextViewUnavailable,
)
from local_document_search.application.jobs import IndexingJobManager


def request(root, path, original, text, *, bom=False):
    stat = path.stat()
    return SaveTextRequest(str(root), RelativePath(path.name), DocumentFormat.MARKDOWN,
                           text, original, bom,
                           (stat.st_size, stat.st_mtime_ns, stat.st_dev, stat.st_ino))


def test_save_preserves_bom_and_existing_mixed_endings(tmp_path):
    path = tmp_path / "note.md"
    original = "one\r\ntwo\nthree\r\n"
    path.write_bytes(b"\xef\xbb\xbf" + original.encode())
    result = SaveTextDocument(LocalTextViewSource()).execute(
        request(tmp_path, path, original, "one\ntwo\nnew\nthree\n", bom=True))
    assert path.read_bytes() == b"\xef\xbb\xbfone\r\ntwo\nnew\r\nthree\r\n"
    assert result.source == "one\r\ntwo\nnew\r\nthree\r\n"


def test_save_rejects_external_change_and_keeps_file(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("old", encoding="utf-8")
    pending = request(tmp_path, path, "old", "draft")
    path.write_text("external change", encoding="utf-8")
    with pytest.raises(TextViewConflict):
        SaveTextDocument(LocalTextViewSource()).execute(pending)
    assert path.read_text(encoding="utf-8") == "external change"


def test_save_enforces_limits_and_rejects_link(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("old", encoding="utf-8")
    with pytest.raises(TextViewTooLarge):
        SaveTextDocument(LocalTextViewSource()).execute(
            request(tmp_path, path, "old", "x" * 100_001))
    assert path.read_text(encoding="utf-8") == "old"
    link = tmp_path / "link.md"
    try:
        link.symlink_to(path)
    except OSError:
        pytest.skip("Symlink non disponibile in questa sessione")
    with pytest.raises(TextViewUnsafePath):
        SaveTextDocument(LocalTextViewSource()).execute(
            request(tmp_path, link, "old", "draft"))


def test_save_waits_for_job_then_requests_fresh_sync(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("old", encoding="utf-8")
    started, release = Event(), Event()
    jobs = IndexingJobManager()

    def running(_):
        started.set()
        release.wait(5)

    jobs.request(running)
    assert started.wait(2)
    calls = []
    lifecycle = SimpleNamespace(jobs=jobs,
                                settings=SimpleNamespace(load=lambda: SimpleNamespace(active_directory=str(tmp_path))),
                                request=lambda trigger: calls.append(trigger))
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(SaveTextDocument(LocalTextViewSource(), lifecycle).execute,
                             request(tmp_path, path, "old", "new"))
        assert not future.done()
        assert path.read_text(encoding="utf-8") == "old"
        release.set()
        result = future.result(timeout=5)
    jobs.close()
    assert path.read_text(encoding="utf-8") == "new"
    assert calls == ["manual"]
    assert result.sync_requested


def test_replace_failure_keeps_original_and_removes_temporary(tmp_path, monkeypatch):
    path = tmp_path / "note.md"
    path.write_text("old", encoding="utf-8")

    def fail_replace(*_):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(TextViewUnavailable):
        SaveTextDocument(LocalTextViewSource()).execute(request(tmp_path, path, "old", "new"))
    assert path.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.iterdir()) == [path]
