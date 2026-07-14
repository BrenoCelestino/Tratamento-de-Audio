@echo off
cd /d "%~dp0"
echo =======================================================
echo Preparando Ambiente Virtual Isolado...
echo Isso manterá o sistema livre de modificacoes globais.
echo =======================================================

:: Forçar uso do Python 3.11, que é altamente compatível com IAs pesadas
py -3.11 -m venv .venv
if %errorlevel% neq 0 (
    echo Erro ao criar ambiente com py -3.11. Tentando com python padrao...
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
echo Instalando o motor de IA para a sua RTX (CUDA)... (Aprox. 2.5GB de download!)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
echo Instalando os outros requisitos...
pip install -r requirements.txt

echo =======================================================
echo Instalação Concluida! Pode fechar e usar o iniciar.bat
echo =======================================================
pause
