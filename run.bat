@echo off
setlocal

:: Chuyển về thư mục chứa file run.bat này (bất kể chạy từ đâu)
cd /d "%~dp0"

:: Tạo venv nếu chưa có
if not exist ".venv\Scripts\activate.bat" (
    echo [*] Tao virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [!] Loi: Khong tim thay Python. Hay cai Python 3.10+ tu python.org
        pause
        exit /b 1
    )
)

:: Kích hoạt venv
call .venv\Scripts\activate.bat

:: Cài thư viện nếu chưa có
python -c "import telegram" 2>nul
if errorlevel 1 (
    echo [*] Cai thu vien (lan dau co the mat 1-2 phut)...
    pip install --quiet -r requirements.txt
    if errorlevel 1 (
        echo [!] Loi khi cai thu vien. Kiem tra requirements.txt
        pause
        exit /b 1
    )
)

:: Tạo .env từ mẫu nếu chưa có
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [*] Da tao file .env tu mau. Hay dien TELEGRAM_BOT_TOKEN vao file .env roi chay lai.
        notepad .env
        pause
        exit /b 0
    )
)

echo [*] Khoi dong Bothuchi...
python main.py
pause
endlocal
