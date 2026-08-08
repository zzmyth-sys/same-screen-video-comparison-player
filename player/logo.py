"""主 logo 绘制：与参考设计稿一致的播放器标识，供启动页与图标复用。"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF

from .style import BG_PRIMARY, TEXT_PRIMARY


def draw_logo(p: QPainter, size: float, color: str = TEXT_PRIMARY,
              notch: str = BG_PRIMARY) -> None:
    """在 0..size 的方形区域内绘制 logo（基于 48 单位参考网格）。"""
    s = size / 48.0
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 2.5 * s)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(5 * s, 5 * s, 38 * s, 38 * s), 5 * s, 5 * s)
    p.drawLine(QPointF(24 * s, 5 * s), QPointF(24 * s, 43 * s))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(color))
    p.drawPolygon(QPolygonF([
        QPointF(14 * s, 18 * s),
        QPointF(14 * s, 30 * s),
        QPointF(21 * s, 24 * s),
    ]))
    p.drawRoundedRect(QRectF(22 * s, 17 * s, 4 * s, 14 * s), 1.5 * s, 1.5 * s)
    p.setBrush(QColor(notch))
    p.drawRoundedRect(QRectF(22.5 * s, 18.5 * s, 3 * s, 11 * s), 1 * s, 1 * s)
