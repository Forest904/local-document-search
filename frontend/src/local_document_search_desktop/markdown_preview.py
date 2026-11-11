"""Offline Markdown preview; source remains the only editable representation."""
from html import escape
from markdown_it import MarkdownIt
from PySide6.QtGui import QTextDocument


def render_preview(source, ranges=()):
    parser = MarkdownIt("commonmark").enable("table")
    parser.options["html"] = False

    def image_as_alt(renderer, tokens, index, options, env):
        return escape(tokens[index].content)

    parser.add_render_rule("image", image_as_alt)
    start_marker, end_marker = "\ue000", "\ue001"
    marked = source
    if ranges:
        first, last = ranges[0][0], ranges[-1][1]
        marked = source[:first] + start_marker + source[first:last] + end_marker + source[last:]
    html = parser.render(marked)
    target = None
    if start_marker in html and end_marker in html:
        document = QTextDocument()
        document.setHtml(html)
        plain = document.toPlainText()
        first, last = plain.find(start_marker), plain.find(end_marker)
        if 0 <= first < last:
            before = plain[:first]
            selected = plain[first + 1:last]
            start = len(before.encode("utf-16-le")) // 2
            target = (start, start + len(selected.encode("utf-16-le")) // 2)
    clean = html.replace(start_marker, "").replace(end_marker, "")
    document = QTextDocument()
    document.setHtml(clean)
    return clean, target, document.toPlainText()
