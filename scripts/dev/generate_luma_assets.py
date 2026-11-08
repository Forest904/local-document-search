"""Generate original Luma SVG/PNG assets and a PNG-backed Windows ICO offline."""
from pathlib import Path
import struct

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "frontend/src/local_document_search_desktop/assets"


def generate():
    app = QGuiApplication.instance() or QGuiApplication([])
    DEST.mkdir(exist_ok=True)
    icons = {
        "search": '<circle cx="10" cy="10" r="6"/><path d="m15 15 5 5"/>',
        "folder": '<path d="M3 7V5h7l2 3h9v12H3Z"/>',
        "settings": '<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="9" cy="6" r="2"/><circle cx="15" cy="12" r="2"/><circle cx="9" cy="18" r="2"/>',
        "back": '<path d="m10 5-7 7 7 7M3 12h18"/>',
        "next": '<path d="m14 5 7 7-7 7M21 12H3"/>',
        "sync": '<path d="M20 10a8 8 0 0 0-14-4L3 9m0-5v5h5M4 14a8 8 0 0 0 14 4l3-3m0 5v-5h-5"/>',
        "document": '<path d="M5 3h9l5 5v13H5ZM14 3v6h5M8 13h8M8 17h6"/>',
        "check": '<path d="m5 12 4 4L19 6"/>',
        "warning": '<path d="m12 3 10 18H2ZM12 9v5M12 17v1"/>',
        "close": '<path d="m6 6 12 12M18 6 6 18"/>',
    }
    for theme, ink, sage, paper in (("light", "#315D50", "#DFEAE2", "#FFFFFF"), ("dark", "#ACD5BC", "#30463A", "#242A26")):
        mark = f'<rect width="64" height="64" rx="19" fill="{sage}"/><path d="M19 15h19l9 9v26H19Z" fill="{paper}"/><path d="M38 15v10h9M25 32h15M25 39h10" fill="none" stroke="{ink}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="m48 6 1.8 5.2L55 13l-5.2 1.8L48 20l-1.8-5.2L41 13l5.2-1.8Z" fill="{ink}"/>'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">{mark}</svg>'
        (DEST / f"logo-{theme}.svg").write_text(svg, encoding="utf-8")
        # The wordmark uses the same Windows system typeface as the application.
        wordmark = f'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="64" viewBox="0 0 240 64">{mark}<text x="80" y="49" font-family="Segoe UI" font-size="48" font-weight="600" fill="{ink}">Luma</text></svg>'
        (DEST / f"wordmark-{theme}.svg").write_text(wordmark, encoding="utf-8")
        renderer = QSvgRenderer(bytes(svg, "utf-8"))
        for size in (16, 24, 32, 48, 64, 128, 256):
            image = QImage(size, size, QImage.Format_ARGB32)
            image.fill(Qt.transparent)
            painter = QPainter(image)
            renderer.render(painter)
            painter.end()
            assert image.save(str(DEST / f"logo-{theme}-{size}.png"))
        for name, shape in icons.items():
            (DEST / f"{name}-{theme}.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{ink}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{shape}</svg>', encoding="utf-8")
    sizes = (16, 24, 32, 48, 64, 128, 256)
    desktop_icon = QImage(str(DEST / "luma-desktop-original.png"))
    if desktop_icon.isNull():
        raise FileNotFoundError(DEST / "luma-desktop-original.png")
    blobs = []
    for size in sizes:
        image = desktop_icon.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        target = DEST / f"luma-desktop-{size}.png"
        assert image.save(str(target))
        blobs.append(target.read_bytes())
    offset = 6 + 16 * len(sizes)
    entries = []
    for size, blob in zip(sizes, blobs):
        entries.append(struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(blob), offset))
        offset += len(blob)
    (DEST / "luma.ico").write_bytes(struct.pack("<HHH", 0, 1, len(sizes)) + b"".join(entries + blobs))


if __name__ == "__main__":
    generate()
