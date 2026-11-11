"""Proiezione della prima corrispondenza dal testo estratto al sorgente Markdown.

L'output canonico è sempre prodotto dal reader esistente. Questo adapter usa i
confini dei token CommonMark per individuare il sorgente dei caratteri visibili;
se non può provare la posizione, restituisce None.
"""
from __future__ import annotations

from array import array
import html
import re

from markdown_it import MarkdownIt

from local_document_search.infrastructure.readers.markdown import _text, _without_front_matter


_ENTITY = re.compile(r"&(?:#[xX][0-9a-fA-F]{1,6}|#[0-9]{1,7}|[A-Za-z][A-Za-z0-9]{1,31});")


def _normalized_source(source: str):
    """CommonMark normalizes CR and NUL; retain offsets of original source."""
    normalized = []
    starts = array("I")
    ends = array("I")
    position = 0
    while position < len(source):
        char = source[position]
        width = 2 if char == "\r" and source[position:position + 2] == "\r\n" else 1
        normalized.append("\n" if char == "\r" else "\ufffd" if char == "\x00" else char)
        starts.append(position)
        ends.append(position + width)
        position += width
    return "".join(normalized), starts, ends


def _source_lines(source: str):
    pieces = source.split("\n")
    lines = [piece + "\n" for piece in pieces[:-1]] + [pieces[-1]]
    offsets = []
    position = 0
    for line in lines:
        offsets.append(position)
        position += len(line)
    return lines, offsets


def _inline_offsets(raw: str, window: str, window_start: int, cursor: int):
    """Locate parser-supplied raw inline lines in their block, in order."""
    if not raw:
        return []
    positions = []
    pieces = raw.split("\n")
    for piece in [value + "\n" for value in pieces[:-1]] + [pieces[-1]]:
        value = piece.rstrip("\n")
        at = window.find(value, cursor) if value else cursor
        escaped_pipe = False
        if at < 0 and "|" in value:
            # markdown-it-py's table rule removes the escape before a pipe.
            literal = value.replace("|", "\\|")
            at = window.find(literal, cursor)
            escaped_pipe = at >= 0
        if at < 0:
            return None
        if escaped_pipe:
            source_cursor = at
            for char in value:
                if char == "|":
                    source_cursor += 1
                positions.append(window_start + source_cursor)
                source_cursor += 1
        else:
            positions.extend(window_start + at + i for i in range(len(value)))
            source_cursor = at + len(value)
        if piece.endswith("\n"):
            line_end = window.find("\n", source_cursor)
            if line_end < 0:
                return None
            positions.append(window_start + line_end)
            cursor = line_end + 1
        else:
            cursor = source_cursor
    return (positions, cursor) if len(positions) == len(raw) else None


def _leaf_positions(content: str, raw: str, raw_offsets: list[int], *, code=False):
    """Walk rendered characters through raw inline syntax in source order.

    Punctuation not emitted by the parser is skipped. An entity or escape maps
    to its complete lexical source, so its location is never inside the URL or
    a fenced block merely because the same text occurs there.
    """
    result = []
    cursor = 0
    pending = []
    for char in content:
        if pending:
            expected, span = pending.pop(0)
            if expected != char:
                return None
            result.append(span)
            continue
        found = None
        while cursor < len(raw):
            match = _ENTITY.match(raw, cursor) if not code and raw[cursor] == "&" else None
            if match:
                rendered = html.unescape(match.group())
                if char == rendered[:1]:
                    found = (cursor, match.end())
                    pending = [(extra, (raw_offsets[cursor], raw_offsets[match.end() - 1] + 1))
                               for extra in rendered[1:]]
                    cursor = match.end()
                    break
            if not code and raw[cursor] == "\\" and cursor + 1 < len(raw) and raw[cursor + 1] == char:
                found = (cursor, cursor + 2)
                cursor += 2
                break
            if raw[cursor] == char or code and char == " " and raw[cursor] == "\n":
                found = (cursor, cursor + 1)
                cursor += 1
                break
            cursor += 1
        if found is None:
            return None
        first, last = found
        result.append((raw_offsets[first], raw_offsets[last - 1] + 1))
    return result


def _closing_delimiter(raw, start, opening, closing):
    depth = 0
    escaped = False
    for position in range(start, len(raw)):
        if escaped:
            escaped = False
            continue
        if raw[position] == "\\":
            escaped = True
            continue
        if raw[position] == opening:
            depth += 1
        elif raw[position] == closing:
            depth -= 1
            if depth == 0:
                return position + 1
    return None


def _after_link(raw, cursor, *, image=False, autolink=False):
    if autolink:
        angle = raw.find("<", cursor)
        end = raw.find(">", angle + 1) if angle >= 0 else -1
        return end + 1 if end >= 0 else None
    start = raw.find("![" if image else "[", cursor)
    if start < 0:
        return None
    bracket = _closing_delimiter(raw, start + int(image), "[", "]")
    if bracket is None:
        return None
    if bracket < len(raw) and raw[bracket] in "([":
        opening = raw[bracket]
        return _closing_delimiter(raw, bracket, opening, ")" if opening == "(" else "]")
    return bracket


def project_first_match(source: str, start: int, end: int):
    """Return original-source spans for the first canonical match, or None."""
    normalized, origins, origin_ends = _normalized_source(source)
    body = _without_front_matter(normalized)
    removed = len(normalized) - len(body)
    parser = MarkdownIt("commonmark").enable("table")
    tokens = parser.parse(body)
    canonical = _text(tokens)
    if start < 0 or end > len(canonical) or start >= end:
        return None
    lines, line_offsets = _source_lines(body)
    selections = []
    canonical_cursor = 0
    block_cursors = {}
    for token in tokens:
        if canonical_cursor >= end and selections:
            break
        if token.type == "inline":
            if token.map is None or token.map[0] >= len(lines):
                return None
            block_start = line_offsets[token.map[0]]
            block_end = (line_offsets[token.map[1]] if token.map[1] < len(lines) else len(body))
            window = body[block_start:block_end]
            key = (block_start, block_end)
            located = _inline_offsets(token.content, window, block_start, block_cursors.get(key, 0))
            if located is None:
                return None
            raw_positions, block_cursors[key] = located
            raw_positions = [position + removed for position in raw_positions]
            raw_cursor = 0
            link_ends = []
            for child in token.children or []:
                if child.type == "link_open":
                    link_ends.append(_after_link(token.content, raw_cursor,
                                                 autolink=child.markup == "autolink"))
                elif child.type == "link_close":
                    if not link_ends or link_ends[-1] is None:
                        return None
                    raw_cursor = max(raw_cursor, link_ends.pop())
                elif child.type in ("text", "code_inline"):
                    value = child.content
                    positions = _leaf_positions(value, token.content[raw_cursor:], raw_positions[raw_cursor:],
                                                code=child.type == "code_inline")
                    if positions is None:
                        return None
                    if canonical_cursor < end and canonical_cursor + len(value) > start:
                        for index in range(max(start - canonical_cursor, 0), min(end - canonical_cursor, len(value))):
                            left, right = positions[index]
                            selections.append((origins[left], origin_ends[right - 1]))
                    if positions:
                        if positions[-1][1] - 1 not in raw_positions[raw_cursor:]:
                            return None
                        raw_cursor = raw_positions.index(positions[-1][1] - 1, raw_cursor) + 1
                    canonical_cursor += len(value)
                elif child.type == "image":
                    # The recursive image text is included by _text(). The
                    # simple label form can be projected through the raw label.
                    value = _text(child.children or [])
                    image_end = _after_link(token.content, raw_cursor, image=True)
                    if image_end is None:
                        return None
                    positions = _leaf_positions(value, token.content[raw_cursor:], raw_positions[raw_cursor:])
                    if positions is None:
                        return None
                    if canonical_cursor < end and canonical_cursor + len(value) > start:
                        for index in range(max(start - canonical_cursor, 0), min(end - canonical_cursor, len(value))):
                            left, right = positions[index]
                            selections.append((origins[left], origin_ends[right - 1]))
                    if positions:
                        if positions[-1][1] - 1 not in raw_positions[raw_cursor:]:
                            return None
                        raw_cursor = raw_positions.index(positions[-1][1] - 1, raw_cursor) + 1
                    raw_cursor = max(raw_cursor, image_end)
                    canonical_cursor += len(value)
                elif child.type in ("softbreak", "hardbreak", "html_inline"):
                    canonical_cursor += 1
        elif token.block:
            canonical_cursor += 1
    if not selections:
        return None
    merged = []
    for first, last in selections:
        if merged and first <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(last, merged[-1][1]))
        else:
            merged.append((first, last))
    return tuple(merged)
