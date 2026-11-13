@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
if exist "%LOCALAPPDATA%\Python\pythoncore-3.15-64\python.exe" (
    set "PY=%LOCALAPPDATA%\Python\pythoncore-3.15-64\python.exe"
) else (
    for /f "delims=" %%I in ('where python 2^>nul') do (
        if not defined PY set "PY=%%I"
    )
)
if not defined PY set "PY=python.exe"

"%PY%" main.py --status
echo.
pause

