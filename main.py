"""同屏播放器 - 多视频同屏对比播放器（程序入口）。"""
import sys

from PySide6.QtWidgets import QApplication

from player.app_icon import app_icon
from player.start_screen import StartScreen
from player.style import apply_style


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("同屏播放器")
    app.setOrganizationName("Local")
    app.setWindowIcon(app_icon())
    apply_style(app)
    win = StartScreen()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
