"""生成应用图标：主 logo -> assets/icon.png、icon.ico 与内嵌模块 app_icon.py。"""

import base64
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QImage, QPainter  # noqa: E402

from player.logo import draw_logo  # noqa: E402


def render(size: int) -> QImage:
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    draw_logo(p, size)
    p.end()
    return img


def main():
    assets = os.path.join(ROOT, "assets")
    os.makedirs(assets, exist_ok=True)
    png = os.path.join(assets, "icon.png")
    ico = os.path.join(ROOT, "icon.ico")
    render(512).save(png, "PNG")
    render(256).save(ico, "ICO")

    with open(png, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    module = os.path.join(ROOT, "player", "app_icon.py")
    body = (
        '"""应用图标（由 tools/make_app_icon.py 生成，内嵌 base64，便于打包）。"""\n\n'
        "import base64\n\n"
        f'ICON_PNG_B64 = "{b64}"\n\n\n'
        "def app_icon():\n"
        "    from PySide6.QtGui import QIcon, QPixmap\n"
        "    pm = QPixmap()\n"
        "    pm.loadFromData(base64.b64decode(ICON_PNG_B64))\n"
        "    return QIcon(pm)\n"
    )
    with open(module, "w", encoding="utf-8") as f:
        f.write(body)
    print("生成:", png, ico, module)


if __name__ == "__main__":
    main()
