"""Regressioni piccole per la preparazione sperimentale Homework 3."""
import importlib.util
import json
from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, NumberObject, DecodedStreamObject


SCRIPT = Path(__file__).resolve().parents[3] / "experiments" / "homework3_corpus.py"
spec = importlib.util.spec_from_file_location("homework3_corpus", SCRIPT)
corpus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corpus)


def test_prepare_preserves_txt_and_reports_bad_encoding(tmp_path):
    source = tmp_path / "Uni"
    folder = source / "Esami" / "Corso"
    folder.mkdir(parents=True)
    (folder / "ok.txt").write_bytes(b"\xef\xbb\xbfCitta\n")
    (folder / "bad.txt").write_bytes(b"\xff")
    (source / "Daily Notes").mkdir()
    (source / "Daily Notes" / "private.txt").write_text("x")
    output = tmp_path / "prepared"
    manifest = corpus.prepare(source, output)
    assert not manifest["complete"]
    assert (output / "txt" / "txt" / "Esami" / "Corso" / "ok.txt").read_bytes() == b"\xef\xbb\xbfCitta\n"
    assert {entry["status"] for entry in manifest["entries"]} == {"converted", "reader_error"}
    with pytest.raises(ValueError, match="incompleta"):
        corpus.verify(output)


def test_synthetic_is_deterministic_and_detects_tampering(tmp_path, monkeypatch):
    monkeypatch.setitem(corpus.PROFILES, "smoke", (10, 300_000))
    first = corpus.synthetic(tmp_path / "one", "smoke")
    second = corpus.synthetic(tmp_path / "two", "smoke")
    assert first["corpus_id"] == second["corpus_id"]
    corpus.verify(tmp_path / "one")
    (tmp_path / "one" / "txt" / first["entries"][0]["path"]).write_text("tampered")
    with pytest.raises(ValueError, match="alterato"):
        corpus.verify(tmp_path / "one")


def make_pdf(path, text=False, protected=False):
    writer = PdfWriter()
    page = writer.add_blank_page(200, 200)
    image = DecodedStreamObject()
    image.set_data(b"\xff\x00\x00")
    image.update({NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Image"),
                  NameObject("/Width"): NumberObject(1), NameObject("/Height"): NumberObject(1),
                  NameObject("/ColorSpace"): NameObject("/DeviceRGB"), NameObject("/BitsPerComponent"): NumberObject(8)})
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}), NameObject("/XObject"): DictionaryObject({NameObject("/Im1"): writer._add_object(image)})})
    stream = DecodedStreamObject()
    stream.set_data(b"q 180 0 0 180 0 0 cm /Im1 Do Q\n" + (b"BT /F1 12 Tf 10 190 Td (Titolo) Tj ET" if text else b""))
    page[NameObject("/Contents")] = writer._add_object(stream)
    if protected:
        writer.encrypt("secret")
    with path.open("wb") as handle:
        writer.write(handle)


def mixed_corpus(tmp_path):
    source = tmp_path / "Uni"
    folder = source / "Esami"
    folder.mkdir(parents=True)
    make_pdf(folder / "slide.pdf", text=True)
    make_pdf(folder / "image.pdf")
    output = tmp_path / "prepared"
    return output, corpus.prepare(source, output)


def test_mixed_pdf_corpus_complete_independently_of_review(tmp_path):
    output, manifest = mixed_corpus(tmp_path)
    assert manifest["complete"]
    assert {e["status"] for e in manifest["entries"]} == {"converted", "pdf_no_text"}
    converted = next(e for e in manifest["entries"] if e["status"] == "converted")
    assert (output / converted["txt_path"]).read_text() == "Titolo"
    assert json.loads((output / "metadata/manual_review.json").read_text())["state"] == "pending"
    corpus.verify(output)


@pytest.mark.parametrize("kind", ["protected", "corrupt"])
def test_pdf_errors_prevent_completion(tmp_path, kind):
    source = tmp_path / "Uni"
    (source / "Esami").mkdir(parents=True)
    pdf = source / "Esami/problem.pdf"
    if kind == "protected":
        make_pdf(pdf, text=True, protected=True)
    else:
        pdf.write_bytes(b"broken PDF")
    manifest = corpus.prepare(source, tmp_path / "out")
    assert not manifest["complete"]
    assert manifest["entries"][0]["status"] == ("protected_pdf" if kind == "protected" else "reader_error")


@pytest.mark.parametrize("damage", ["missing_original", "altered_original", "extra_txt", "omitted_candidate", "scan_error"])
def test_verifier_checks_exclusions_and_inventory(tmp_path, damage):
    output, manifest = mixed_corpus(tmp_path)
    excluded = next(e for e in manifest["entries"] if e["status"] == "pdf_no_text")
    if damage == "missing_original":
        (output / excluded["original_path"]).unlink()
    elif damage == "altered_original":
        (output / excluded["original_path"]).write_bytes(b"altered")
    elif damage == "extra_txt":
        (output / "txt/extra.txt").write_text("extra")
    elif damage == "omitted_candidate":
        manifest["entries"].remove(excluded)
        corpus.write_json(output / "metadata/manifest.json", manifest)
    else:
        path = output / "metadata/inventory.json"
        data = json.loads(path.read_text())
        data["records"].append({"path": "unreadable", "status": "scan_error"})
        corpus.write_json(path, data)
    with pytest.raises(ValueError):
        corpus.verify(output)


def test_selection_preserves_provenance_without_txt(tmp_path):
    source, manifest = mixed_corpus(tmp_path)
    selected = next(e for e in manifest["entries"] if e["status"] == "converted")
    decisions = tmp_path / "decisions.json"
    corpus.write_json(decisions, {"schema": 1, "source_corpus_id": manifest["corpus_id"],
                      "decisions": [{"path": selected["path"], "action": "exclude",
                                     "reason": "Fixture non didattica", "author": "test"}]})
    destination = tmp_path / "new"
    result = corpus.select_prepared(source, destination, decisions)
    assert result["complete"]
    excluded = next(e for e in result["entries"] if e["path"] == selected["path"])
    assert excluded["status"] == "selection_excluded"
    assert "txt_path" not in excluded
    assert (destination / excluded["original_path"]).is_file()
    assert not list((destination / "txt").rglob("*.txt"))


def test_document_reproducibility_and_diversity():
    documents = [corpus.synthetic_document(i) for i in range(100)]
    assert documents == [corpus.synthetic_document(i) for i in range(100)]
    assert corpus.synthetic_document(0, 42) != documents[0]
    entries = [e for e, _ in documents]
    assert {(e["topic"], e["language"]) for e in entries} == {(t, l) for t in corpus.TOPICS for l in ("it", "en")}
    assert {e["structure"] for e in entries} == set(corpus.STRUCTURES)
    assert len({tuple(e["sections"]) for e in entries}) > 20
    assert len({e["path"].casefold() for e in entries}) == 100
    assert {e["target_bytes"] for e in entries} == set(corpus.SIZE_TARGETS)
    for e, data in documents:
        assert e["target_bytes"] <= len(data) < e["target_bytes"] + 600
        assert data.decode("utf-8").rstrip().endswith(".")
        assert len(set(data.decode("utf-8").splitlines())) > 15
    assert any(any(ord(c) > 127 for c in e["path"]) for e in entries)


def test_controlled_texts_without_product_analyzer():
    import re
    reserved = {w for case in corpus.FAMILIES.values() for key in ("filename", "content", "tail")
                for w in case.get(key, "").split()} - {"passaggio"}
    for i in range(100):
        entry, data = corpus.synthetic_document(i)
        name = set(re.findall(r"[^\W\d_]+", Path(entry["path"]).stem.lower()))
        text = data.decode("utf-8")
        tokens = re.findall(r"[^\W\d_]+", text.lower())
        content = set(tokens)
        case = corpus.FAMILIES[entry["family"]]
        assert name & reserved == set(case["filename"].split())
        assert content & reserved == (set((case["content"] + " " + case.get("tail", "")).split()) - {"passaggio"})
        assert not (name | content) & set(corpus.ABSENT_TERMS)
        if entry["family"] in {"consecutive", "interrupted", "reversed"}:
            left, right = tokens.index("frandilo"), tokens.index("spolvero")
            assert right - left == {"consecutive": 1, "interrupted": 2, "reversed": -1}[entry["family"]]
        if entry["family"] == "distant":
            assert tokens.index("remotivo") - tokens.index("distalvo") > 500
            assert "Appendice." in text


def test_nested_profiles_and_order_independent_identity(tmp_path, monkeypatch):
    for name, count in (("small", 10), ("medium", 20), ("large", 30)):
        monkeypatch.setitem(corpus.PROFILES, name, (count, count * 30000))
        corpus.synthetic(tmp_path / name, name)
    assert corpus.verify_nested([tmp_path / p for p in corpus.PROFILES])["nested"]
    small = corpus.verify(tmp_path / "small")
    medium = corpus.verify(tmp_path / "medium")
    assert small["entries"] == medium["entries"][:10]
    small["entries"].reverse()
    small["environment"] = {"different": "execution"}
    corpus.write_json(tmp_path / "small/manifest.json", small)
    corpus.verify(tmp_path / "small")
    with pytest.raises(FileExistsError):
        corpus.synthetic(tmp_path / "small", "small")
    corpus.synthetic(tmp_path / "other", "small", seed=42)
    with pytest.raises(ValueError, match="stesso seed"):
        corpus.verify_nested([tmp_path / p for p in ("other", "medium", "large")])


@pytest.mark.parametrize("damage", ["missing", "extra", "hash", "count", "entry_count", "volume", "metadata", "utf8", "bytes", "identity"])
def test_new_synthetic_rejects_damage(tmp_path, monkeypatch, damage):
    monkeypatch.setitem(corpus.PROFILES, "smoke", (10, 300_000))
    output = tmp_path / "corpus"
    manifest = corpus.synthetic(output, "smoke")
    entry = manifest["entries"][0]
    path = output / "txt" / entry["path"]
    if damage == "missing":
        path.unlink()
    elif damage == "extra":
        (output / "txt/extra.txt").write_text("extra")
    elif damage == "hash":
        entry["sha256"] = "0" * 64
    elif damage == "count":
        manifest["expected_count"] += 1
    elif damage == "entry_count":
        manifest["entries"].pop()
    elif damage == "volume":
        entry["bytes"] = 1_000_000
    elif damage == "metadata":
        entry["family"] = "distant"
    elif damage == "utf8":
        path.write_bytes(b"\xff")
    elif damage == "bytes":
        entry["bytes"] += 1
    else:
        manifest["corpus_id"] = "0" * 64
    corpus.write_json(output / "manifest.json", manifest)
    with pytest.raises(ValueError):
        corpus.verify(output)


def test_legacy_manifest_remains_verifiable(tmp_path):
    (tmp_path / "txt").mkdir()
    (tmp_path / "txt/old.txt").write_bytes(b"legacy")
    entries = [{"path": "old.txt", "bytes": 6, "sha256": corpus.digest(b"legacy")}]
    identity = corpus.digest(json.dumps([("old.txt", entries[0]["sha256"])], separators=(",", ":")).encode())
    corpus.write_json(tmp_path / "manifest.json", {"schema": 1, "profile": "small", "entries": entries, "corpus_id": identity})
    assert corpus.verify(tmp_path)["corpus_id"] == identity
