"""单个视频显示窗格：参考 HTML 设计稿（深底、占位图标、角标、拖放高亮）。"""

import cv2
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QFileDialog, QWidget

from .icons import make_icon
from .video_reader import is_video_file


class VideoPane(QWidget):
    video_dropped = Signal(str)
    wheel_zoom = Signal(dict)        # {"factor": float, "fx": float, "fy": float}
    pan_delta = Signal(float, float) # 归一化平移量
    reset_zoom_requested = Signal()
    clicked = Signal()

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.setAcceptDrops(True)
        self.setMinimumSize(240, 160)
        self._frame = None
        self._qimg = None
        self._qbuf = None  # 保存 QImage 引用的缓冲，防止被释放
        self._src_w = 0
        self._src_h = 0
        self._frame_idx = -1
        self._frame_count = 0
        self._filename = ""
        self._zoom = 1.0
        self._cx = 0.5
        self._cy = 0.5
        self._dragging = False
        self._last_pos = None
        self._press_pos = None
        self._drag_over = False
        self._ph_icon = make_icon("film", "#555555", 44).pixmap(44, 44)

    # ---------- 对外接口 ----------

    def set_frame(self, index: int, bgr, frame_count: int, filename: str):
        if index == self._frame_idx and bgr is self._frame:
            return  # 帧没变，跳过重建
        self._frame_idx = index
        self._frame_count = frame_count
        self._filename = filename
        self._frame = bgr
        if bgr is not None:
            self._qimg = self._build_qimage(bgr)
        else:
            self._qimg = None
            self._qbuf = None
        self.update()

    def set_zoom(self, zoom: float, cx: float, cy: float):
        changed = abs(zoom - self._zoom) > 0.001
        self._zoom = max(1.0, zoom)
        self._cx = cx
        self._cy = cy
        if changed and self._frame is not None:
            self._qimg = self._build_qimage(self._frame)
        self.update()

    def reset_zoom(self):
        changed = self._zoom != 1.0
        self._zoom = 1.0
        self._cx = self._cy = 0.5
        if changed and self._frame is not None:
            self._qimg = self._build_qimage(self._frame)
        self.update()

    @property
    def zoom(self) -> float:
        return self._zoom

    # ---------- 绘制 ----------

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#0a0a0a"))
        w, h = self.width(), self.height()
        if self._qimg is None:
            self._draw_placeholder(p)
            self._draw_chip(p, f"视频 {self.index + 1}", Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            self._draw_state(p)
            self._draw_border(p)
            return
        img = self._qimg
        fw, fh = self._src_w, self._src_h
        scale = min(w / fw, h / fh) * self._zoom
        half_w = (w / 2) / scale / fw
        half_h = (h / 2) / scale / fh
        cx = 0.5 if half_w >= 0.5 else min(1.0 - half_w, max(half_w, self._cx))
        cy = 0.5 if half_h >= 0.5 else min(1.0 - half_h, max(half_h, self._cy))
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        p.translate(w / 2, h / 2)
        p.scale(scale, scale)
        p.drawImage(QRectF(-cx * fw, -cy * fh, fw, fh), img)
        p.resetTransform()
        self._draw_overlay(p)
        self._draw_state(p)
        self._draw_border(p)

    def _draw_state(self, p: QPainter):
        """拖放高亮：半透明底 + 虚线描边。"""
        if not self._drag_over:
            return
        p.fillRect(self.rect(), QColor(255, 255, 255, 10))
        pen = QPen(QColor(255, 255, 255, 38), 1, Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(self.rect().adjusted(3, 3, -3, -3))

    def _draw_border(self, p: QPainter):
        p.setPen(QPen(QColor(255, 255, 255, 18), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))

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
                   "拖入文件 或 双击选择")
        font.setPointSize(12)
        p.setFont(font)
        p.setPen(QColor("#4f4f4f"))
        p.drawText(QRectF(0, y0 + icon_h + 12 + 24, w, 18),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                   "支持 MP4 / MKV / MOV / WEBM")

    def _draw_overlay(self, p: QPainter):
        if self._filename:
            text = self._filename
            if self._frame_count > 0:
                text += f"  ·  {self._frame_idx + 1} / {self._frame_count} 帧"
            self._draw_chip(p, text, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        if self._zoom > 1.01:
            self._draw_chip(p, f"{self._zoom:.1f}×", Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            self._draw_chip(p, "拖动平移 · 双击复位",
                            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

    def _draw_chip(self, p: QPainter, text: str, align, margin: int = 10):
        font = p.font()
        font.setPointSize(11)
        p.setFont(font)
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text)
        th = fm.height()
        pad_x, pad_y = 10, 3
        bw, bh = tw + pad_x * 2, th + pad_y * 2
        if align & Qt.AlignmentFlag.AlignRight:
            x = self.width() - margin - bw
        else:
            x = margin
        if align & Qt.AlignmentFlag.AlignBottom:
            y = self.height() - margin - bh
        else:
            y = margin
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 140))
        p.drawRoundedRect(QRectF(x, y, bw, bh), 4, 4)
        p.setPen(QColor(255, 255, 255, 191))
        p.drawText(QRectF(x, y, bw, bh), Qt.AlignmentFlag.AlignCenter, text)

    # ---------- 交互 ----------

    def wheelEvent(self, event):
        if self._qimg is None:
            return
        pos = event.position()
        factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        fw, fh = self._src_w, self._src_h
        scale = min(self.width() / fw, self.height() / fh) * self._zoom
        fx = (pos.x() - self.width() / 2) / (scale * fw) + self._cx
        fy = (pos.y() - self.height() / 2) / (scale * fh) + self._cy
        self.wheel_zoom.emit({"factor": factor, "fx": fx, "fy": fy})
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._qimg is not None and self._zoom > 1.01:
            self._dragging = True
            self._last_pos = event.position()
            self._press_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            self._press_pos = event.position()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._last_pos is not None:
            dx = event.position().x() - self._last_pos.x()
            dy = event.position().y() - self._last_pos.y()
            self._last_pos = event.position()
            fw, fh = self._src_w, self._src_h
            scale = min(self.width() / fw, self.height() / fh) * self._zoom
            self.pan_delta.emit(-dx / (scale * fw), -dy / (scale * fh))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._last_pos = None
        self.unsetCursor()
        if event.button() == Qt.MouseButton.LeftButton and self._press_pos is not None:
            if (event.position() - self._press_pos).manhattanLength() < 8:
                if self._qimg is not None:
                    self.clicked.emit()
        self._press_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self._zoom > 1.01:
            self.reset_zoom_requested.emit()
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"选择视频 {self.index + 1}",
            "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv *.flv *.wmv *.ts *.webm *.m4v)",
        )
        if path:
            self.video_dropped.emit(path)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._frame is not None:
            self._qimg = self._build_qimage(self._frame)
            self.update()

    # ---------- 图像构建 ----------

    def _build_qimage(self, bgr):
        """按显示尺寸缩小后再转为 QImage（BGR888 直读，零拷贝）。"""
        h, w = bgr.shape[:2]
        self._src_w, self._src_h = w, h
        tw = max(1, int(self.width() * self._zoom))
        th = max(1, int(self.height() * self._zoom))
        if w * h > tw * th * 1.5 and (w > tw or h > th):
            s = min(tw / w, th / h)
            dw = max(1, int(w * s))
            dh = max(1, int(h * s))
            bgr = cv2.resize(bgr, (dw, dh), interpolation=cv2.INTER_LINEAR)
            h, w = bgr.shape[:2]
        try:
            # 直接引用 numpy 缓冲，零拷贝
            self._qbuf = bgr
            return QImage(bgr.data, w, h, 3 * w, QImage.Format.Format_BGR888)
        except TypeError:
            return QImage(bgr.tobytes(), w, h, 3 * w, QImage.Format.Format_BGR888).copy()

    # ---------- 拖放 ----------

    def dragEnterEvent(self, event):
        if self._has_video_urls(event):
            self._drag_over = True
            self.update()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._drag_over = False
        self.update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._drag_over = False
        self.update()
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if is_video_file(path):
                self.video_dropped.emit(path)
                break
        event.acceptProposedAction()

    @staticmethod
    def _has_video_urls(event) -> bool:
        return any(is_video_file(u.toLocalFile()) for u in event.mimeData().urls())
