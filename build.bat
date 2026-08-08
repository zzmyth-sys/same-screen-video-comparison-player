@echo off
chcp 65001 >nul
python -m PyInstaller --noconfirm --clean --windowed --onefile --name 同屏播放器 --icon icon.ico main.py
echo.
echo 打包完成，exe 位于 dist\同屏播放器.exe
pause
