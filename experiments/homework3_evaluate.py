"""Artefatti locali congelati e valutazione HW3-02; eseguire dalla radice repo."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys

from homework3_metrics import aggregate, score
from homework3_scan import check_plain, compile_query, scan, text_files


def digest(value):
    return hashlib.sha256(value).hexdigest()


def identity(value):
    return digest(json.dumps(value, ensure_ascii=True, sort_keys=True,
                             separators=(",", ":")).encode())


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def environment():
    repo = Path(__file__).resolve().parents[1]
    def git(*args):
        return subprocess.run(["git", *args], cwd=repo, check=True,
                              capture_output=True, text=True, encoding="utf-8").stdout.strip()
    return {"utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
            "platform": platform.platform(), "revision": git("rev-parse", "HEAD"),
            "working_tree": git("status", "--porcelain"),
            "tools": {p.name: digest(p.read_bytes()) for p in sorted(
                Path(__file__).parent.glob("homework3_*.py"))}}


def save_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def seal(path, payload):
    data = dict(payload, schema=1, environment=environment())
    data["artifact_sha256"] = identity(data)
    save_new(path, data)
    return data


def unseal(path, kind=None):
    data = read_json(path)
    claimed = data.pop("artifact_sha256", None)
    if claimed != identity(data) or data.get("schema") != 1:
        raise ValueError("Artefatto alterato o non congelato")
    data["artifact_sha256"] = claimed
    if kind and data.get("kind") != kind:
        raise ValueError("Tipo artefatto inatteso")
    return data


def relative(value):
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or ".." in path.parts or "\\" in value
            or ":" in value or path.as_posix() != value):
        raise ValueError("Percorso relativo non valido")
    return value


def inventory(root):
    root = Path(root).absolute()
    return [{"path": p.relative_to(root).as_posix(), "sha256": digest(p.read_bytes()),
             "bytes": p.stat().st_size} for p in text_files(root)]


def corpus(root):
    root = Path(root).absolute()
    check_plain(root)
    manifest_path = root / "metadata/manifest.json"
    if not manifest_path.exists():
        manifest_path = root / "manifest.json"
    check_plain(manifest_path)
    manifest = read_json(manifest_path)
    real = "profile" not in manifest
    entries = [e for e in manifest["entries"] if not real or e["status"] == "converted"]
    expected = []
    for entry in entries:
        path = entry["txt_path"][4:] if real else entry["path"]
        if real and not entry["txt_path"].startswith("txt/"):
            raise ValueError("TXT fuori dalla radice")
        expected.append({"path": relative(path),
                         "sha256": entry["txt_sha256"] if real else entry["sha256"],
                         "bytes": entry["txt_bytes"] if real else entry["bytes"]})
    actual = inventory(root / "txt")
    if actual != sorted(expected, key=lambda x: x["path"]):
        raise ValueError("Corpus alterato, file mancanti o estranei")
    # Conserva l'identità HW3-01, verificando la sua serializzazione storica.
    pairs = [(e["txt_path"], e["txt_sha256"]) for e in entries] if real else [
        (e["path"], e["sha256"]) for e in sorted(entries, key=lambda e: e["path"])]
    if digest(json.dumps(pairs, separators=(",", ":")).encode()) != manifest["corpus_id"]:
        raise ValueError("Identità manifest non coerente")
    return {"root": str(root), "corpus_id": manifest["corpus_id"],
            "manifest_sha256": digest(manifest_path.read_bytes()), "files": actual}


def check_corpus(frozen):
    current = corpus(frozen["root"])
    if current != frozen:
        raise ValueError("Corpus diverso dalla versione congelata")


def validate_queries(rows, lexical=True):
    if len({r["id"] for r in rows}) != len(rows) or not rows:
        raise ValueError("Query mancanti o ID duplicati")
    if lexical and Counter(r["field"] for r in rows) != {
            "filename": 10, "content": 15, "both": 5}:
        raise ValueError("Sono richieste 30 query: 10 nome, 15 contenuto, 5 entrambi")
    for row in rows:
        compile_query(row["query"], row["field"])


def freeze_lexical(root, draft_path, output):
    if Path(output).exists():
        raise FileExistsError(output)
    source = corpus(root)
    draft = read_json(draft_path)
    queries = draft["queries"]
    validate_queries(queries)
    checks = draft.get("manual_checks", [])
    if not checks or not draft.get("author"):
        raise ValueError("Mancano controlli manuali e autore")
    expected = scan(Path(root) / "txt", queries)
    known = {e["path"] for e in source["files"]}
    for check in checks:
        if (check["document"] not in known or check["query_id"] not in expected
                or type(check["expected"]) is not bool or not check.get("reason")):
            raise ValueError("Controllo manuale incompleto")
        if (check["document"] in expected[check["query_id"]]) != check["expected"]:
            raise ValueError("Scansione discordante dal controllo manuale")
    check_corpus(source)
    return seal(output, {"kind": "lexical_frozen", "corpus": source,
                         "draft": draft, "draft_sha256": digest(Path(draft_path).read_bytes()),
                         "expected": expected})


def retrieve(app, query, snapshot):
    from local_document_search.application.contracts import SearchRequest
    from local_document_search.domain.queries import SearchField
    fields = {"filename": SearchField.FILENAME, "content": SearchField.CONTENT,
              "both": SearchField.BOTH}
    paths, total = [], None
    while True:
        response = app.search.execute(SearchRequest(query["query"], fields[query["field"]],
            limit=50, offset=len(paths), allow_wildcards=False, snapshot_id=snapshot))
        if response.snapshot_id != snapshot or (total is not None and total != response.total_matches):
            raise ValueError("Snapshot o totale cambiato durante la paginazione")
        total = response.total_matches
        page = [r.relative_path.value for r in response.results]
        paths.extend(page)
        if len(paths) >= total:
            break
        if not page:
            raise ValueError("Paginazione incompleta")
    if len(paths) != total or len(set(paths)) != total or paths != sorted(paths):
        raise ValueError("Risultati duplicati, fuori ordine o totale incoerente")
    return paths


def evaluate(root, queries, expected, count):
    from local_document_search.interfaces.composition import compose_cli
    app = compose_cli(str(Path(root).absolute()))
    build = app.build.execute(app.root_directory)
    if build.indexed != count or build.discovered != count or build.excluded:
        raise ValueError("Build non corrispondente al corpus")
    rows = []
    for query in queries:
        actual = retrieve(app, query, build.snapshot_id)
        wanted = expected[query["id"]]
        rows.append({"id": query["id"], "field": query["field"],
                     "expected": wanted, "actual": actual,
                     "false_positives": sorted(set(actual) - set(wanted)),
                     "false_negatives": sorted(set(wanted) - set(actual)),
                     "metrics": score(wanted, actual)})
    return {"rows": rows, "summary": aggregate(r["metrics"] for r in rows),
            "by_field": {field: aggregate(r["metrics"] for r in rows if r["field"] == field)
                         for field in sorted({r["field"] for r in rows})},
            "indexed": build.indexed, "snapshot_id": build.snapshot_id}


def evaluate_lexical(frozen_path, output):
    if Path(output).exists():
        raise FileExistsError(output)
    frozen = unseal(frozen_path, "lexical_frozen")
    check_corpus(frozen["corpus"])
    queries = frozen["draft"]["queries"]
    validate_queries(queries)
    if set(frozen["expected"]) != {q["id"] for q in queries}:
        raise ValueError("Attesi mancanti")
    result = evaluate(Path(frozen["corpus"]["root"]) / "txt", queries,
                      frozen["expected"], len(frozen["corpus"]["files"]))
    check_corpus(frozen["corpus"])
    return seal(output, {"kind": "lexical_report", "frozen_sha256": frozen["artifact_sha256"],
                         "corpus_id": frozen["corpus"]["corpus_id"], **result,
                         "passed": all(r["metrics"]["exact"] for r in result["rows"])})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("freeze-lexical")
    cmd.add_argument("corpus", type=Path)
    cmd.add_argument("draft", type=Path)
    cmd.add_argument("output", type=Path)
    cmd = sub.add_parser("evaluate-lexical")
    cmd.add_argument("frozen", type=Path)
    cmd.add_argument("output", type=Path)
    args = parser.parse_args()
    result = (freeze_lexical(args.corpus, args.draft, args.output) if args.command == "freeze-lexical"
              else evaluate_lexical(args.frozen, args.output))
    print(json.dumps({k: result[k] for k in ("kind", "artifact_sha256", "passed", "summary")
                      if k in result}))
    return 1 if result.get("passed") is False else 0


if __name__ == "__main__":
    raise SystemExit(main())
