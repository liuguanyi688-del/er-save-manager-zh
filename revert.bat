@echo off
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
    set /p APPDIR=请把 er-save-manager 文件夹拖到这里，然后回车: 
) else (
    set "APPDIR=%~1"
)
python apply.py --app "%APPDIR%" --revert
echo.
pause
