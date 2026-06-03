@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [*] Tao virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [!] Loi: Khong tim thay Python 3.10+
        echo     Tai ve tai: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

python -c "import telegram" 2>nul
if errorlevel 1 (
    echo [*] Cai thu vien, vui long cho 1-2 phut...
    pip install --quiet -r requirements.txt
    if errorlevel 1 (
        echo [!] Loi cai thu vien. Kiem tra requirements.txt
        pause
        exit /b 1
    )
)

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [*] Da tao file .env
        echo     => Hay dien TELEGRAM_BOT_TOKEN vao file .env roi chay lai
        notepad .env
        pause
        exit /b 0
    )
)

echo [*] Dang khoi dong Bothuchi...
python main.py
pause
endlocal
