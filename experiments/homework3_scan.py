"""Oracolo lessicale a scansione, derivato dalla specifica e solo standard library."""
from pathlib import Path
import os
import stat
import unicodedata as ud


def tokens(text, filename=False):
    text = ud.normalize("NFC", text)
    if filename:
        separated = []
        for i, char in enumerate(text):
            left = i - 1
            while left >= 0 and ud.category(text[left])[0] == "M":
                left -= 1
            right = i + 1
            while right < len(text) and ud.category(text[right])[0] == "M":
                right += 1
            previous = text[left] if left >= 0 else ""
            following = text[right] if right < len(text) else ""
            boundary = previous and (
                (previous.islower() and char.isupper())
                or (previous.isupper() and char.isupper() and following.islower())
                or (previous.isalpha() and char.isnumeric())
                or (previous.isnumeric() and char.isalpha()))
            if boundary:
                separated.append(" ")
            separated.append(char)
        text = "".join(separated)
    text = ud.normalize("NFC", text.casefold())
    result, current = [], []
    for char in text:
        category = ud.category(char)[0]
        if category in "LN" or (category == "M" and current):
            current.append(char)
        elif current:
            result.append("".join(current))
            current = []
    if current:
        result.append("".join(current))
    return result


def clauses(query):
    if not query.strip() or query.count('"') % 2:
        raise ValueError("Query vuota o virgolette sbilanciate")
    result = []
    for index, part in enumerate(query.split('"')):
        if index % 2:
            result.append((True, part))
        else:
            if part.strip():
                result.append((False, part))
    return result


def compile_query(query, field):
    if field not in ("filename", "content", "both"):
        raise ValueError("Campo non valido")
    parsed = clauses(query)
    compiled = {}
    for filename in ([True, False] if field == "both" else [field == "filename"]):
        checks = []
        for phrase, raw in parsed:
            terms = tokens(raw, filename)
            if not terms:
                raise ValueError("Clausola senza token")
            checks.append((phrase, terms))
        compiled[filename] = checks
    return compiled


def evaluate(streams, compiled):
    for filename, checks in compiled.items():
        stream = streams[filename]
        vocabulary = set(stream)
        if all(any(stream[i:i + len(terms)] == terms
                   for i in range(len(stream) - len(terms) + 1))
               if phrase else all(term in vocabulary for term in terms)
               for phrase, terms in checks):
            return True
    return False


def matches(name, text, query, field):
    compiled = compile_query(query, field)
    streams = {filename: tokens(source_name(name) if filename else text, filename)
               for filename in compiled}
    return evaluate(streams, compiled)


def source_name(name):
    return name[:-4] if name.lower().endswith((".txt", ".pdf")) else (
        name[:-3] if name.lower().endswith(".md") else name)


def check_plain(path):
    path = Path(path).absolute()
    for node in (path, *path.parents):
        info = node.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Link/reparse point nel corpus")


def text_files(root):
    root = Path(root).absolute()
    check_plain(root)
    if not root.is_dir():
        raise ValueError("Radice corpus non valida")
    result = []
    def fail(error):
        raise error
    for directory, folders, files in os.walk(root, followlinks=False, onerror=fail):
        for name in folders + files:
            check_plain(Path(directory) / name)
        for name in files:
            path = Path(directory) / name
            if path.suffix.lower() != ".txt":
                raise ValueError("File non TXT nel corpus valutato")
            result.append(path)
    return sorted(result, key=lambda p: p.relative_to(root).as_posix())


def scan(root, queries):
    """Una lettura per documento; nessun indice o analyzer del prodotto."""
    results = {row["id"]: [] for row in queries}
    if len(results) != len(queries):
        raise ValueError("ID query duplicati")
    root = Path(root).absolute()
    compiled = {row["id"]: compile_query(row["query"], row["field"]) for row in queries}
    for path in text_files(root):
        streams = {True: tokens(source_name(path.name), True),
                   False: tokens(path.read_text(encoding="utf-8-sig"))}
        for row in queries:
            if evaluate(streams, compiled[row["id"]]):
                results[row["id"]].append(path.relative_to(root).as_posix())
    return results
