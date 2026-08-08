"""开始界面：参考 HTML 设计稿的启动页（logo + 卡片 + 药丸选择 + 主按钮）。"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from .icons import make_icon
from .player_window import PlayerWindow
from .logo import draw_logo


class Logo(QWidget):
    """播放器 logo：圆角方块 + 中轴 + 左侧三角 + 右侧播放条。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 64)

    def paintEvent(self, event):
        p = QPainter(self)
        draw_logo(p, 64)
        p.end()


class StartScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("同屏播放器")
        self.setFixedSize(640, 700)
        self.num_videos = 2
        self.landscape = True
        self.player = None
        self._build_ui()
        self._center()

    def _center(self):
        scr = self.screen().availableGeometry()
        self.move(scr.center().x() - self.width() // 2,
                  scr.center().y() - self.height() // 2)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 32, 24, 32)
        root.setSpacing(24)
        root.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # ---- 头部：logo + 标题 + 副标题 ----
        header = QVBoxLayout()
        header.setSpacing(10)
        header.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        logo = Logo()
        header.addWidget(logo, 0, Qt.AlignmentFlag.AlignHCenter)
        title = QLabel("同屏播放器")
        title.setObjectName("launchTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        title.setFont(font)
        header.addWidget(title)
        subtitle = QLabel("多视频同步对比 · 帧级精度 · 划像检视")
        subtitle.setObjectName("launchSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(subtitle)
        root.addLayout(header)

        # ---- 配置卡片 ----
        card = QFrame()
        card.setObjectName("configCard")
        card.setFixedWidth(480)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(28, 28, 28, 28)
        card_lay.setSpacing(24)

        label1 = QLabel("对比视频数量")
        label1.setObjectName("sectionLabel")
        card_lay.addWidget(label1)
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self.r2 = QRadioButton("2 个视频")
        self.r3 = QRadioButton("3 个视频")
        self.r_land = QRadioButton("横屏 → 上下排列")
        self.r_port = QRadioButton("竖屏 → 左右排列")
        # 两组互相独立：视频数量一组、视频方向一组
        self.count_group = QButtonGroup(self)
        self.count_group.setExclusive(True)
        self.count_group.addButton(self.r2)
        self.count_group.addButton(self.r3)
        self.orient_group = QButtonGroup(self)
        self.orient_group.setExclusive(True)
        self.orient_group.addButton(self.r_land)
        self.orient_group.addButton(self.r_port)
        for b in (self.r2, self.r3, self.r_land, self.r_port):
            b.setAutoExclusive(False)
        self.r2.setObjectName("pill")
        self.r3.setObjectName("pill")
        self.r2.setChecked(True)
        self.r2.setCursor(Qt.CursorShape.PointingHandCursor)
        self.r3.setCursor(Qt.CursorShape.PointingHandCursor)
        row1.addWidget(self.r2, 1)
        row1.addWidget(self.r3, 1)
        card_lay.addLayout(row1)

        label2 = QLabel("视频方向")
        label2.setObjectName("sectionLabel")
        card_lay.addWidget(label2)
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self.r_land.setObjectName("pill")
        self.r_port.setObjectName("pill")
        self.r_land.setChecked(True)
        self.r_land.setCursor(Qt.CursorShape.PointingHandCursor)
        self.r_port.setCursor(Qt.CursorShape.PointingHandCursor)
        row2.addWidget(self.r_land, 1)
        row2.addWidget(self.r_port, 1)
        card_lay.addLayout(row2)

        hint = QFrame()
        hint.setObjectName("hintRow")
        hint_lay = QHBoxLayout(hint)
        hint_lay.setContentsMargins(14, 12, 14, 12)
        hint_lay.setSpacing(10)
        hint_icon = QLabel()
        hint_icon.setPixmap(make_icon("info", "#808080", 18).pixmap(18, 18))
        hint_lay.addWidget(hint_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        hint_text = QLabel("进入后拖入视频文件，或双击窗口选择；2 视频模式支持划像对比。")
        hint_text.setObjectName("hintText")
        hint_text.setWordWrap(True)
        hint_lay.addWidget(hint_text, 1)
        card_lay.addWidget(hint)

        root.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)

        # ---- 主按钮 ----
        self.btn_start = QPushButton("开始对比")
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.setFixedWidth(480)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self._start)
        root.addWidget(self.btn_start, 0, Qt.AlignmentFlag.AlignHCenter)
        root.addStretch(1)

    def _start(self):
        self.num_videos = 2 if self.r2.isChecked() else 3
        self.landscape = self.r_land.isChecked()
        if self.player is not None:
            self.player.close()
            self.player.deleteLater()
        self.player = PlayerWindow(self.num_videos, self.landscape)
        self.player.closed.connect(self._on_player_closed)
        self.hide()
        self.player.show()

    def _on_player_closed(self):
        self.show()
        self._center()
