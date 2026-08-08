"""真实桌面启动测试：弹出开始界面，3 秒后自动关闭。"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from player.start_screen import StartScreen


def main():
    app = QApplication(sys.argv)
    win = StartScreen()
    win.show()
    QTimer.singleShot(3000, app.quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
