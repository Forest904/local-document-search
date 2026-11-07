"""Corpus prestazionale V2-02: sintetico, deterministico e separato da V2-01."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random

from m9_corpus import pdf_bytes


SEED = 20261107
PROFILES = {
    "small": (100, 300_000),
    "adverse": (1000, 30_000_000),
    "target": (10_000, 300_000_000),
    "smoke": (12, 24_000),
}
VOCABULARY = tuple(f"termine{i:05d}" for i in range(20_000))
MARKERS = ("marcatoreuniversale", "marcatoremedio", "marcatoreraro")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _text(index, length, rng, adverse):
    markers = [MARKERS[0]]
    if index % 10 == 0:
        markers.append(MARKERS[1])
    if index % 100 == 0:
        markers.append(MARKERS[2])
    prefix = " ".join(markers) + " frasecomune consecutiva "
    # Zipf-like frequencies; repeating phrase stresses common posting intersections.
    words = [VOCABULARY[rng.randrange(len(VOCABULARY)) if rng.random() < .1
                        else min(int(rng.paretovariate(1.4) - 1), len(VOCABULARY) - 1)]
             for _ in range(256)]
    unit = " ".join(words) + (" frasecomune consecutiva " if adverse else " ")
    body = (unit * ((length // len(unit)) + 1))[:max(0, length - len(prefix) - 1)]
    return prefix + body.rsplit(" ", 1)[0] + "\n"


def generate(destination, profile="target", *, count=None, target_bytes=None):
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Destinazione non vuota")
    default_count, default_bytes = PROFILES[profile]
    count = default_count if count is None else count
    target_bytes = default_bytes if target_bytes is None else target_bytes
    if count < 3 or target_bytes < count * 100:
        raise ValueError("Dimensioni del corpus non valide")
    source = destination / "source"
    source.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    weights = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    total_weight = sum(weights[i % len(weights)] for i in range(count))
    entries = []
    for index in range(count):
        suffix = ("txt", "md", "pdf")[index % 3]
        relative = f"cartella{index % 20:02d}/documento{index:05d}.{suffix}"
        size = target_bytes * weights[index % len(weights)] // total_weight
        text = _text(index, size, rng, profile == "adverse")
        data = (pdf_bytes(text) if suffix == "pdf" else
                (text + "\n```\nbloccoescluso\n```\n").encode() if suffix == "md" else
                text.encode())
        path = source / relative
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
        entries.append({"path": relative, "sha256": digest(data), "source_bytes": len(data),
                        "expected_text_bytes": len(text.encode()), "index": index})
    manifest = {"schema": 1, "profile": profile, "seed": SEED, "count": count,
                "target_text_bytes": target_bytes, "source_bytes": sum(e["source_bytes"] for e in entries),
                "expected_text_bytes": sum(e["expected_text_bytes"] for e in entries),
                "files": entries}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def verify(destination):
    destination = Path(destination)
    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    files = manifest["files"]
    if len(files) != manifest["count"] or len({e["path"] for e in files}) != len(files):
        raise ValueError("Manifest incompleto")
    actual = {p.relative_to(destination / "source").as_posix() for p in (destination / "source").rglob("*") if p.is_file()}
    expected = {e["path"] for e in files}
    if actual != expected:
        raise ValueError("File mancanti o estranei")
    def valid(entry):
        return digest((destination / "source" / entry["path"]).read_bytes()) == entry["sha256"]
    with ThreadPoolExecutor(max_workers=16) as workers:
        for entry, correct in zip(files, workers.map(valid, files)):
            if not correct:
                raise ValueError(f"Hash diverso: {entry['path']}")
    if sum(e["expected_text_bytes"] for e in files) < manifest["target_text_bytes"] * .99:
        raise ValueError("Testo atteso sotto il target")
    return manifest


def expected_paths(manifest, query, field):
    entries = manifest["files"]
    def hit(entry):
        i = entry["index"]
        filename = query == "documento" or (query == "documento00000" and i == 0)
        content = (query in (MARKERS[0], '"frasecomune consecutiva"') or
                   query == MARKERS[1] and i % 10 == 0 or
                   query == MARKERS[2] and i % 100 == 0 or
                   query == "marcatoreuniversale marcatoremedio" and i % 10 == 0)
        return (field in ("filename", "both") and filename or
                field in ("content", "both") and content)
    return sorted(e["path"] for e in entries if hit(e))


QUERIES = [("documento", "filename"), ("documento00000", "filename"),
           ("assentezz", "filename"), (MARKERS[0], "content"),
           (MARKERS[1], "content"), (MARKERS[2], "content"),
           ("marcatoreuniversale marcatoremedio", "content"),
           ('"frasecomune consecutiva"', "content"), ("assentezz", "content"),
           ("documento", "both"), (MARKERS[1], "both"),
           ("marcatoreuniversale marcatoremedio", "both"),
           ("documento marcatoreuniversale", "both"), ("assentezz", "both")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("generate")
    create.add_argument("destination", type=Path)
    create.add_argument("--profile", choices=PROFILES, default="target")
    create.add_argument("--count", type=int)
    create.add_argument("--target-bytes", type=int)
    check = sub.add_parser("verify")
    check.add_argument("destination", type=Path)
    args = parser.parse_args()
    result = (generate(args.destination, args.profile, count=args.count, target_bytes=args.target_bytes)
              if args.command == "generate" else verify(args.destination))
    print(json.dumps({k: v for k, v in result.items() if k != "files"}, indent=2))


if __name__ == "__main__":
    main()
