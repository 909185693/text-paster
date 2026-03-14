@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo    文本快速粘贴工具
echo ========================================
echo.
echo 正在启动程序...
echo.

python main.py

if errorlevel 1 (
    echo.
    echo 程序运行出错!
    echo.
    echo 请确保已安装依赖:
    echo   pip install -r requirements.txt
    echo.
    pause
)
