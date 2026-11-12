@echo off
chcp 65001 >nul
cd /d "%~dp0\.."

echo [1/2] Compilando binarios...
python -m PyInstaller --noconfirm --onefile --windowed --hidden-import win32timezone --name Pestinha --distpath dist --workpath build/work --specpath build main.py
if errorlevel 1 (
    echo [ERRO] Falha ao compilar binarios.
    pause
    exit /b 1
)

echo [2/2] Gerando pacote instalador...
set "ISCC_PATH=C:\Users\Moa\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

if exist "%ISCC_PATH%" (
    "%ISCC_PATH%" "instalador\pestinha.iss"
    echo.
    echo Concluido: instalador\saida\Pestinha-Pro-2.0.0-Instalador.exe
) else (
    echo [AVISO] Inno Setup nao encontrado.
)
pause
