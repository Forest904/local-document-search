"""Il reader del sorgente non modifica la ricerca e conserva la provenienza."""
import pytest

from local_document_search.application.contracts import SearchRequest
from local_document_search.application.text_view import TextViewRequest
from local_document_search.domain.queries import SearchField
from local_document_search.infrastructure.text_view_source import (
    TextViewChangedDuringRead, TextViewEncodingError, TextViewMissing,
    TextViewPermission, TextViewTooLarge,
)
from local_document_search.interfaces.composition import compose_cli


def _prepared(tmp_path, filename, source, query, *, field=SearchField.BOTH):
    root = tmp_path / "docs"
    root.mkdir()
    path = root / filename
    path.write_bytes(source.encode("utf-8"))
    app = compose_cli(str(root))
    app.build.execute(str(root))
    response = app.search.execute(SearchRequest(query, field=field, allow_wildcards=True))
    assert response.total_matches == 1
    result = response.results[0]
    from local_document_search.infrastructure.text_view_source import LocalTextViewSource
    request = TextViewRequest(str(root), result.relative_path, result.format,
                              response.snapshot_id, result.text_target)
    return path, result, request, LocalTextViewSource()


@pytest.mark.parametrize("source,query,expected", [
    ("foo **bar** baz", "bar", "bar"),
    ("---\ntitle: bar\n---\n# foo **bar**", "bar", "bar"),
    ("[foo](https://example.invalid/foo) foo", "foo", "foo"),
    ("![alt](image.png)", "alt", "alt"),
    ("foo&#98;ar", "foobar", "&#98;"),
    ("a\\*b", '"a b"', "\\*"),
    ("| A | B |\n|---|---|\n| foo | bar |", "bar", "bar"),
    ("| A | B |\n|---|---|\n| foo\\|bar | baz |", "bar", "bar"),
    ("> foo\n> bar", "bar", "bar"),
    ("- foo\n- bar", "bar", "bar"),
    ("`foo bar`", "bar", "bar"),
    ("`foo\nbar`", "bar", "bar"),
    ("`&amp;`", "amp", "amp"),
    ("foo\r\n**bar**", "bar", "bar"),
    ("foo\u2028bar", "bar", "bar"),
])
def test_markdown_source_target(tmp_path, source, query, expected):
    path, result, request, reader = _prepared(tmp_path, "note.md", source, query)
    document = reader.prepare(request)
    assert document.destination_status == "ready"
    assert expected in "".join(document.source[item.start:item.end] for item in document.source_ranges)


def test_txt_target_filename_only_and_changed_source(tmp_path):
    path, result, request, reader = _prepared(tmp_path, "alpha.txt", "😀 alpha\r\nbeta", "beta")
    assert result.text_target.canonical_range.start == len("😀 alpha\r\n")
    document = reader.prepare(request)
    assert document.source[document.source_ranges[0].start:document.source_ranges[0].end] == "beta"
    assert document.line_endings == "crlf"
    path.write_text("different beta", encoding="utf-8")
    changed = reader.prepare(request)
    assert changed.destination_status == "changed" and not changed.source_ranges

    root = tmp_path / "name"
    root.mkdir()
    (root / "alpha.txt").write_text("unrelated", encoding="utf-8")
    app = compose_cli(str(root))
    app.build.execute(str(root))
    response = app.search.execute(SearchRequest("alpha", SearchField.FILENAME))
    only_name = response.results[0]
    assert only_name.text_target.canonical_range is None


def test_text_view_limits_and_encoding(tmp_path):
    path, _, request, reader = _prepared(tmp_path, "alpha.txt", "alpha", "alpha")
    path.write_bytes(b"\xff")
    with pytest.raises(TextViewEncodingError):
        reader.prepare(request)
    path.write_bytes(b"x" * (10 * 1024 * 1024 + 1))
    with pytest.raises(TextViewTooLarge):
        reader.prepare(request)
    path.write_text("x" * 100_001, encoding="utf-8")
    with pytest.raises(TextViewTooLarge):
        reader.prepare(request)
    path.write_text("\n" * 100_000, encoding="utf-8")
    with pytest.raises(TextViewTooLarge):
        reader.prepare(request)
    path.write_bytes((b"x" * 99_999 + b"\n") * 104 + b"x" * 85_760)
    assert reader.prepare(request).destination_status == "changed"


def test_text_view_reports_missing_permissions_and_mid_read_change(tmp_path, monkeypatch):
    path, _, request, reader = _prepared(tmp_path, "alpha.txt", "alpha", "alpha")
    original_open = type(path).open

    def denied(self, *args, **kwargs):
        if self == path:
            raise PermissionError("denied")
        return original_open(self, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(type(path), "open", denied)
        with pytest.raises(TextViewPermission):
            reader.prepare(request)

    class ChangingStream:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self): return self
        def __exit__(self, *args): return self.stream.__exit__(*args)
        def fileno(self): return self.stream.fileno()
        def read(self, *args):
            data = self.stream.read(*args)
            with original_open(path, "wb") as writer:
                writer.write(b"alpha changed")
            return data

    def changed(self, *args, **kwargs):
        stream = original_open(self, *args, **kwargs)
        return ChangingStream(stream) if self == path else stream

    with monkeypatch.context() as patch:
        patch.setattr(type(path), "open", changed)
        with pytest.raises(TextViewChangedDuringRead):
            reader.prepare(request)
    path.unlink()
    with pytest.raises(TextViewMissing):
        reader.prepare(request)


def test_search_reads_snapshot_not_source(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    path = root / "alpha.txt"
    path.write_text("alpha beta", encoding="utf-8")
    app = compose_cli(str(root))
    app.build.execute(str(root))
    path.unlink()
    result = app.search.execute(SearchRequest("beta")).results[0]
    assert result.text_target.canonical_range is not None


def test_duplicate_table_cells_do_not_reuse_first_source_cell():
    from markdown_it import MarkdownIt
    from local_document_search.infrastructure.markdown_provenance import project_first_match
    from local_document_search.infrastructure.readers.markdown import _text
    source = "| A | B |\n|---|---|\n| foo | foo |"
    canonical = _text(MarkdownIt("commonmark").enable("table").parse(source))
    second = canonical.find("foo", canonical.find("foo") + 1)
    spans = project_first_match(source, second, second + 3)
    assert spans == ((source.rfind("foo"), len(source) - 2),)


def test_multichar_entity_maps_to_one_source_lexeme():
    from markdown_it import MarkdownIt
    from local_document_search.infrastructure.markdown_provenance import project_first_match
    from local_document_search.infrastructure.readers.markdown import _text
    source = "a&NotEqualTilde;b"
    canonical = _text(MarkdownIt("commonmark").enable("table").parse(source))
    assert project_first_match(source, canonical.index("≂"), canonical.index("b")) == (
        (1, len(source) - 1),)


def test_link_destination_is_never_used_as_following_visible_text():
    from markdown_it import MarkdownIt
    from local_document_search.infrastructure.markdown_provenance import project_first_match
    from local_document_search.infrastructure.readers.markdown import _text
    for source in ("[x](foo)foo", "![x](foo)foo", "[foo](foo)foo",
                   "<https://example.org/foo>foo"):
        canonical = _text(MarkdownIt("commonmark").enable("table").parse(source))
        target = canonical.rfind("foo")
        assert project_first_match(source, target, target + 3) == ((source.rfind("foo"), len(source)),)


def test_phrase_skips_markdown_syntax_and_and_uses_first_content_clause(tmp_path):
    path, result, request, reader = _prepared(tmp_path, "note.md", "beta then alpha **gamma**", "alpha beta")
    doc = reader.prepare(request)
    assert doc.source[doc.source_ranges[0].start:doc.source_ranges[0].end] == "beta"

    root = tmp_path / "other"
    root.mkdir()
    (root / "note.md").write_text("alpha **beta**", encoding="utf-8")
    app = compose_cli(str(root))
    app.build.execute(str(root))
    response = app.search.execute(SearchRequest('"alpha beta"'))
    item = response.results[0]
    from local_document_search.infrastructure.text_view_source import LocalTextViewSource
    prepared = LocalTextViewSource().prepare(TextViewRequest(str(root), item.relative_path, item.format,
                                                              response.snapshot_id, item.text_target))
    assert prepared.destination_status == "ready"
    assert "".join(prepared.source[span.start:span.end] for span in prepared.source_ranges) == "alpha beta"
