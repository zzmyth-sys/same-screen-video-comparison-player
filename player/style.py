"""全局深色主题：参考 HTML 深色模式设计稿（中性色阶 + 白色强调）。"""

# 与参考设计稿一致的调色板
BG_PRIMARY = "#1a1a1a"      # 卡片 / 深色面板
BG_SECONDARY = "#242424"    # 页面背景 / 工具栏 / 进度行 / 状态栏
BG_TERTIARY = "#2e2e2e"     # 悬停 / 选中
TEXT_PRIMARY = "#f0f0f0"
TEXT_SECONDARY = "#b0b0b0"
TEXT_TERTIARY = "#808080"
TEXT_QUATERNARY = "#555555"
BORDER = "#333333"
ACCENT = "#f0f0f0"
DANGER = "#e74c3c"
VIDEO_BG = "#0a0a0a"


STYLE = f"""
* {{
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", "PingFang SC";
    font-size: 13px;
    color: {TEXT_PRIMARY};
}}
QMainWindow, QWidget {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
}}
QLabel {{
    background: transparent;
    color: {TEXT_PRIMARY};
}}

/* ========== 启动页 ========== */
QFrame#configCard {{
    background-color: {BG_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QLabel#sectionLabel {{
    font-size: 13px;
    font-weight: 500;
    color: {TEXT_SECONDARY};
}}
QLabel#launchTitle {{
    font-size: 28px;
    font-weight: 500;
    color: {TEXT_PRIMARY};
}}
QLabel#launchSubtitle {{
    font-size: 14px;
    color: {TEXT_TERTIARY};
}}
QFrame#hintRow {{
    background-color: {BG_SECONDARY};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QLabel#hintText {{
    font-size: 13px;
    color: {TEXT_TERTIARY};
}}

/* 药丸单选 */
QRadioButton#pill {{
    background-color: {BG_PRIMARY};
    border: 1.5px solid {BORDER};
    border-radius: 10px;
    padding: 12px 16px;
    color: {TEXT_SECONDARY};
    font-size: 14px;
}}
QRadioButton#pill:hover {{
    border-color: {TEXT_QUATERNARY};
}}
QRadioButton#pill:checked {{
    border-color: {ACCENT};
    background-color: {BG_TERTIARY};
    color: {TEXT_PRIMARY};
    font-weight: 500;
}}
QRadioButton#pill::indicator {{
    width: 0px;
    height: 0px;
}}

/* ========== 通用按钮 ========== */
QPushButton {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    color: {TEXT_SECONDARY};
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {BG_TERTIARY};
    color: {TEXT_PRIMARY};
}}
QPushButton:pressed {{
    background-color: {BG_PRIMARY};
}}
QPushButton:checked {{
    background-color: {BG_TERTIARY};
    color: {TEXT_PRIMARY};
}}
QPushButton#primaryButton {{
    background-color: {ACCENT};
    color: {BG_PRIMARY};
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 500;
    padding: 14px 24px;
}}
QPushButton#primaryButton:hover {{
    background-color: #e2e2e2;
    color: {BG_PRIMARY};
}}
QPushButton#primaryButton:pressed {{
    background-color: #d2d2d2;
}}
QPushButton#toolButton {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    color: {TEXT_SECONDARY};
    font-size: 13px;
}}
QPushButton#toolButton:hover {{
    background-color: {BG_TERTIARY};
    color: {TEXT_PRIMARY};
}}
QPushButton#toolButton:checked {{
    background-color: {BG_TERTIARY};
    color: {TEXT_PRIMARY};
}}
QPushButton#toolButtonDanger {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    color: {DANGER};
    font-size: 13px;
}}
QPushButton#toolButtonDanger:hover {{
    background-color: rgba(231, 76, 60, 0.10);
    color: #ff6b5e;
}}

/* ========== 播放器页 ========== */
QFrame#toolbar {{
    background-color: {BG_SECONDARY};
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}}
QFrame#divider {{
    background-color: {BORDER};
}}
QFrame#timeline {{
    background-color: {BG_SECONDARY};
    border-bottom: 1px solid {BORDER};
}}
QLabel#timeLabel {{
    font-family: Consolas, "Cascadia Code", "SF Mono", monospace;
    font-size: 12px;
    color: {TEXT_TERTIARY};
    min-width: 110px;
}}

/* 进度条：细轨道 + 圆形滑块，对齐参考稿 */
QSlider::groove:horizontal {{
    height: 4px;
    background: {BORDER};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT};
    border-radius: 2px;
}}
QSlider::add-page:horizontal {{
    background: {BORDER};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
    background: {ACCENT};
    border: 3px solid {BG_SECONDARY};
}}
QSlider::handle:horizontal:hover {{
    background: #ffffff;
}}

/* ========== 状态栏 ========== */
QStatusBar {{
    background: {BG_SECONDARY};
    color: {TEXT_TERTIARY};
    border-top: 1px solid {BORDER};
    font-size: 12px;
}}
QStatusBar::item {{
    border: none;
}}
QLabel#statusHint {{
    color: {TEXT_TERTIARY};
    font-size: 12px;
}}
QLabel#statusDot {{
    color: rgba(255, 255, 255, 100);
    font-size: 12px;
}}
QLabel#kbd {{
    background: {BG_TERTIARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    font-family: Consolas, "Cascadia Code", monospace;
    font-size: 11px;
    padding: 1px 5px;
    color: {TEXT_SECONDARY};
}}

QMessageBox {{
    background-color: {BG_PRIMARY};
}}
QToolTip {{
    background-color: {BG_TERTIARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
}}
VideoPane {{
    background-color: {VIDEO_BG};
}}
WipePane {{
    background-color: {VIDEO_BG};
}}
"""


def apply_style(app) -> None:
    """给应用套用深色主题。"""
    app.setStyle("Fusion")  # 让 QSS 在所有平台渲染一致
    app.setStyleSheet(STYLE)
