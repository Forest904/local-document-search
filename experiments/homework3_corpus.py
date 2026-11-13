"""Preparazione locale dei corpus Homework 3; nessun dato personale versionato."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import random
import platform
import stat
import subprocess
import sys
import shutil

from local_document_search.application.ports import Extracted, Excluded, FileCandidate
from local_document_search.domain.documents import DocumentFormat, DocumentMetadata, FileFingerprint, RelativePath
from local_document_search.infrastructure.readers.markdown import MarkdownReader
from local_document_search.infrastructure.readers.pdf import PdfReader
from local_document_search.infrastructure.readers.text import TextReader

SEED = 20261113
PROFILES = {"small": (100, 3_000_000), "medium": (1000, 30_000_000), "large": (10000, 300_000_000)}
TECHNICAL = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist", ".vscode", ".idea", "target"}
FORMATS = {".txt": DocumentFormat.TXT, ".md": DocumentFormat.MARKDOWN, ".pdf": DocumentFormat.PDF}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scan(root):
    records = []
    pending = [root]
    while pending:
        folder = pending.pop()
        try:
            with os.scandir(folder) as iterator:
                entries = sorted(iterator, key=lambda e: e.name)
            for entry in entries:
                relative = Path(entry.path).relative_to(root).as_posix()
                try:
                    info = entry.stat(follow_symlinks=False)
                    if getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT or stat.S_ISLNK(info.st_mode):
                        records.append({"path": relative, "status": "reparse_excluded"})
                    elif stat.S_ISDIR(info.st_mode):
                        if entry.name.lower() in TECHNICAL or relative.split("/")[0] != "Esami":
                            records.append({"path": relative, "status": "directory_excluded"})
                        else:
                            pending.append(Path(entry.path))
                    elif stat.S_ISREG(info.st_mode):
                        ext = Path(entry.name).suffix.lower()
                        status = "selected" if ext in FORMATS and relative.startswith("Esami/") else "format_excluded"
                        records.append({"path": relative, "status": status, "bytes": info.st_size, "mtime_ns": info.st_mtime_ns, "format": ext})
                except OSError as exc:
                    records.append({"path": relative, "status": "stat_error", "error": str(exc)})
        except OSError as exc:
            records.append({"path": folder.relative_to(root).as_posix(), "status": "scan_error", "error": str(exc)})
    return sorted(records, key=lambda item: item["path"])


def inventory(root, output):
    records = scan(root)
    write_json(output, {"schema": 1, "records": records})
    return records


def groups(entries, key):
    by_hash = defaultdict(list)
    for entry in entries:
        if key in entry:
            by_hash[entry[key]].append(entry["path"])
    return [paths for paths in by_hash.values() if len(paths) > 1]


def preparation_complete(records, entries):
    """Esclusioni previste sono esiti; errori e omissioni non lo sono."""
    selected = [r["path"] for r in records if r["status"] == "selected"]
    paths = [e["path"] for e in entries]
    return (
        not any(r["status"] in {"scan_error", "stat_error"} for r in records)
        and len(paths) == len(set(paths)) == len(selected)
        and set(paths) == set(selected)
        and all(e.get("status") == "selection_excluded" or e.get("status") == "converted" or (
            e.get("status") == "pdf_no_text" and e.get("format") == ".pdf"
            and bool(e.get("reason"))
        ) for e in entries)
    )


def select_prepared(source, destination, decisions):
    """Deriva una versione immutabile dalla copia verificata, senza OneDrive."""
    verify(source)
    previous = json.loads((source / "metadata/manifest.json").read_text(encoding="utf-8"))
    inventory_data = json.loads((source / "metadata/inventory.json").read_text(encoding="utf-8"))
    decision_data = json.loads(decisions.read_text(encoding="utf-8"))
    if decision_data.get("schema") != 1 or decision_data.get("source_corpus_id") != previous["corpus_id"]:
        raise ValueError("Decisioni non riferite al corpus sorgente")
    by_path = {e["path"]: e for e in previous["entries"]}
    choices = decision_data["decisions"]
    if len(choices) != len({d["path"] for d in choices}):
        raise ValueError("Decisioni duplicate")
    for choice in choices:
        if choice["path"] not in by_path or choice["action"] not in {"include", "exclude"} or not choice.get("reason") or not choice.get("author"):
            raise ValueError("Decisione invalida")
    destination.mkdir(parents=True, exist_ok=False)
    mapped = {d["path"]: d for d in choices}
    entries = []
    for old in previous["entries"]:
        entry = dict(old)
        choice = mapped.get(entry["path"])
        if choice:
            entry["selection_decision"] = choice
        if choice and choice["action"] == "exclude":
            entry["status"] = "selection_excluded"
            for key in ("txt_path", "txt_bytes", "txt_sha256"):
                entry.pop(key, None)
        else:
            if "txt_path" in entry:
                target = destination / entry["txt_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / entry["txt_path"], target)
        original = destination / entry["original_path"]
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / entry["original_path"], original)
        entries.append(entry)
    converted = [e for e in entries if e["status"] == "converted"]
    identity = digest(json.dumps([(e["txt_path"], e["txt_sha256"]) for e in converted], separators=(",", ":")).encode())
    manifest = dict(previous, entries=entries, corpus_id=identity,
                    parent_corpus_id=previous["corpus_id"], complete=preparation_complete(inventory_data["records"], entries),
                    source_duplicates=groups(entries, "source_sha256"), txt_duplicates=groups(entries, "txt_sha256"))
    write_json(destination / "metadata/inventory.json", inventory_data)
    write_json(destination / "metadata/selection_decisions.json", decision_data)
    write_json(destination / "metadata/manifest.json", manifest)
    write_json(destination / "metadata/manual_review.json", {"schema": 1, "state": "pending", "sample": stratify(converted),
              "suspicious": [e["path"] for e in converted if e["txt_bytes"] < 100 or e["txt_bytes"] < e["source_bytes"] // 100], "findings": []})
    return verify(destination)


def prepare(root, destination):
    destination.mkdir(parents=True, exist_ok=False)
    metadata = destination / "metadata"
    records = inventory(root, metadata / "inventory.json")
    readers = {".txt": TextReader(), ".md": MarkdownReader(), ".pdf": PdfReader()}
    outcomes = []
    used = set()
    try:
        for item in records:
            if item["status"] != "selected":
                continue
            relative = Path(item["path"])
            source = root / relative
            entry = {"path": item["path"], "format": item["format"]}
            outcomes.append(entry)
            try:
                before = source.stat(follow_symlinks=False)
                if (getattr(before, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
                        or not stat.S_ISREG(before.st_mode) or (before.st_size, before.st_mtime_ns) != (item["bytes"], item["mtime_ns"])):
                    raise ValueError("sorgente cambiata o reparse point")
                raw = source.read_bytes()
                after = source.stat(follow_symlinks=False)
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or len(raw) != before.st_size:
                    raise ValueError("sorgente cambiata durante la copia")
                copy = destination / "originals" / relative
                copy.parent.mkdir(parents=True, exist_ok=True)
                copy.write_bytes(raw)
                entry.update(source_bytes=len(raw), source_sha256=digest(raw), original_path=copy.relative_to(destination).as_posix())
                candidate = FileCandidate(str(destination / "originals"), DocumentMetadata(
                    RelativePath(relative.as_posix()), relative.name, FORMATS[item["format"]],
                    FileFingerprint(len(raw), after.st_mtime_ns)))
                result = readers[item["format"]].read(candidate)
                if isinstance(result, Excluded):
                    entry.update(status="pdf_no_text", reason=(
                        "Nessun testo non-whitespace estratto con pypdf "
                        + importlib.metadata.version("pypdf")
                    ))
                    continue
                if not isinstance(result, Extracted):
                    entry.update(status="protected_pdf" if "password" in result.reason.lower() else "reader_error", reason=result.reason)
                    continue
                target = Path(item["format"][1:]) / relative.with_suffix(".txt")
                if target.as_posix().casefold() in used:
                    raise ValueError("collisione TXT")
                used.add(target.as_posix().casefold())
                output = raw if item["format"] == ".txt" else result.document.content.encode("utf-8")
                path = destination / "txt" / target
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(output)
                entry.update(status="converted", txt_path=path.relative_to(destination).as_posix(), txt_bytes=len(output), txt_sha256=digest(output))
            except (OSError, ValueError) as exc:
                entry.update(status="copy_error", reason=str(exc))
    finally:
        converted = [entry for entry in outcomes if entry.get("status") == "converted"]
        identity = digest(json.dumps([(e["txt_path"], e["txt_sha256"]) for e in converted], separators=(",", ":")).encode())
        revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout)
        manifest = {"schema": 1, "source_root": str(root), "complete": preparation_complete(records, outcomes),
                    "corpus_id": identity, "python": sys.version, "readers": {"markdown-it-py": importlib.metadata.version("markdown-it-py"), "pypdf": importlib.metadata.version("pypdf")},
                    "git_revision": revision, "git_dirty": dirty, "entries": outcomes,
                    "source_duplicates": groups(outcomes, "source_sha256"), "txt_duplicates": groups(outcomes, "txt_sha256")}
        write_json(metadata / "manifest.json", manifest)
        review = stratify(converted)
        write_json(metadata / "manual_review.json", {"schema": 1, "state": "pending", "sample": review, "suspicious": [e["path"] for e in converted if e["txt_bytes"] < 100 or e["txt_bytes"] < e["source_bytes"] // 100], "findings": []})
    return manifest


def stratify(entries):
    strata = defaultdict(list)
    for fmt in sorted({e["format"] for e in entries}):
        ordered = sorted((e for e in entries if e["format"] == fmt), key=lambda e: (e["txt_bytes"], e["path"]))
        for index, entry in enumerate(ordered):
            strata[(fmt, min(2, 3 * index // len(ordered)))].append(entry["path"])
    selected = []
    keys = sorted(strata)
    while len(selected) < min(20, len(entries)):
        changed = False
        for key in keys:
            if strata[key] and len(selected) < 20:
                selected.append(strata[key].pop((len(strata[key]) - 1) // 2))
                changed = True
        if not changed:
            break
    return selected


GENERATOR_VERSION = "hw3-original-2"
SIZE_TARGETS = (6000, 12000, 18000, 24000, 30000, 30000, 36000, 42000, 48000, 54000)
TOPICS = ("analisi", "reti", "basi di dati", "fisica", "storia", "linguistica")
STRUCTURES = ("appunti", "scheda di laboratorio", "esercitazione", "riepilogo")
# Lessico riservato: solo lettere minuscole, indipendente dagli analyzer del prodotto.
FAMILIES = {
    "filename_only": {"filename": "zefirnome", "content": "", "description": "Termine soltanto nel nome"},
    "content_only": {"filename": "", "content": "zefirtesto", "description": "Termine soltanto nel contenuto"},
    "same_filename": {"filename": "velnaro tespilo", "content": "", "description": "Coppia nello stesso nome"},
    "same_content": {"filename": "", "content": "velnaro tespilo", "description": "Coppia nello stesso contenuto"},
    "split_forward": {"filename": "velnaro", "content": "tespilo", "description": "Primo termine nel nome, secondo nel contenuto"},
    "split_reverse": {"filename": "tespilo", "content": "velnaro", "description": "Secondo termine nel nome, primo nel contenuto"},
    "consecutive": {"filename": "", "content": "frandilo spolvero", "description": "Frase consecutiva"},
    "interrupted": {"filename": "", "content": "frandilo passaggio spolvero", "description": "Frase interrotta da una parola"},
    "reversed": {"filename": "", "content": "spolvero frandilo", "description": "Ordine invertito"},
    "distant": {"filename": "", "content": "distalvo", "tail": "remotivo", "description": "Coppia in sezioni distanti"},
}
ABSENT_TERMS = ("assentivo", "introvello", "vacanzuro")
SUBJECT_TEXT = {
    "analisi": (("derivata", "integrale", "successione", "equicontinuità"),
                ("derivative", "integral", "sequence", "equicontinuity"),
                "Una stima locale della pendenza non garantisce il comportamento globale della funzione.",
                "A local slope estimate does not establish the global behaviour of the function."),
    "reti": (("pacchetto", "instradamento", "latenza", "incapsulamento"),
             ("packet", "routing", "latency", "encapsulation"),
             "Un collegamento può restare attivo mentre una coda ritarda la consegna dei pacchetti.",
             "A link can remain active while a queue delays packet delivery."),
    "basi di dati": (("relazione", "transazione", "chiave", "serializzabilità"),
                     ("relation", "transaction", "key", "serializability"),
                     "Due transazioni leggono la stessa relazione ma devono preservare il vincolo sulla chiave.",
                     "Two transactions read the same relation but must preserve the key constraint."),
    "fisica": (("energia", "velocità", "misura", "birifrangenza"),
               ("energy", "velocity", "measurement", "birefringence"),
               "Il confronto tra energia iniziale e finale richiede di dichiarare i confini del sistema.",
               "Comparing initial and final energy requires an explicit boundary for the system."),
    "storia": (("archivio", "fonte", "cronologia", "palinsesto"),
               ("archive", "source", "chronology", "palimpsest"),
               "La data di una copia non coincide necessariamente con la data del fatto narrato.",
               "The date of a copy need not coincide with the date of the event it describes."),
    "linguistica": (("fonema", "sintassi", "contesto", "allomorfia"),
                    ("phoneme", "syntax", "context", "allomorphy"),
                    "La stessa forma può assumere funzioni diverse quando cambia il contesto della frase.",
                    "The same form can serve different functions when the sentence context changes."),
}


def environment():
    return {"python": sys.version, "platform": platform.platform(),
            "git_revision": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
            "git_dirty": bool(subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout)}


def synthetic_document(index, seed=SEED):
    """Funzione pura: il profilo non partecipa a percorso, testo o caratteristiche."""
    rng = random.Random(f"{GENERATOR_VERSION}:{seed}:{index}")
    topic = TOPICS[index % 6]
    language = ("it", "en")[(index // 6) % 2]
    structure = STRUCTURES[(index // 12 + index % 4) % 4]
    family = list(FAMILIES)[index % len(FAMILIES)]
    case = FAMILIES[family]
    target = SIZE_TARGETS[index % 10]
    relative = f"{topic}/{language}/Unità {index // 100:03d}/{structure}-{topic} {language}-{index:05d} {case['filename']}.txt"
    words = SUBJECT_TEXT[topic][language == "en"]
    principle = SUBJECT_TEXT[topic][2 + (language == "en")]
    headings = (["Obiettivo", "Metodo", "Esempi", "Osservazioni", "Discussione", "Verifica"] if language == "it"
                else ["Objective", "Method", "Examples", "Observations", "Discussion", "Check"])
    rng.shuffle(headings)
    headings = headings[:rng.randint(3, 6)]
    title = {"it": ("Appunti ragionati", "Scheda di laboratorio", "Esercitazione guidata", "Riepilogo critico"),
             "en": ("Study notes", "Laboratory sheet", "Guided exercise", "Critical summary")}[language][STRUCTURES.index(structure)]
    parts = [f"{title} — {topic}, {index:05d}. Café, città, naïve.\n", case["content"] + ".\n" if case["content"] else ""]
    size = sum(len(p.encode("utf-8")) for p in parts)
    paragraph = 0
    while size < target:
        term = rng.choice(words[:3] if paragraph % 17 else words)
        number, other = rng.randint(2, 97), rng.randint(101, 499)
        if language == "it":
            variants = [
                f"Nel caso {number} il gruppo studia {term} usando {other} osservazioni. {principle} La conclusione distingue il dato dall'ipotesi.",
                f"L'esempio {number} confronta due descrizioni di {term}. Si annotano {other} risultati e si spiega perché una differenza può dipendere dal metodo.",
                f"Procedura {number}: descrivere {term}, esplicitare le assunzioni e discutere il caso limite {other}. {principle}",
                f"La domanda {number} richiede una spiegazione di {term}. Una risposta utile collega il risultato {other} alle condizioni iniziali e segnala gli aspetti ancora incerti.",
                f"Nel riepilogo {number} ritorna il tema {term}: {term} è ripetuto per collegare le sezioni. Il confronto {other} suggerisce un controllo indipendente."]
        else:
            variants = [
                f"In case {number} the group studies {term} using {other} observations. {principle} The conclusion separates evidence from assumptions.",
                f"Example {number} compares two accounts of {term}. The team records {other} results and explains why a difference may depend on the method.",
                f"Procedure {number}: describe {term}, state the assumptions and discuss boundary case {other}. {principle}",
                f"Question {number} asks for an explanation of {term}. A useful answer connects result {other} to the initial conditions and identifies remaining uncertainty.",
                f"Summary {number} returns to {term}: {term} is repeated to connect the sections. Comparison {other} suggests an independent check."]
        section = f"\n{headings[(paragraph // 4) % len(headings)]} {paragraph // 4 + 1}.\n" if paragraph % 4 == 0 else ""
        prefix = ("- " if paragraph % 3 == 0 else "") if structure in STRUCTURES[1:3] else ""
        part = section + prefix + rng.choice(variants) + "\n"
        parts.append(part)
        size += len(part.encode("utf-8"))
        paragraph += 1
    if "tail" in case:
        parts.append("\nAppendice.\n" + case["tail"] + ".\n")
    data = "".join(parts).encode("utf-8")
    entry = {"id": index, "path": relative, "bytes": len(data), "sha256": digest(data),
             "language": language, "topic": topic, "structure": structure, "family": family,
             "target_bytes": target, "sections": headings, "paragraphs": paragraph}
    return entry, data


def synthetic_identity(entries):
    return digest(json.dumps(sorted((e["path"], e["sha256"]) for e in entries), separators=(",", ":")).encode())


def synthetic_summary(entries):
    lengths = sorted(e["bytes"] for e in entries)
    return {"count": len(entries), "bytes": sum(lengths),
            "lengths": {"min": min(lengths), "median": (lengths[(len(lengths)-1)//2] + lengths[len(lengths)//2])/2, "max": max(lengths)},
            **{key: dict(sorted(Counter(str(e[key]) for e in entries).items()))
               for key in ("language", "topic", "structure", "family", "target_bytes")},
            "topic_language": dict(sorted(Counter(e["topic"] + "/" + e["language"] for e in entries).items()))}


def synthetic(destination, profile, seed=SEED):
    count, target = PROFILES[profile]
    destination.mkdir(parents=True, exist_ok=False)
    entries = []
    for index in range(count):
        entry, data = synthetic_document(index, seed)
        path = destination / "txt" / entry["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        entries.append(entry)
    manifest = {"schema": 2, "generator_version": GENERATOR_VERSION, "profile": profile,
                "seed": seed, "expected_count": count, "target_bytes": target, "tolerance": 0.05,
                "corpus_id": synthetic_identity(entries), "entries": entries,
                "families": FAMILIES, "absent_terms": list(ABSENT_TERMS),
                "summary": synthetic_summary(entries), "environment": environment()}
    write_json(destination / "manifest.json", manifest)
    return manifest


def verify_synthetic_metadata(manifest):
    if manifest.get("generator_version") != GENERATOR_VERSION:
        raise ValueError("Versione generatore non supportata")
    count, target = PROFILES[manifest["profile"]]
    entries = manifest["entries"]
    if (manifest.get("expected_count") != count or len(entries) != count
            or manifest.get("target_bytes") != target or manifest.get("tolerance") != 0.05):
        raise ValueError("Conteggi o obiettivi non coerenti")
    if not 0.95 * target <= sum(e["bytes"] for e in entries) <= 1.05 * target:
        raise ValueError("Volume fuori tolleranza")
    if (manifest.get("families") != FAMILIES or manifest.get("absent_terms") != list(ABSENT_TERMS)
            or manifest.get("summary") != synthetic_summary(entries)
            or sorted(e["id"] for e in entries) != list(range(count))
            or len({e["path"].casefold() for e in entries}) != count):
        raise ValueError("Metadati sintetici non coerenti")
    for entry in entries:
        expected, _ = synthetic_document(entry["id"], manifest["seed"])
        if entry != expected:
            raise ValueError("Caratteristiche o hash non coerenti con seed e ID")


def verify_nested(destinations):
    manifests = sorted((verify(p) for p in destinations), key=lambda m: len(m["entries"]))
    if (len(manifests) != 3 or {m.get("profile") for m in manifests} != set(PROFILES)
            or len({(m.get("generator_version"), m.get("seed")) for m in manifests}) != 1
            or any(m["schema"] != 2 for m in manifests)):
        raise ValueError("Servono i tre nuovi profili con stesso seed e versione")
    for small, large in zip(manifests, manifests[1:]):
        by_id = {e["id"]: (e["path"], e["sha256"]) for e in large["entries"]}
        if any(by_id.get(e["id"]) != (e["path"], e["sha256"]) for e in small["entries"]):
            raise ValueError("Profili non annidati")
    return {"verified": True, "nested": True, "environment": environment(),
            "profiles": [{"profile": m["profile"], "corpus_id": m["corpus_id"], "summary": m["summary"]} for m in manifests]}


def verify(destination):
    path = destination / "metadata" / "manifest.json"
    if not path.exists():
        path = destination / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = manifest["entries"]
    real = "profile" not in manifest
    if manifest.get("schema") not in ({1} if real else {1, 2}):
        raise ValueError("Schema manifest non supportato")
    if real:
        inventory_data = json.loads((destination / "metadata" / "inventory.json").read_text(encoding="utf-8"))
        if not manifest["complete"] or not preparation_complete(inventory_data["records"], entries):
            raise ValueError("preparazione incompleta")
        candidates = {r["path"]: r for r in inventory_data["records"] if r["status"] == "selected"}
    if not real and manifest["schema"] == 2:
        verify_synthetic_metadata(manifest)
    expected = set()
    expected_originals = set()
    for entry in entries:
        if real:
            RelativePath(entry["path"])
            candidate = candidates[entry["path"]]
            if entry["format"] != candidate["format"] or entry["source_bytes"] != candidate["bytes"]:
                raise ValueError("Metadati discordanti dall'inventario")
            original_path = entry["original_path"]
            if original_path != "originals/" + entry["path"]:
                raise ValueError("Mappa sorgente non coerente")
            original = destination / original_path
            expected_originals.add(original_path)
            if not original.is_file() or original.stat().st_size != entry["source_bytes"] or digest(original.read_bytes()) != entry["source_sha256"]:
                raise ValueError(f"Originale mancante o alterato: {entry['path']}")
            if entry["status"] in {"pdf_no_text", "selection_excluded"}:
                if any(key in entry for key in ("txt_path", "txt_sha256", "txt_bytes")):
                    raise ValueError("Un PDF escluso non deve avere un TXT")
                continue
        target = entry.get("txt_path", "txt/" + entry.get("path", ""))
        RelativePath(target)
        if not target.startswith("txt/") or target in expected:
            raise ValueError("Percorso TXT non valido o duplicato")
        expected.add(target)
        actual = destination / target
        if not actual.is_file() or digest(actual.read_bytes()) != entry.get("txt_sha256", entry.get("sha256")):
            raise ValueError(f"TXT mancante o alterato: {target}")
        if not real and manifest["schema"] == 2:
            actual.read_bytes().decode("utf-8", errors="strict")
        if actual.stat().st_size != entry.get("txt_bytes", entry.get("bytes")):
            raise ValueError("Dimensione TXT non coerente")
    actual = {p.relative_to(destination).as_posix() for p in (destination / "txt").rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError("TXT estranei o mancanti")
    if real:
        originals = {p.relative_to(destination).as_posix() for p in (destination / "originals").rglob("*") if p.is_file()}
        if originals != expected_originals:
            raise ValueError("Originali estranei o mancanti")
        if manifest["source_duplicates"] != groups(entries, "source_sha256") or manifest["txt_duplicates"] != groups(entries, "txt_sha256"):
            raise ValueError("Gruppi duplicati non coerenti")
        entries = [e for e in entries if e["status"] == "converted"]
    key = "txt_path" if "profile" not in manifest else "path"
    identity = digest(json.dumps([(e[key], e.get("txt_sha256", e.get("sha256"))) for e in entries], separators=(",", ":")).encode())
    if not real and manifest["schema"] == 2:
        identity = synthetic_identity(entries)
    if identity != manifest["corpus_id"]:
        raise ValueError("identità corpus alterata")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inventory", "prepare"):
        cmd = sub.add_parser(name)
        cmd.add_argument("source", type=Path)
        cmd.add_argument("destination", type=Path)
    cmd = sub.add_parser("synthetic")
    cmd.add_argument("destination", type=Path)
    cmd.add_argument("--profile", choices=PROFILES, required=True)
    cmd = sub.add_parser("verify")
    cmd.add_argument("destination", type=Path)
    cmd = sub.add_parser("verify-nested")
    cmd.add_argument("destinations", type=Path, nargs=3)
    cmd.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "inventory":
        result = inventory(args.source, args.destination)
    elif args.command == "prepare":
        result = prepare(args.source, args.destination)
    elif args.command == "synthetic":
        result = synthetic(args.destination, args.profile)
    elif args.command == "verify-nested":
        result = verify_nested(args.destinations)
        write_json(args.output, result)
    else:
        result = verify(args.destination)
    count = len(result.get("entries", [])) if isinstance(result, dict) else len(result)
    print(json.dumps({"command": args.command, "count": count, "complete": result.get("complete") if isinstance(result, dict) else None}, ensure_ascii=False))


if __name__ == "__main__":
    main()
