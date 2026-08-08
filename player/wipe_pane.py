"""划像对比窗格：参考 HTML 设计稿（白色分隔线 + 圆形手柄 + 箭头）。"""

import cv2
from PySide6.QtCore import QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .icons import make_icon
from .video_reader import is_video_file


class WipePane(QWidget):
    dropped_file = Signal(str)
    clicked = Signal()
    wheel_zoom = Signal(dict)          # {"factor": float, "fx": float, "fy": float}
    reset_zoom_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumSize(480, 320)
        self._a = None
        self._b = None
        self.divider = 0.5
        self.vertical = True
        self._press_pos = None
        self._a_src = None
        self._b_src = None
        self._src_w = 0
        self._src_h = 0
        self._zoom = 1.0
        self._cx = 0.5
        self._cy = 0.5
        self._ph_icon = make_icon("film", "#555555", 44).pixmap(44, 44)
        self.setCursor(Qt.CursorShape.SizeHorCursor)

    def set_frames(self, a, b):
        if a is self._a_src and b is self._b_src:
            return  # 帧没变，跳过重建
        self._a_src = a
        self._b_src = b
        if a is not None:
            self._src_h, self._src_w = a.shape[:2]
        elif b is not None:
            self._src_h, self._src_w = b.shape[:2]
        self._a, self._a_buf = self._convert(a)
        self._b, self._b_buf = self._convert(b)
        self.update()

    def set_zoom(self, zoom: float, cx: float, cy: float):
        self._zoom = max(1.0, zoom)
        self._cx = cx
        self._cy = cy
        self.update()

    def reset_zoom(self):
        self._zoom = 1.0
        self._cx = self._cy = 0.5
        self.update()

    @property
    def zoom(self) -> float:
        return self._zoom

    def set_vertical(self, vertical: bool):
        self.vertical = vertical
        self.setCursor(Qt.CursorShape.SizeHorCursor if vertical else Qt.CursorShape.SizeVerCursor)
        self.update()

    def _convert(self, bgr):
        if bgr is None:
            return None, None
        h, w = bgr.shape[:2]
        tw = max(1, self.width())
        th = max(1, self.height())
        if w * h > tw * th * 1.5 and (w > tw or h > th):
            s = min(tw / w, th / h)
            dw = max(1, int(w * s))
            dh = max(1, int(h * s))
            bgr = cv2.resize(bgr, (dw, dh), interpolation=cv2.INTER_LINEAR)
            h, w = bgr.shape[:2]
        try:
            return QImage(bgr.data, w, h, 3 * w, QImage.Format.Format_BGR888), bgr
        except TypeError:
            return QImage(bgr.tobytes(), w, h, 3 * w, QImage.Format.Format_BGR888).copy(), None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._a_src is not None or self._b_src is not None:
            self._a, self._a_buf = self._convert(self._a_src)
            self._b, self._b_buf = self._convert(self._b_src)
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#0a0a0a"))
        w, h = self.width(), self.height()
        if self._a is None and self._b is None:
            self._draw_placeholder(p)
            self._draw_border(p)
            return
        if self._a is not None:
            self._draw_cover(p, self._a, w, h)
        if self._b is not None:
            if self.vertical:
                clip = QRect(int(w * self.divider), 0, w - int(w * self.divider), h)
            else:
                clip = QRect(0, int(h * self.divider), w, h - int(h * self.divider))
            p.save()
            p.setClipRect(clip)
            self._draw_cover(p, self._b, w, h)
            p.restore()
        self._draw_handle(p)
        self._draw_border(p)

    def _draw_placeholder(self, p: QPainter):
        w, h = self.width(), self.height()
        icon_h = 44
        total = icon_h + 12 + 20 + 4 + 18
        y0 = (h - total) / 2
        p.setOpacity(0.35)
        p.drawPixmap(int((w - icon_h) / 2), int(y0), self._ph_icon)
        p.setOpacity(1.0)
        font = p.font()
        font.setPointSize(13)
        p.setFont(font)
        p.setPen(QColor("#666666"))
        p.drawText(QRectF(0, y0 + icon_h + 12, w, 20),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                   "划像对比模式")
        font.setPointSize(12)
        p.setFont(font)
        p.setPen(QColor("#4f4f4f"))
        p.drawText(QRectF(24, y0 + icon_h + 12 + 24, w - 48, 18),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                   "拖入 2 个视频后，拖动分隔线对比两侧画面")

    def _draw_handle(self, p: QPainter):
        w, h = self.width(), self.height()
        x = int(w * self.divider)
        y = int(h * self.divider)
        p.setPen(QPen(QColor("#f0f0f0"), 2))
        if self.vertical:
            p.drawLine(x, 0, x, h)
            cx, cy = x, h / 2
        else:
            p.drawLine(0, y, w, y)
            cx, cy = w / 2, y
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#f0f0f0"))
        p.drawEllipse(QRectF(cx - 14, cy - 14, 28, 28))
        p.setPen(QPen(QColor("#1a1a1a"), 2.5, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if self.vertical:
            p.drawLine(cx - 2, cy - 6, cx + 5, cy)
            p.drawLine(cx - 2, cy + 6, cx + 5, cy)
        else:
            p.drawLine(cx - 6, cy - 2, cx, cy + 5)
            p.drawLine(cx + 6, cy - 2, cx, cy + 5)

    def _draw_border(self, p: QPainter):
        p.setPen(QPen(QColor(255, 255, 255, 18), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def _draw_cover(self, p: QPainter, img: QImage, w: int, h: int):
        fw, fh = img.width(), img.height()
        if not fw or not fh:
            return
        scale = max(w / fw, h / fh) * self._zoom
        half_w = (w / 2) / (scale * fw)
        half_h = (h / 2) / (scale * fh)
        cx = 0.5 if half_w >= 0.5 else min(1.0 - half_w, max(half_w, self._cx))
        cy = 0.5 if half_h >= 0.5 else min(1.0 - half_h, max(half_h, self._cy))
        p.save()
        p.translate(w / 2, h / 2)
        p.scale(scale, scale)
        p.drawImage(QRect(-cx * fw, -cy * fh, fw, fh), img)
        p.restore()

    # ---------- 交互 ----------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.position()
            self._set_divider(event.position().x(), event.position().y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._press_pos is not None:
            if (event.position() - self._press_pos).manhattanLength() < 8:
                if self._a is not None or self._b is not None:
                    self.clicked.emit()
        self._press_pos = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._set_divider(event.position().x(), event.position().y())

    def mouseDoubleClickEvent(self, event):
        if self._zoom > 1.01:
            self.reset_zoom_requested.emit()
            return
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        if self._src_w <= 0 or self._src_h <= 0:
            return
        pos = event.position()
        factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        fw, fh = self._src_w, self._src_h
        scale = max(self.width() / fw, self.height() / fh) * self._zoom
        fx = (pos.x() - self.width() / 2) / (scale * fw) + self._cx
        fy = (pos.y() - self.height() / 2) / (scale * fh) + self._cy
        self.wheel_zoom.emit({"factor": factor, "fx": fx, "fy": fy})
        event.accept()

    def _set_divider(self, x: float, y: float):
        if self.vertical:
            self.divider = max(0.02, min(0.98, x / max(1, self.width())))
        else:
            self.divider = max(0.02, min(0.98, y / max(1, self.height())))
        self.update()

    # ---------- 拖放 ----------

    def dragEnterEvent(self, event):
        if any(is_video_file(u.toLocalFile()) for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if is_video_file(path):
                self.dropped_file.emit(path)
                break
        event.acceptProposedAction()
