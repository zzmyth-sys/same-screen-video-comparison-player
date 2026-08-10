"""内嵌 SVG 图标：渲染为 QIcon，颜色按主题替换。"""

from functools import lru_cache

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


_ICONS = {
    "play": (
        '<svg viewBox="0 0 24 24" fill="currentColor">'
        '<path d="M8 5v14l11-7z"/></svg>'
    ),
    "pause": (
        '<svg viewBox="0 0 24 24" fill="currentColor">'
        '<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>'
    ),
    "prev": (
        '<svg viewBox="0 0 24 24" fill="currentColor">'
        '<path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>'
    ),
    "next": (
        '<svg viewBox="0 0 24 24" fill="currentColor">'
        '<path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>'
    ),
    "zoom": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="11" cy="11" r="8"/>'
        '<path d="M21 21l-4.35-4.35M11 8v6M8 11h6"/></svg>'
    ),
    "loop": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="17 1 21 5 17 9"/>'
        '<path d="M3 11V9a4 4 0 0 1 4-4h14"/>'
        '<polyline points="7 23 3 19 7 15"/>'
        '<path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>'
    ),
    "layout": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2">'
        '<rect x="3" y="3" width="18" height="18" rx="2"/>'
        '<path d="M3 12h18"/></svg>'
    ),
    "wipe": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2">'
        '<path d="M4 4h7v16H4zM13 4h7v16h-7z"/></svg>'
    ),
    "trash": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round">'
        '<path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6'
        'm3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>'
    ),
    "back": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M19 12H5M12 19l-7-7 7-7"/></svg>'
    ),
    "film": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="2" y="2" width="20" height="20" rx="2.5"/>'
        '<path d="M10 8l6 4-6 4V8z"/></svg>'
    ),
    "info": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round">'
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M12 16v-4M12 8h.01"/></svg>'
    ),
    "drop": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4'
        'M7 10l5 5 5-5M12 15V3"/></svg>'
    ),
    "monitor": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round">'
        '<rect x="2" y="3" width="20" height="14" rx="2"/>'
        '<path d="M8 21h8M12 17v4"/></svg>'
    ),
}


@lru_cache(maxsize=256)
def make_icon(name: str, color: str = "#b0b0b0", size: int = 16) -> QIcon:
    """按名称渲染图标，size 为像素边长；颜色用于替换 SVG 中的 currentColor。"""
    svg = _ICONS[name].replace("currentColor", color)
    renderer = QSvgRenderer(bytes(svg.encode("utf-8")))
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    renderer.render(p, QRectF(0, 0, size, size))
    p.end()
    return QIcon(pm)
