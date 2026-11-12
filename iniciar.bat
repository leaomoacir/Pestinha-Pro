@echo off
cd /d "%~dp0"

set "PYW="
if exist "%LOCALAPPDATA%\Python\pythoncore-3.15-64\pythonw.exe" (
    set "PYW=%LOCALAPPDATA%\Python\pythoncore-3.15-64\pythonw.exe"
) else (
    for /f "delims=" %%I in ('where pythonw 2^>nul') do (
        if not defined PYW set "PYW=%%I"
    )
)

if not defined PYW set "PYW=pythonw.exe"

start "" "%PYW%" main.py --direto
exit /b 0

