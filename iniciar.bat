@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
    echo O ambiente virtual nao foi encontrado!
    echo Execute "instalar_requisitos.bat" primeiro!
    pause
    exit /b
)
call ".venv\Scripts\activate.bat"
python limpar_audios.py
pause
