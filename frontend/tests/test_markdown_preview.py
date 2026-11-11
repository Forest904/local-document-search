from local_document_search_desktop.markdown_preview import render_preview


def selected(source, word, occurrence=0):
    start = -1
    for _ in range(occurrence + 1):
        start = source.index(word, start + 1)
    html, target, plain = render_preview(source, ((start, start + len(word)),))
    assert target is not None
    encoded = plain.encode("utf-16-le")
    return html, encoded[target[0] * 2:target[1] * 2].decode("utf-16-le")


def test_preview_maps_second_occurrence_across_emphasis_and_link(qt):
    html, match = selected("alpha and **alpha**", "alpha", 1)
    assert match == "alpha"
    assert "<strong>alpha</strong>" in html
    html, match = selected("alpha [alpha](https://example.org)", "alpha", 1)
    assert match == "alpha"
    assert "href=" in html
    _, match = selected("😀 alpha and **alpha**", "alpha", 1)
    assert match == "alpha"


def test_preview_disables_html_and_images_and_supports_table(qt):
    html, match = selected("a | b\n--|--\nalpha | x", "alpha")
    assert match == "alpha"
    assert "<table>" in html
    html, _ = render_preview("<script>bad()</script>\n![alt](https://example.org/img.png)")[:2]
    assert "<script>" not in html
    assert "<img" not in html
    assert "alt" in html
