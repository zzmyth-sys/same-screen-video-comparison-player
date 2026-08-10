"""主播放窗口：参考 HTML 设计稿的工具栏 / 进度条 / 状态栏，核心逻辑不变。"""

import os

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .icons import make_icon
from .video_pane import VideoPane
from .video_reader import VideoReader
from .wipe_pane import WipePane


def _fmt(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class PlayerWindow(QMainWindow):
    closed = Signal()

    def __init__(self, num_videos: int, landscape: bool):
        super().__init__()
        self.num_videos = num_videos
        self.landscape = landscape
        self.readers = [None] * num_videos
        self.frames = [None] * num_videos
        self.playing = False
        self.accum = [0.0] * num_videos
        self.tick_fps = 30.0
        self.zoom = 1.0
        self.center = (0.5, 0.5)
        self.wipe_mode = False
        self.wipe_vertical = True
        self.loop_mode = False
        self._centered_once = False
        self._was_playing = False

        self.panes = [VideoPane(i) for i in range(num_videos)]
        self.wipe_pane = WipePane()

        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self._tick)
        self.seek_timer = QTimer(self)
        self.seek_timer.setInterval(33)
        self.seek_timer.timeout.connect(self._on_seek_timer)
        self._drag_seeking = False
        self._pending_resume = False

        self._build_ui()
        self._apply_layout()
        self._connect()
        self._recalc_tick()
        self._update_slider()
        self.statusBar().showMessage("拖入下方窗口加载视频，或双击窗口选择")

    # ---------- 界面搭建 ----------

    def _build_ui(self):
        self.setWindowTitle("同屏播放器 - 对比播放")
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- 顶部工具栏 ----
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(16, 8, 16, 8)
        tb.setSpacing(2)

        self.btn_back = QPushButton(make_icon("back"), "返回")
        self.btn_back.setObjectName("toolButton")
        self.btn_back.setIconSize(QSize(16, 16))
        self.btn_back.setToolTip("返回开始界面 (Esc)")
        self.btn_back.clicked.connect(self.close)
        tb.addWidget(self.btn_back)

        self.btn_play = QPushButton(make_icon("play"), "播放")
        self.btn_play.setObjectName("toolButton")
        self.btn_play.setIconSize(QSize(16, 16))
        self.btn_play.setCheckable(True)
        self.btn_play.setToolTip("播放 / 暂停 (Space)")
        tb.addWidget(self.btn_play)

        self.btn_prev = QPushButton(make_icon("prev"), "上一帧")
        self.btn_prev.setObjectName("toolButton")
        self.btn_prev.setIconSize(QSize(16, 16))
        self.btn_prev.setToolTip("上一帧 (←)")
        tb.addWidget(self.btn_prev)

        self.btn_next = QPushButton(make_icon("next"), "下一帧")
        self.btn_next.setObjectName("toolButton")
        self.btn_next.setIconSize(QSize(16, 16))
        self.btn_next.setToolTip("下一帧 (→)")
        tb.addWidget(self.btn_next)

        tb.addWidget(self._divider())
        self.btn_zoom = QPushButton(make_icon("zoom"), "复位")
        self.btn_zoom.setObjectName("toolButton")
        self.btn_zoom.setIconSize(QSize(16, 16))
        self.btn_zoom.setToolTip("复位缩放 (R)")
        tb.addWidget(self.btn_zoom)

        self.btn_loop = QPushButton(make_icon("loop"), "循环")
        self.btn_loop.setObjectName("toolButton")
        self.btn_loop.setIconSize(QSize(16, 16))
        self.btn_loop.setCheckable(True)
        self.btn_loop.setToolTip("循环播放：播完自动从头开始")
        tb.addWidget(self.btn_loop)

        tb.addStretch(1)

        self.btn_layout = QPushButton(make_icon("layout"), "")
        self.btn_layout.setObjectName("toolButton")
        self.btn_layout.setIconSize(QSize(16, 16))
        tb.addWidget(self.btn_layout)

        self.btn_wipe = QPushButton(make_icon("wipe"), "划像对比")
        self.btn_wipe.setObjectName("toolButton")
        self.btn_wipe.setIconSize(QSize(16, 16))
        self.btn_wipe.setCheckable(True)
        tb.addWidget(self.btn_wipe)

        self.btn_wipe_dir = QPushButton("竖划像")
        self.btn_wipe_dir.setObjectName("toolButton")
        tb.addWidget(self.btn_wipe_dir)

        self.divider2 = self._divider()
        tb.addWidget(self.divider2)

        self.btn_clear = QPushButton(make_icon("trash"), "清空")
        self.btn_clear.setObjectName("toolButtonDanger")
        self.btn_clear.setIconSize(QSize(16, 16))
        tb.addWidget(self.btn_clear)
        root.addWidget(toolbar)

        # ---- 进度行 ----
        timeline = QFrame()
        timeline.setObjectName("timeline")
        tl = QHBoxLayout(timeline)
        tl.setContentsMargins(16, 10, 16, 10)
        tl.setSpacing(14)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 10000)
        self.slider.setToolTip("拖动进度条，所有视频同步跳转")
        tl.addWidget(self.slider, 1)
        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        tl.addWidget(self.time_label)
        root.addWidget(timeline)

        # ---- 内容区：并列页 / 划像页 ----
        self.stack = QStackedWidget()
        self.panes_page = QWidget()
        self.stack.addWidget(self.panes_page)
        self.stack.addWidget(self.wipe_pane)
        root.addWidget(self.stack, 1)

        self.btn_wipe.setVisible(self.num_videos == 2)
        self.btn_wipe_dir.setVisible(False)
        self._refresh_layout_button()
        self._setup_statusbar()

    @staticmethod
    def _divider() -> QFrame:
        d = QFrame()
        d.setObjectName("divider")
        d.setFixedSize(1, 20)
        return d

    def _setup_statusbar(self):
        sb = self.statusBar()
        sb.setSizeGripEnabled(False)
        for name, text in (("drop", "拖入下方加载"), ("monitor", "双击窗口选择")):
            item = QWidget()
            lay = QHBoxLayout(item)
            lay.setContentsMargins(0, 0, 14, 0)
            lay.setSpacing(5)
            icon = QLabel()
            icon.setPixmap(make_icon(name, "#808080", 14).pixmap(14, 14))
            lab = QLabel(text)
            lab.setObjectName("statusHint")
            lay.addWidget(icon)
            lay.addWidget(lab)
            sb.addWidget(item)
        sb.addPermanentWidget(self._kbd_item("Space", "播放"))
        sb.addPermanentWidget(self._dot_label())
        sb.addPermanentWidget(self._kbd_item("←", "逐帧"))
        sb.addPermanentWidget(self._dot_label())
        sb.addPermanentWidget(self._kbd_item("滚轮", "缩放"))

    @staticmethod
    def _kbd_item(key: str, text: str) -> QWidget:
        item = QWidget()
        lay = QHBoxLayout(item)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        k = QLabel(key)
        k.setObjectName("kbd")
        t = QLabel(text)
        t.setObjectName("statusHint")
        lay.addWidget(k)
        lay.addWidget(t)
        return item

    @staticmethod
    def _dot_label() -> QLabel:
        lab = QLabel("·")
        lab.setObjectName("statusDot")
        return lab

    def _apply_layout(self):
        """横屏上下并列 / 竖屏左右并列，2 或 3 个视频通用。"""
        grid = self.panes_page.layout()
        if grid is None:
            grid = QGridLayout(self.panes_page)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setSpacing(0)
        while grid.count():
            item = grid.takeAt(0)
            if item.widget():
                grid.removeWidget(item.widget())
        for i in range(8):
            grid.setRowStretch(i, 0)
            grid.setColumnStretch(i, 0)
        if self.landscape:
            for i, pane in enumerate(self.panes):
                grid.addWidget(pane, i, 0)
                grid.setRowStretch(i, 1)
            grid.setColumnStretch(0, 1)
        else:
            for i, pane in enumerate(self.panes):
                grid.addWidget(pane, 0, i)
                grid.setColumnStretch(i, 1)
            grid.setRowStretch(0, 1)

    def _refresh_layout_button(self):
        self.btn_layout.setText("左右排列" if self.landscape else "上下排列")
        self.btn_layout.setToolTip("切换布局")

    def _connect(self):
        for i, pane in enumerate(self.panes):
            pane.video_dropped.connect(lambda p, idx=i: self._load_video(idx, p))
            pane.videos_dropped.connect(lambda paths, idx=i: self._on_videos_dropped(idx, paths))
            pane.wheel_zoom.connect(self._on_wheel_zoom)
            pane.pan_delta.connect(self._on_pan_delta)
            pane.reset_zoom_requested.connect(self._reset_zoom)
            pane.clicked.connect(self._toggle_play)
        self.wipe_pane.clicked.connect(self._toggle_play)
        self.wipe_pane.dropped_file.connect(self._on_wipe_drop)
        self.wipe_pane.videos_dropped.connect(self._on_wipe_videos_dropped)
        self.wipe_pane.wheel_zoom.connect(self._on_wheel_zoom)
        self.wipe_pane.reset_zoom_requested.connect(self._reset_zoom)

        self.btn_play.clicked.connect(self._toggle_play)
        self.btn_prev.clicked.connect(lambda: self._step_frame(-1))
        self.btn_next.clicked.connect(lambda: self._step_frame(1))
        self.btn_zoom.clicked.connect(self._reset_zoom)
        self.btn_loop.toggled.connect(self._on_loop_toggled)
        self.btn_layout.clicked.connect(self._toggle_layout)
        self.btn_wipe.clicked.connect(self._toggle_wipe)
        self.btn_wipe_dir.clicked.connect(self._toggle_wipe_dir)
        self.btn_clear.clicked.connect(self._clear_videos)

        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderReleased.connect(self._on_slider_released)
        self.slider.valueChanged.connect(self._on_slider_value)

        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self._toggle_play)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, lambda: self._step_frame(-1))
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, lambda: self._step_frame(1))
        QShortcut(QKeySequence(Qt.Key.Key_R), self, self._reset_zoom)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.close)

    # ---------- 视频加载 ----------

    def _load_video(self, index: int, path: str):
        if not os.path.isfile(path):
            return
        try:
            reader = VideoReader(path)
        except Exception as exc:
            QMessageBox.warning(self, "无法打开视频", str(exc))
            return
        old = self.readers[index]
        if old is not None:
            old.release()
        self.readers[index] = reader
        self.frames[index] = None
        reader.read_index(0)
        self.frames[index] = reader.frame_bgr()
        self._recalc_tick()
        self._refresh_panes()
        self._update_slider()
        self.statusBar().showMessage(f"已加载视频 {index + 1}：{os.path.basename(path)}", 4000)

    def _recalc_tick(self):
        if self.readers[0] is not None:
            self.tick_fps = self.readers[0].fps or 30.0

    def _on_wipe_drop(self, path: str):
        if self.readers[0] is None:
            self._load_video(0, path)
        else:
            self._load_video(1, path)

    def _on_videos_dropped(self, index: int, paths: list):
        """一次拖入多个文件：单个文件仍按目标窗口加载，多个文件自动依次填入。"""
        paths = [p for p in paths if os.path.isfile(p)][:self.num_videos]
        if not paths:
            return
        if len(paths) == 1:
            self._load_video(index, paths[0])
            return
        self._assign_videos(paths)

    def _on_wipe_videos_dropped(self, paths: list):
        paths = [p for p in paths if os.path.isfile(p)][:2]
        if not paths:
            return
        if len(paths) == 1:
            self._on_wipe_drop(paths[0])
            return
        self._assign_videos(paths)

    def _assign_videos(self, paths: list):
        """先把文件填入空窗口，没有空位则从第一个窗口开始替换。"""
        targets = [i for i, r in enumerate(self.readers) if r is None]
        order = targets + [i for i in range(self.num_videos) if i not in targets]
        count = 0
        for i, path in zip(order, paths):
            self._load_video(i, path)
            count += 1
        self.statusBar().showMessage(f"已加载 {count} 个视频", 4000)

    # ---------- 播放控制 ----------

    def _toggle_play(self):
        if not any(r is not None for r in self.readers):
            return
        self._set_playing(not self.playing)

    def _set_playing(self, on: bool):
        self.playing = bool(on)
        if self.playing:
            master = self.readers[0]
            at_end = master is not None and (
                master.at_end
                or (master.frame_count and master.current >= master.frame_count - 1)
            )
            if at_end:
                # 播完后再点播放：自动从头开始
                self._restart_all()
            self.accum = [0.0] * self.num_videos
            interval = max(16, min(100, int(1000.0 / self.tick_fps)))
            self.timer.start(interval)
            self.btn_play.setIcon(make_icon("pause"))
            self.btn_play.setText("暂停")
            self.btn_play.setChecked(True)
        else:
            self.timer.stop()
            self.btn_play.setIcon(make_icon("play"))
            self.btn_play.setText("播放")
            self.btn_play.setChecked(False)

    def _tick(self):
        master = self.readers[0]
        if master is None:
            self._set_playing(False)
            return
        ended = False
        for i, r in enumerate(self.readers):
            if r is None:
                continue
            self.accum[i] += r.fps / self.tick_fps
            steps = max(1, int(self.accum[i]))
            self.accum[i] -= int(self.accum[i])
            for _ in range(steps):
                if r.next_frame(wait=False) is not None:
                    continue
                else:
                    break
            if r.at_end:
                ended = True
            self.frames[i] = r.frame_bgr()
        if ended or master.at_end or (
            master.frame_count and master.current >= master.frame_count - 1
        ):
            if self.loop_mode:
                self._restart_all()
                self.accum = [0.0] * self.num_videos
                self._refresh_panes()
                self._update_slider()
                return
            self._set_playing(False)
        self._refresh_panes()
        self._update_slider()

    def _restart_all(self):
        """所有视频回到第 0 帧（同步读取，保证帧号精确）。"""
        for i, r in enumerate(self.readers):
            if r is not None:
                r.seek_relative(0.0)
                self.frames[i] = r.frame_bgr()

    def _on_loop_toggled(self, checked: bool):
        self.loop_mode = checked
        self.statusBar().showMessage(
            "循环播放：开启，播完自动从头开始" if checked else "循环播放：关闭",
            2500,
        )

    def _step_frame(self, delta: int):
        self._pending_resume = False
        self._drag_seeking = False
        self.seek_timer.stop()
        self._set_playing(False)
        for i, r in enumerate(self.readers):
            if r is None:
                continue
            if delta > 0:
                r.next_frame()
            else:
                r.prev_frame()
            self.frames[i] = r.frame_bgr()
        self._refresh_panes()
        self._update_slider()

    # ---------- 进度条 ----------

    def _on_slider_pressed(self):
        self._was_playing = self.playing
        self._set_playing(False)
        self._drag_seeking = True

    def _on_slider_value(self, value: int):
        if not self._drag_seeking:
            return
        self._request_seek_all(value / 10000.0)
        self._update_time_label(value / 10000.0)

    def _on_slider_released(self):
        self._drag_seeking = False
        p = self.slider.value() / 10000.0
        self._request_seek_all(p)
        self._update_time_label(p)
        self._pending_resume = self._was_playing

    def _request_seek_all(self, p: float):
        """请求所有视频后台跳转（非阻塞，拖动进度条时界面不卡）。"""
        started = False
        for r in self.readers:
            if r is not None:
                r.request_seek(p)
                started = True
        if started and not self.seek_timer.isActive():
            self.seek_timer.start()

    def _on_seek_timer(self):
        for r in self.readers:
            if r is not None and r.seek_in_flight():
                return  # 还有视频在后台跳转，继续等
        self.seek_timer.stop()
        for i, r in enumerate(self.readers):
            if r is not None:
                self.frames[i] = r.frame_bgr()
        self._refresh_panes()
        if not self._drag_seeking:
            self._update_slider()
        if self._pending_resume:
            self._pending_resume = False
            self._set_playing(True)

    def _update_time_label(self, p: float):
        master = self.readers[0]
        if master is None or master.frame_count <= 1:
            self.time_label.setText("00:00:00 / 00:00:00")
            return
        self.time_label.setText(f"{_fmt(p * master.duration)} / {_fmt(master.duration)}")

    def _update_slider(self):
        master = self.readers[0]
        if master is None or master.frame_count <= 1:
            self.slider.blockSignals(True)
            self.slider.setValue(0)
            self.slider.blockSignals(False)
            self.time_label.setText("00:00:00 / 00:00:00")
            return
        p = master.progress()
        self.slider.blockSignals(True)
        self.slider.setValue(int(round(p * 10000)))
        self.slider.blockSignals(False)
        cur = master.current / master.fps if master.fps else 0.0
        self.time_label.setText(f"{_fmt(cur)} / {_fmt(master.duration)}")

    # ---------- 缩放与平移 ----------

    def _on_wheel_zoom(self, data: dict):
        self.zoom = max(1.0, min(64.0, self.zoom * data["factor"]))
        self.center = self._clamp_center(data["fx"], data["fy"])
        for pane in self.panes:
            pane.set_zoom(self.zoom, *self.center)
        self.wipe_pane.set_zoom(self.zoom, *self.center)

    def _on_pan_delta(self, dx: float, dy: float):
        self.center = self._clamp_center(self.center[0] + dx, self.center[1] + dy)
        for pane in self.panes:
            pane.set_zoom(self.zoom, *self.center)
        self.wipe_pane.set_zoom(self.zoom, *self.center)

    def _reset_zoom(self):
        self.zoom = 1.0
        self.center = (0.5, 0.5)
        for pane in self.panes:
            pane.set_zoom(1.0, 0.5, 0.5)
        self.wipe_pane.reset_zoom()

    def _clamp_center(self, cx: float, cy: float):
        pane = self.panes[0]
        master = self.readers[0]
        if pane is None or master is None or not master.width or not master.height:
            return max(0.0, min(1.0, cx)), max(0.0, min(1.0, cy))
        fw, fh = master.width, master.height
        scale = min(pane.width() / fw, pane.height() / fh) * self.zoom
        half_w = (pane.width() / 2) / (scale * fw)
        half_h = (pane.height() / 2) / (scale * fh)
        return self._clamp_dim(half_w, cx), self._clamp_dim(half_h, cy)

    @staticmethod
    def _clamp_dim(half: float, c: float) -> float:
        """把中心点夹紧到可视范围内；若整幅画面都可见则保持居中。"""
        if half >= 0.5:
            return 0.5
        return min(1.0 - half, max(half, c))

    # ---------- 布局与划像 ----------

    def _toggle_layout(self):
        # 切换布局时先退出划像模式，回到并列画面
        if self.wipe_mode:
            self._set_wipe_mode(False)
        self.landscape = not self.landscape
        self._apply_layout()
        self._refresh_layout_button()
        self._center_window()

    def _toggle_wipe(self):
        self._set_wipe_mode(not self.wipe_mode)

    def _set_wipe_mode(self, on: bool):
        if self.num_videos != 2:
            on = False
        if on == self.wipe_mode:
            return
        self.wipe_mode = on
        self.stack.setCurrentIndex(1 if on else 0)
        self.btn_wipe.setChecked(on)
        self.btn_wipe_dir.setVisible(on)
        if on:
            self._refresh_panes()
            self.wipe_pane.set_zoom(self.zoom, *self.center)
        self.statusBar().showMessage(
            "划像对比：拖动画面上的分隔线查看两侧画面" if on else "已退出划像对比",
            3000,
        )

    def _toggle_wipe_dir(self):
        self.wipe_vertical = not self.wipe_vertical
        self.wipe_pane.set_vertical(self.wipe_vertical)
        self.btn_wipe_dir.setText("竖划像" if self.wipe_vertical else "横划像")

    def _clear_videos(self):
        if self.wipe_mode:
            self._set_wipe_mode(False)
        self.seek_timer.stop()
        self._pending_resume = False
        self._drag_seeking = False
        self._set_playing(False)
        for r in self.readers:
            if r is not None:
                r.release()
        self.readers = [None] * self.num_videos
        self.frames = [None] * self.num_videos
        self._reset_zoom()
        self._refresh_panes()
        self._update_slider()
        self.statusBar().showMessage("已清空视频，可重新拖入", 3000)

    # ---------- 刷新与窗口 ----------

    def _refresh_panes(self):
        for i, r in enumerate(self.readers):
            pane = self.panes[i]
            if r is not None:
                pane.set_frame(r.current, r.frame_bgr(), r.frame_count,
                               os.path.basename(r.path))
            else:
                pane.set_frame(-1, None, 0, "")
        if self.wipe_mode and self.num_videos >= 2:
            self.wipe_pane.set_frames(self.frames[0], self.frames[1])

    def _center_window(self):
        scr = self.screen().availableGeometry()
        if self.landscape:
            w = min(1400, int(scr.width() * 0.82))
            h = min(920, int(scr.height() * 0.86))
        else:
            w = min(1000, int(scr.width() * 0.72))
            h = min(1320, int(scr.height() * 0.9))
        self.resize(w, h)
        self.move(scr.center().x() - w // 2, scr.center().y() - h // 2)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._centered_once:
            self._centered_once = True
            self._center_window()

    def closeEvent(self, event):
        self._set_playing(False)
        self.seek_timer.stop()
        for r in self.readers:
            if r is not None:
                r.release()
        self.closed.emit()
        super().closeEvent(event)
