"""Corpus funzionale V2-01: generazione, acquisizione e confronto senza benchmark."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from urllib.request import Request, urlopen

from local_document_search.application.contracts import SearchRequest
from local_document_search.domain.queries import QueryParser, SearchField
from local_document_search.interfaces.composition import compose_cli

from m9_corpus import pdf_bytes
from run_homework3 import CORPUS as HOMEWORK_CORPUS


DATA = Path(__file__).with_name("v2_corpus")
REAL_MANIFEST = DATA / "real_manifest.json"
REAL_QUERIES = DATA / "real_queries.json"
SCHEMA = 1


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def corpus_id(manifest):
    return digest(canonical(manifest))


def safe_path(value):
    path = PurePosixPath(value)
    if (not value or value != path.as_posix() or path.is_absolute()
            or any(part in (".", "..") for part in value.split("/"))
            or ":" in value or "\\" in value):
        raise ValueError(f"Percorso non valido: {value!r}")
    return path


def local_path(source, relative):
    path = Path(source)
    for part in safe_path(relative).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f"Symlink nel corpus: {relative}")
    return path


def load_manifest(path=REAL_MANIFEST):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(manifest) != {"schema", "files"} or manifest["schema"] != SCHEMA:
        raise ValueError("Schema manifest non valido")
    files = manifest["files"]
    if not isinstance(files, list) or not 12 <= len(files) <= 30:
        raise ValueError("Il manifest reale richiede 12–30 file")
    paths, urls, languages, formats = set(), set(), set(), set()
    required = {"path", "source", "url", "license", "license_url", "language", "format", "sha256"}
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != required:
            raise ValueError("Campi del documento non validi")
        path = safe_path(entry["path"])
        if entry["path"] in paths or entry["url"] in urls:
            raise ValueError("Percorso o URL duplicato")
        paths.add(entry["path"])
        urls.add(entry["url"])
        for key in ("source", "license"):
            if not isinstance(entry[key], str) or not entry[key].strip():
                raise ValueError(f"{key} mancante")
        for key in ("url", "license_url"):
            if not isinstance(entry[key], str) or not entry[key].startswith("https://"):
                raise ValueError(f"{key} deve essere HTTPS")
        if not isinstance(entry["sha256"], str) or len(entry["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in entry["sha256"]):
            raise ValueError("SHA-256 non valido")
        if entry["language"] not in ("it", "en") or entry["format"] not in ("txt", "md", "pdf") or path.suffix.lower() != "." + entry["format"]:
            raise ValueError("Lingua o formato non valido")
        languages.add(entry["language"])
        formats.add(entry["format"])
    if languages != {"it", "en"} or formats != {"txt", "md", "pdf"}:
        raise ValueError("Copertura lingua/formato incompleta")
    return manifest


def load_queries(path, manifest):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(data) != {"schema", "corpus_id", "queries"} or data["schema"] != SCHEMA or data["corpus_id"] != corpus_id(manifest):
        raise ValueError("Schema o versione delle query non validi")
    paths = {entry["path"] for entry in manifest["files"]}
    queries = data["queries"]
    if not isinstance(queries, list) or not queries:
        raise ValueError("Lista delle query vuota")
    seen = set()
    for case in queries:
        if not isinstance(case, dict) or set(case) != {"query", "field", "expected", "ambiguities"}:
            raise ValueError("Campi query non validi")
        if not isinstance(case["query"], str) or not case["query"].strip() or case["field"] not in ("filename", "content", "both"):
            raise ValueError("Query o campo non valido")
        QueryParser().parse(case["query"], SearchField(case["field"]))
        key = (case["query"], case["field"])
        if key in seen:
            raise ValueError("Query duplicata")
        seen.add(key)
        expected = case["expected"]
        if not isinstance(expected, list) or any(not isinstance(item, str) or item not in paths for item in expected) or expected != sorted(set(expected)):
            raise ValueError("Attesi non validi, duplicati o non ordinati")
        if not isinstance(case["ambiguities"], list) or any(not isinstance(item, str) for item in case["ambiguities"]):
            raise ValueError("Ambiguità non valide")
    return data


def verify_files(manifest, source):
    source = Path(source)
    problems = []
    for entry in manifest["files"]:
        try:
            path = local_path(source, entry["path"])
        except ValueError:
            problems.append({"path": entry["path"], "reason": "symlink"})
            continue
        if not path.is_file():
            problems.append({"path": entry["path"], "reason": "mancante o symlink"})
        elif digest(path.read_bytes()) != entry["sha256"]:
            problems.append({"path": entry["path"], "reason": "hash diverso"})
    actual = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    for extra in sorted(actual - {entry["path"] for entry in manifest["files"]}):
        problems.append({"path": extra, "reason": "file non previsto"})
    return problems


def fetch(manifest, source):
    source = Path(source)
    source.mkdir(parents=True, exist_ok=True)
    diagnostics = []
    for entry in manifest["files"]:
        try:
            path = local_path(source, entry["path"])
        except ValueError:
            diagnostics.append({"path": entry["path"], "status": "invalid-cache", "reason": "symlink"})
            continue
        if path.is_file() and digest(path.read_bytes()) == entry["sha256"]:
            diagnostics.append({"path": entry["path"], "status": "cached"})
            continue
        if path.exists():
            diagnostics.append({"path": entry["path"], "status": "invalid-cache"})
            continue
        try:
            request = Request(entry["url"], headers={"User-Agent": "LocalDocumentSearchCorpus/0.1"})
            with urlopen(request, timeout=45) as response:
                data = response.read()
            if digest(data) != entry["sha256"]:
                diagnostics.append({"path": entry["path"], "status": "hash-mismatch"})
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            diagnostics.append({"path": entry["path"], "status": "downloaded"})
        except Exception as exc:
            diagnostics.append({"path": entry["path"], "status": "unavailable", "reason": str(exc)})
    return diagnostics


def synthetic():
    files = dict(HOMEWORK_CORPUS)
    files.update({
        "guide.md": "# Caffè e città\n\nAlfa **beta** gamma.\n\n```\nsegretoescluso\n```\n",
        "notes.md": "# Caffè\n\nBeta alfa.\n",
        "empty.md": "```\nsegretoescluso\n```\n",
        "manual.pdf": pdf_bytes("Alfa beta gamma. Caffe documento."),
        "second.pdf": pdf_bytes("Beta alfa documento."),
    })
    entries = [{"path": path, "sha256": digest(value if isinstance(value, bytes) else value.encode("utf-8"))} for path, value in sorted(files.items())]
    manifest = {"schema": SCHEMA, "files": entries}
    cases = [
        {"query": "caffè", "field": "content", "expected": ["Unicode2026.TXT", "guide.md", "notes.md"]},
        {"query": '"alfa beta"', "field": "content", "expected": ["guide.md", "manual.pdf"]},
        {"query": "alfa gamma", "field": "content", "expected": ["guide.md", "manual.pdf"]},
        {"query": "alfa beta", "field": "both", "expected": ["guide.md", "manual.pdf", "notes.md", "second.pdf"]},
        {"query": "guide", "field": "filename", "expected": ["guide.md"]},
        {"query": "guide alfa", "field": "both", "expected": []},
        {"query": "empty", "field": "filename", "expected": ["Empty.txt", "empty.md"]},
        {"query": '"data data"', "field": "content", "expected": ["RomaTre.txt"]},
        {"query": "segretoescluso", "field": "content", "expected": []},
        {"query": "nonpresente", "field": "both", "expected": []},
        {"query": "roma", "field": "filename", "expected": ["RomaTre.txt", "sub/RomaNote.txt"]},
    ]
    queries = {"schema": SCHEMA, "corpus_id": corpus_id(manifest), "queries": [dict(case, ambiguities=[]) for case in cases]}
    return files, manifest, queries


def generate_synthetic(destination):
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Destinazione sintetica non vuota")
    files, manifest, queries = synthetic()
    source = destination / "source"
    for name, value in files.items():
        path = source.joinpath(*safe_path(name).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else value.encode("utf-8"))
    (destination / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination / "queries.json").write_text(json.dumps(queries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest, queries


def revision():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def working_tree_dirty():
    try:
        return bool(subprocess.check_output(["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL).strip())
    except (OSError, subprocess.CalledProcessError):
        return None


def export_text(manifest, source, destination):
    problems = verify_files(manifest, source)
    if problems:
        raise ValueError(f"Corpus incompleto: {problems}")
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Destinazione dell'estrazione non vuota")
    app = compose_cli(str(Path(source).resolve()))
    build = app.build.execute(app.root_directory)
    if build.indexed != len(manifest["files"]) or build.excluded:
        raise ValueError("Corpus non interamente indicizzabile")
    snapshot = app.build.snapshots.load_active()
    destination.mkdir(parents=True, exist_ok=True)
    for document in snapshot.catalog.documents.values():
        relative = document.descriptor.metadata.relative_path.value
        output = destination.joinpath(*safe_path(relative).parts).with_suffix(".txt")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(document.extracted_text, encoding="utf-8")
    (destination / "corpus_id.txt").write_text(corpus_id(manifest) + "\n", encoding="utf-8")


def validate(manifest, queries, source):
    problems = verify_files(manifest, source)
    result = {"code_revision": revision(), "working_tree_dirty": working_tree_dirty(), "corpus_id": corpus_id(manifest), "query_sha256": digest(canonical(queries)), "complete": not problems, "problems": problems, "cases": []}
    if problems:
        result["passed"] = False
        return result
    app = compose_cli(str(Path(source).resolve()))
    build = app.build.execute(app.root_directory)
    if build.indexed != len(manifest["files"]) or build.excluded:
        result["complete"] = False
        result["problems"].append({"reason": "reader: file non indicizzati"})
        result["passed"] = False
        return result
    for case in queries["queries"]:
        response = app.search.execute(SearchRequest(case["query"], SearchField(case["field"]), limit=len(manifest["files"])))
        actual = sorted(item.relative_path.value for item in response.results)
        passed = actual == case["expected"] and response.total_matches == len(actual)
        result["cases"].append({"query": case["query"], "field": case["field"], "expected": case["expected"], "actual": actual, "passed": passed})
    result["passed"] = all(case["passed"] for case in result["cases"])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("synthetic", "fetch", "validate-real", "verify-real", "export-text"):
        command = sub.add_parser(name)
        command.add_argument("destination", type=Path)
        if name == "export-text":
            command.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    if args.command == "synthetic":
        manifest, queries = generate_synthetic(args.destination)
        report = validate(manifest, queries, args.destination / "source")
    else:
        manifest = load_manifest()
        if args.command == "fetch":
            diagnostics = fetch(manifest, args.destination)
            report = {"corpus_id": corpus_id(manifest), "diagnostics": diagnostics, "problems": verify_files(manifest, args.destination)}
            report["passed"] = not report["problems"]
        elif args.command == "export-text":
            export_text(manifest, args.destination, args.output)
            report = {"corpus_id": corpus_id(manifest), "output": str(args.output), "passed": True}
        elif args.command == "verify-real":
            report = {"corpus_id": corpus_id(manifest), "problems": verify_files(manifest, args.destination)}
            report["passed"] = not report["problems"]
        else:
            try:
                queries = load_queries(REAL_QUERIES, manifest)
            except FileNotFoundError:
                report = {"code_revision": revision(), "working_tree_dirty": working_tree_dirty(), "corpus_id": corpus_id(manifest), "query_sha256": None, "passed": False, "complete": False, "problems": [{"reason": "ground truth reale mancante"}]}
            else:
                report = validate(manifest, queries, args.destination)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
