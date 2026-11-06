"""Contratti M4 con documenti sintetici reali e regressioni della pipeline."""
from types import SimpleNamespace

import pytest
from pypdf import PdfWriter
from pypdf.generic import (
    DecodedStreamObject, DictionaryObject, NameObject, NumberObject,
)

from local_document_search.application.contracts import SearchRequest
from local_document_search.application.errors import ExtractionFailure, ResourceFailure
from local_document_search.application.ports import Extracted, Excluded, ExtractionFailed
from local_document_search.domain.documents import DocumentFormat
from local_document_search.domain.queries import SearchField
from local_document_search.infrastructure.filesystem import DocumentFileDiscovery, TextFileDiscovery
from local_document_search.infrastructure.readers.markdown import MarkdownReader
from local_document_search.infrastructure.readers.pdf import PdfReader
from local_document_search.infrastructure.readers.registry import DocumentReader
from local_document_search.interfaces.composition import compose_cli


def make_pdf(path, pages, password=None):
    """PDF minimo: Helvetica e una vera immagine RGB, senza librerie aggiuntive."""
    writer = PdfWriter()
    for text in pages:
        page = writer.add_blank_page(width=200, height=200)
        stream = DecodedStreamObject()
        if text is None:
            image = DecodedStreamObject()
            image.set_data(bytes([255, 0, 0]))
            image.update({NameObject('/Type'): NameObject('/XObject'),
                          NameObject('/Subtype'): NameObject('/Image'),
                          NameObject('/Width'): NumberObject(1),
                          NameObject('/Height'): NumberObject(1),
                          NameObject('/ColorSpace'): NameObject('/DeviceRGB'),
                          NameObject('/BitsPerComponent'): NumberObject(8)})
            page[NameObject('/Resources')] = DictionaryObject({
                NameObject('/XObject'): DictionaryObject({NameObject('/Im'): image}),
            })
            stream.set_data(b'q 100 0 0 100 10 10 cm /Im Do Q')
        else:
            font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                                     NameObject('/Subtype'): NameObject('/Type1'),
                                     NameObject('/BaseFont'): NameObject('/Helvetica')})
            page[NameObject('/Resources')] = DictionaryObject({
                NameObject('/Font'): DictionaryObject({NameObject('/F1'): font}),
            })
            stream.set_data(b'BT /F1 12 Tf 10 100 Td (' + text.encode('ascii') + b') Tj ET')
        page[NameObject('/Contents')] = stream
    if password is not None:
        writer.encrypt(password, owner_password='owner-secret', algorithm='RC4-128')
    writer.write(path)


def candidate(root, name):
    return next(c for c in DocumentFileDiscovery().discover(str(root))
                if c.metadata.relative_path.value == name)


@pytest.mark.parametrize('source,expected', [
    ('# Titolo\n\nParagrafo *corsivo* **forte**\n\n- uno\n- due',
     'Titolo Paragrafo corsivo forte uno due'),
    ('| primo | secondo |\n| --- | --- |\n| terzo | quarto |',
     'primo secondo terzo quarto'),
    ('[etichetta](https://invalid.test/segreto) ![alt *immagine*](missing.png) `codice`',
     'etichetta alt immagine codice'),
    ('prima\n\n```python\nsegreto\n```\n\ndopo\n\n    nascosto', 'prima dopo'),
    ('prima<b>visibile</b>dopo<!-- segreto -->fine', 'prima visibile dopo fine'),
    ('<div>nascosto</div>\n\nvisibile', 'visibile'),
    ('---\nsegreto: valore\n---\nvisibile', 'visibile'),
    ('---\nvisibile: valore', 'visibile: valore'),
    ('\ufeff# Caffè\r\n\r\nroma  \r\ntre', 'Caffè roma tre'),
    ('', ''),
    ('```\nsegreto\n```', ''),
    ('pa**ro**la', 'parola'),
    ('prima\n\n---\n\ndopo', 'prima dopo'),
])
def test_markdown_visible_text(tmp_path, source, expected):
    (tmp_path / 'doc.md').write_text(source, encoding='utf-8')
    result = MarkdownReader().read(candidate(tmp_path, 'doc.md'))
    assert isinstance(result, Extracted)
    assert ' '.join(result.document.content.split()) == expected


def test_markdown_invalid_utf8(tmp_path):
    (tmp_path / 'bad.md').write_bytes(b'\xff')
    result = MarkdownReader().read(candidate(tmp_path, 'bad.md'))
    assert isinstance(result, ExtractionFailed)
    assert 'bad.md' in result.reason


@pytest.mark.parametrize('pages,expected', [
    (['roma', 'tre'], 'roma\ntre'),
    (['roma', None, 'tre'], 'roma\n\ntre'),
    (['...'], '...'),
])
def test_pdf_text_and_page_order(tmp_path, pages, expected):
    make_pdf(tmp_path / 'doc.pdf', pages)
    result = PdfReader().read(candidate(tmp_path, 'doc.pdf'))
    assert isinstance(result, Extracted)
    assert result.document.content == expected


@pytest.mark.parametrize('pages', [[None], ['   '], [], ['', None]])
def test_pdf_without_text_is_excluded(tmp_path, pages):
    make_pdf(tmp_path / 'doc.pdf', pages)
    result = PdfReader().read(candidate(tmp_path, 'doc.pdf'))
    assert isinstance(result, Excluded)
    assert result.reason


@pytest.mark.parametrize('password,kind', [('secret', ExtractionFailed), ('', Extracted)])
def test_pdf_password_required_or_empty(tmp_path, password, kind):
    make_pdf(tmp_path / 'doc.pdf', ['roma'], password)
    assert isinstance(PdfReader().read(candidate(tmp_path, 'doc.pdf')), kind)


def test_corrupt_pdf_is_failure(tmp_path):
    (tmp_path / 'bad.pdf').write_bytes(b'%PDF-1.7\nbroken')
    result = PdfReader().read(candidate(tmp_path, 'bad.pdf'))
    assert isinstance(result, ExtractionFailed)
    assert 'bad.pdf' in result.reason


@pytest.mark.parametrize('name,reader', [('doc.md', MarkdownReader), ('doc.pdf', PdfReader)])
def test_missing_source_is_failure(tmp_path, name, reader):
    path = tmp_path / name
    path.touch()
    item = candidate(tmp_path, name)
    path.unlink()
    assert isinstance(reader().read(item), ExtractionFailed)


def test_discovery_multiformat_and_txt_compatibility(tmp_path):
    (tmp_path / 'sub').mkdir()
    for name in ['a.TXT', 'sub/a.MD', 'z.PdF', 'skip.docx']:
        (tmp_path / name).write_bytes(b'abc')
    found = DocumentFileDiscovery().discover(str(tmp_path))
    assert [(c.metadata.relative_path.value, c.metadata.format) for c in found] == [
        ('a.TXT', DocumentFormat.TXT), ('sub/a.MD', DocumentFormat.MARKDOWN),
        ('z.PdF', DocumentFormat.PDF),
    ]
    assert all(c.metadata.fingerprint.size_bytes == 3 for c in found)
    assert [c.metadata.relative_path.value for c in TextFileDiscovery().discover(str(tmp_path))] == ['a.TXT']


def test_unregistered_reader_is_failure(tmp_path):
    (tmp_path / 'a.md').touch()
    assert isinstance(DocumentReader({}).read(candidate(tmp_path, 'a.md')), ExtractionFailed)


def test_mixed_pipeline_manifest_and_search(tmp_path):
    (tmp_path / 'a.txt').write_text('roma tre', encoding='utf-8')
    (tmp_path / 'b.md').write_text('# roma\n\ntre', encoding='utf-8')
    (tmp_path / 'vuoto.md').write_text('```\nnascosto\n```', encoding='utf-8')
    (tmp_path / 'vuoto.txt').touch()
    make_pdf(tmp_path / 'c.pdf', ['roma', None, 'tre'])
    make_pdf(tmp_path / 'immagine.pdf', [None])
    make_pdf(tmp_path / 'simboli.pdf', ['...'])
    app = compose_cli(str(tmp_path))
    report = app.build.execute(app.root_directory)
    assert (report.discovered, report.indexed, report.excluded) == (7, 6, 1)
    response = app.search.execute(SearchRequest('"roma tre"', SearchField.CONTENT))
    assert [r.relative_path.value for r in response.results] == ['a.txt', 'b.md', 'c.pdf']
    assert app.search.execute(SearchRequest('vuoto', SearchField.FILENAME)).total_matches == 2
    assert app.search.execute(SearchRequest('simboli')).total_matches == 1
    assert app.search.execute(SearchRequest('immagine')).total_matches == 0
    snapshot = app.build.snapshots.load_active()
    assert len(snapshot.manifest.entries) == 7
    assert len(snapshot.catalog.documents) == 6


@pytest.mark.parametrize('bad_name', ['z.md', 'z.pdf'])
@pytest.mark.parametrize('previous', [False, True])
def test_failed_build_never_publishes_partial_snapshot(tmp_path, bad_name, previous):
    (tmp_path / 'a.txt').write_text('prima', encoding='utf-8')
    app = compose_cli(str(tmp_path))
    if previous:
        app.build.execute(app.root_directory)
    active = app.build.snapshots.load_active()
    (tmp_path / 'a.txt').write_text('nuovo', encoding='utf-8')
    (tmp_path / bad_name).write_bytes(b'\xff')
    with pytest.raises(ExtractionFailure):
        app.build.execute(app.root_directory)
    assert app.build.snapshots.load_active() is active
    if previous:
        assert app.search.execute(SearchRequest('nuovo')).total_matches == 0


@pytest.mark.parametrize('error,expected', [(RuntimeError, ExtractionFailure), (MemoryError, ResourceFailure)])
def test_later_pdf_page_failure_preserves_snapshot(tmp_path, monkeypatch, error, expected):
    from local_document_search.infrastructure.readers import pdf
    make_pdf(tmp_path / 'doc.pdf', ['prima', 'seconda'])
    app = compose_cli(str(tmp_path))
    app.build.execute(app.root_directory)
    active = app.build.snapshots.load_active()
    def fail():
        raise error('errore seconda pagina')
    monkeypatch.setattr(pdf, 'Parser', lambda stream: SimpleNamespace(
        is_encrypted=False, pages=[SimpleNamespace(extract_text=lambda: 'nuovo'),
                                   SimpleNamespace(extract_text=fail)],
    ))
    with pytest.raises(expected):
        app.build.execute(app.root_directory)
    assert app.build.snapshots.load_active() is active
    assert app.search.execute(SearchRequest('nuovo')).total_matches == 0


def test_multiformat_console(tmp_path):
    from test_cli import run_cli
    (tmp_path / 'a.txt').write_text('roma', encoding='utf-8')
    (tmp_path / 'b.md').write_text('# roma', encoding='utf-8')
    make_pdf(tmp_path / 'c.pdf', ['roma'])
    make_pdf(tmp_path / 'image.pdf', [None])
    result = run_cli([str(tmp_path)], 'contenuto roma\n')
    assert result.returncode == 0, result.stderr
    assert 'indicizzati: 3; esclusi: 1' in result.stdout
    assert 'Risultati: 3' in result.stdout
    for name in ['a.txt', 'b.md', 'c.pdf']:
        assert f'{name} [contenuto]' in result.stdout
