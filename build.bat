@echo off
chcp 65001 >nul
echo ============================================
echo   易学 打包脚本 (PyInstaller)
echo ============================================

REM 1. 安装打包工具
pip install pyinstaller

REM 2. 清理旧产物
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist 易学.spec del /q 易学.spec

REM 3. 打包为单文件 exe
pyinstaller --noconfirm --clean --onefile --name 易学 ^
  --add-data "app.py;." ^
  --add-data "data\courses.json;data" ^
  --add-data ".streamlit;.streamlit" ^
  --collect-all streamlit ^
  --collect-all altair ^
  --collect-all pydeck ^
  --copy-metadata streamlit ^
  --hidden-import streamlit.web.cli ^
  run.py

echo.
echo 打包完成，产物在 dist\易学.exe
pause
