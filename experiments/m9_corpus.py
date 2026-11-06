"""Corpus M9 sintetico deterministico, senza dipendenze per la generazione PDF."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import textwrap


SEED = 20261106
WORDS = ("archivio documento ricerca locale indice posizione termine frase "
         "memoria versione cartella percorso progetto testo pagina esempio "
         "montagna pianura fiume mare albero foglia radice ramo cielo nuvola "
         "stella luna pianeta sole").split()


def pdf_bytes(text):
    """PDF ASCII con pagine vere, font standard e xref deterministico."""
    lines = textwrap.wrap(text, width=90)
    pages = [lines[i:i + 55] for i in range(0, len(lines), 55)] or [[]]
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    refs = []
    for page in pages:
        page_id = len(objects) + 1
        refs.append(f"{page_id} 0 R")
        objects.append((f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                        f"/Resources << /Font << /F1 3 0 R >> >> /Contents {page_id + 1} 0 R >>").encode())
        stream = b"BT /F1 10 Tf 36 750 Td 12 TL\n"
        for line in page:
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream += f"({escaped}) Tj T*\n".encode("ascii")
        stream += b"ET"
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(refs)}] /Count {len(refs)} >>".encode()
    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    start = len(result)
    result.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())
    result.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode())
    return bytes(result)


def generate(destination, count=3000, text_bytes=10000, seed=SEED):
    if count <= 0 or text_bytes < 100:
        raise ValueError("count positivo e text_bytes >= 100 richiesti")
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("La destinazione deve essere vuota per non mescolare corpus")
    source = destination / "source"
    source.mkdir(parents=True)
    rng = random.Random(seed)
    entries = []
    for index in range(count):
        suffix = ("txt", "md", "pdf")[index % 3]
        relative = f"cartella{index % 20:02d}/NomeSolo{index:05d}.{suffix}"
        prefix = "corpus comune alfa beta " if index % 2 == 0 else "corpus comune beta alfa "
        prefix += f"selettore{index:05d} "
        text = prefix
        while len(text) < text_bytes:
            text += " ".join(rng.choices(WORDS, k=100)) + " "
        text = text[:text_bytes].rsplit(" ", 1)[0] + "\n"
        if suffix == "pdf":
            data = pdf_bytes(text)
        elif suffix == "md":
            data = (text + "\n```\nesclusomarkdown\n```\n").encode("utf-8")
        else:
            data = text.encode("utf-8")
        path = source / relative
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
        entries.append({"path": relative, "bytes": len(data), "text_bytes": len(text),
                        "sha256": hashlib.sha256(data).hexdigest()})
    all_paths = sorted(entry["path"] for entry in entries)
    even_paths = sorted(entry["path"] for index, entry in enumerate(entries) if index % 2 == 0)
    queries = [
        {"query": "nome solo", "field": "filename", "expected": all_paths},
        {"query": "corpus comune", "field": "content", "expected": all_paths},
        {"query": '"alfa beta"', "field": "content", "expected": even_paths},
        {"query": 'corpus "alfa beta"', "field": "both", "expected": even_paths},
        {"query": "nome corpus", "field": "both", "expected": []},
        {"query": "esclusomarkdown", "field": "content", "expected": []},
        {"query": "selettore00000", "field": "content", "expected": [entries[0]["path"]]},
    ]
    manifest = {"seed": seed, "count": count, "target_text_bytes": text_bytes,
                "source_bytes": sum(e["bytes"] for e in entries),
                "canonical_input_bytes": sum(e["text_bytes"] for e in entries),
                "files": entries, "queries": queries}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def error_fixtures(destination):
    """Separati dal corpus prestazionale; la cifratura usa solo pypdf gia previsto."""
    from pypdf import PdfReader, PdfWriter
    from io import BytesIO
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "invalid.txt").write_bytes(b"\xff\xfe")
    (destination / "corrupt.pdf").write_bytes(b"%PDF-1.4\ninvalid")
    (destination / "no-text.pdf").write_bytes(pdf_bytes(""))
    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(pdf_bytes("segreto sintetico"))))
    writer.encrypt("password-sintetica", algorithm="RC4-128")
    writer.write(destination / "protected.pdf")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--count", type=int, default=3000)
    parser.add_argument("--text-bytes", type=int, default=10000)
    args = parser.parse_args()
    report = generate(args.destination, args.count, args.text_bytes)
    error_fixtures(args.destination / "errors")
    print(json.dumps({k: v for k, v in report.items() if k not in {"files", "queries"}}, indent=2))
