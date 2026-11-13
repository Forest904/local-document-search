"""Campionamento e revisione cieca locale per HW3-02."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import shutil

from homework3_evaluate import (check_corpus, corpus, digest, evaluate, identity, inventory,
                               read_json, relative, save_new, seal, unseal, validate_queries)
from homework3_scan import check_plain

SEED = 20261113
QUOTAS = {".pdf": 40, ".txt": 10, ".md": 10}


def select(entries, subjects):
    """Terzili per formato; round-robin degli strati ordinati materia/terzile."""
    selected = []
    for fmt, quota in QUOTAS.items():
        ordered = sorted((e for e in entries if e["format"] == fmt),
                         key=lambda e: (e["txt_bytes"], e["path"]))
        if len(ordered) < quota:
            raise ValueError("Documenti insufficienti per le quote")
        strata = defaultdict(list)
        for rank, entry in enumerate(ordered):
            subject = subjects[entry["path"]]
            if not subject.get("subject") or not subject.get("basis"):
                raise ValueError("Classificazione materia incompleta")
            row = dict(entry, subject=subject["subject"], length_tertile=min(2, rank * 3 // len(ordered)))
            strata[(row["subject"], row["length_tertile"])].append(row)
        for values in strata.values():
            values.sort(key=lambda e: (digest(f"{SEED}:{e['path']}".encode()), e["path"]))
        picked = []
        while len(picked) < quota:
            for key in sorted(strata):
                if strata[key] and len(picked) < quota:
                    picked.append(strata[key].pop(0))
        selected.extend(picked)
    return sorted(selected, key=lambda e: e["txt_path"])


def prepare_sample(root, subjects_path, destination):
    root, destination = Path(root), Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    source = corpus(root)
    manifest = read_json(root / "metadata/manifest.json")
    entries = [e for e in manifest["entries"] if e["status"] == "converted"]
    subjects = read_json(subjects_path)
    if set(subjects) != {e["path"] for e in entries}:
        raise ValueError("La mappa materie deve coprire tutti gli inclusi")
    selected = select(entries, subjects)
    duplicates = Counter(e["txt_sha256"] for e in entries)
    destination.mkdir(parents=True)
    for index, entry in enumerate(selected, 1):
        entry["document_id"] = f"D{index:03d}"
        entry["duplicate_count_in_corpus"] = duplicates[entry["txt_sha256"]]
        original = root / relative(entry["original_path"])
        check_plain(original)
        if digest(original.read_bytes()) != entry["source_sha256"]:
            raise ValueError("Originale alterato")
        target = destination / relative(entry["txt_path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / entry["txt_path"], target)
    files = inventory(destination / "txt")
    wanted = sorted([{"path": e["txt_path"][4:], "sha256": e["txt_sha256"],
                      "bytes": e["txt_bytes"]} for e in selected], key=lambda e: e["path"])
    if files != wanted:
        raise ValueError("Copia del campione non coerente")
    check_corpus(source)
    return seal(destination / "sample.json", {"kind": "relevance_sample", "corpus": source,
        "sample_id": identity(files), "seed": SEED, "quotas": QUOTAS,
        "subjects": subjects, "entries": selected, "files": files})


def check_sample(sample_path):
    sample = unseal(sample_path, "relevance_sample")
    check_corpus(sample["corpus"])
    if inventory(Path(sample_path).parent / "txt") != sample["files"]:
        raise ValueError("Campione alterato")
    for entry in sample["entries"]:
        path = Path(sample["corpus"]["root"]) / relative(entry["original_path"])
        check_plain(path)
        if digest(path.read_bytes()) != entry["source_sha256"]:
            raise ValueError("Originale del campione alterato")
    return sample


def approval(record, target):
    if (record.get("decision") != "approved" or record.get("role") != "user"
            or record.get("target_sha256") != target
            or not all(record.get(key) for key in ("author", "date", "evidence"))):
        raise ValueError("Manca approvazione esplicita dell'utente riferita a questa versione")


def freeze_needs(sample_path, draft_path, approval_path, output):
    if Path(output).exists():
        raise FileExistsError(output)
    sample = check_sample(sample_path)
    draft = read_json(draft_path)
    if draft["sample_sha256"] != sample["artifact_sha256"]:
        raise ValueError("Bisogni riferiti a un altro campione")
    needs = draft["needs"]
    if len(needs) != 10:
        raise ValueError("Servono dieci bisogni")
    validate_queries(needs, lexical=False)
    for row in needs:
        if not all(row.get(k) for k in ("need", "criterion", "include", "exclude")):
            raise ValueError("Criterio binario incompleto")
    record = read_json(approval_path)
    approval(record, digest(Path(draft_path).read_bytes()))
    return seal(output, {"kind": "needs_frozen", "sample_sha256": sample["artifact_sha256"],
                         "needs": needs, "approval": record})


def prepare_batches(sample_path, needs_path, destination):
    sample = check_sample(sample_path)
    needs = unseal(needs_path, "needs_frozen")
    approval(needs.get("approval", {}), needs.get("approval", {}).get("target_sha256"))
    if needs["sample_sha256"] != sample["artifact_sha256"]:
        raise ValueError("Campione diverso")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for index, need in enumerate(needs["needs"], 1):
        save_new(destination / f"batch-{index:02d}.json", {
            "need_id": need["id"], "needs_sha256": needs["artifact_sha256"],
            "judgments": [{"document_id": e["document_id"], "relevant": None,
                "state": "pending", "reason": "", "reference": "",
                "original_review": "", "reviewer": ""} for e in sample["entries"]]})


def validate_judgments(sample, needs, rows):
    if needs["sample_sha256"] != sample["artifact_sha256"]:
        raise ValueError("Campione diverso")
    documents = {e["document_id"] for e in sample["entries"]}
    if len(rows) != 10 or {r["need_id"] for r in rows} != {n["id"] for n in needs["needs"]}:
        raise ValueError("Lotti mancanti o duplicati")
    for batch in rows:
        if batch["needs_sha256"] != needs["artifact_sha256"]:
            raise ValueError("Bisogni diversi")
        judgments = batch["judgments"]
        if len(judgments) != 60 or {j["document_id"] for j in judgments} != documents:
            raise ValueError("Giudizi mancanti o duplicati")
        for row in judgments:
            if (type(row["relevant"]) is not bool or row["state"] != "reviewed"
                    or not all(row.get(k) for k in ("reason", "reference", "original_review", "reviewer"))):
                raise ValueError("Giudizio incompleto o ambiguo")


def freeze_judgments(sample_path, needs_path, batches, approval_path, output):
    if Path(output).exists():
        raise FileExistsError(output)
    sample = check_sample(sample_path)
    needs = unseal(needs_path, "needs_frozen")
    approval(needs.get("approval", {}), needs.get("approval", {}).get("target_sha256"))
    files = sorted(Path(batches).glob("batch-*.json"))
    rows = [read_json(p) for p in files]
    validate_judgments(sample, needs, rows)
    record = read_json(approval_path)
    approval(record, identity(rows))
    return seal(output, {"kind": "judgments_frozen", "sample_sha256": sample["artifact_sha256"],
                         "needs_sha256": needs["artifact_sha256"], "batches": rows,
                         "approval": record})


def evaluate_relevance(sample_path, needs_path, judgments_path, output):
    if Path(output).exists():
        raise FileExistsError(output)
    sample = check_sample(sample_path)
    needs = unseal(needs_path, "needs_frozen")
    judgments = unseal(judgments_path, "judgments_frozen")
    approval(needs.get("approval", {}), needs.get("approval", {}).get("target_sha256"))
    approval(judgments.get("approval", {}), identity(judgments["batches"]))
    validate_queries(needs["needs"], lexical=False)
    validate_judgments(sample, needs, judgments["batches"])
    if (needs["sample_sha256"] != sample["artifact_sha256"]
            or judgments["sample_sha256"] != sample["artifact_sha256"]
            or judgments["needs_sha256"] != needs["artifact_sha256"]):
        raise ValueError("Artefatti di versioni diverse")
    documents = {e["document_id"]: e["txt_path"][4:] for e in sample["entries"]}
    expected = {b["need_id"]: sorted(documents[j["document_id"]] for j in b["judgments"]
                                    if j["relevant"]) for b in judgments["batches"]}
    result = evaluate(Path(sample_path).parent / "txt", needs["needs"], expected, 60)
    check_sample(sample_path)
    return seal(output, {"kind": "relevance_report", "sample_id": sample["sample_id"],
        "needs_sha256": needs["artifact_sha256"], "judgments_sha256": judgments["artifact_sha256"],
        "recall_scope": "60 selected documents only", **result})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    commands = {
        "prepare-sample": (prepare_sample, ["root", "subjects_path", "destination"]),
        "freeze-needs": (freeze_needs, ["sample_path", "draft_path", "approval_path", "output"]),
        "prepare-batches": (prepare_batches, ["sample_path", "needs_path", "destination"]),
        "freeze-judgments": (freeze_judgments, ["sample_path", "needs_path", "batches", "approval_path", "output"]),
        "evaluate": (evaluate_relevance, ["sample_path", "needs_path", "judgments_path", "output"]),
    }
    for name, (_, arguments) in commands.items():
        cmd = sub.add_parser(name)
        for argument in arguments:
            cmd.add_argument(argument, type=Path)
    args = parser.parse_args()
    function, arguments = commands[args.command]
    function(**{key: getattr(args, key) for key in arguments})
    print(args.command + ": completed")


if __name__ == "__main__":
    main()
