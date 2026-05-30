#!/bin/bash
# Chạy bot Bothuchi trên Linux
# venv nằm cùng thư mục với main.py

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"

# Tạo venv nếu chưa có
if [ ! -d "$VENV" ]; then
    echo "Tạo virtual environment..."
    python3 -m venv "$VENV"
fi

# Kích hoạt venv
source "$VENV/bin/activate"

# Cài / cập nhật thư viện
pip install -q -r "$DIR/requirements.txt"

# Tạo .env nếu chưa có
if [ ! -f "$DIR/.env" ]; then
    cp "$DIR/.env.example" "$DIR/.env"
    echo ""
    echo "⚠️  Chưa có file .env — đã tạo từ .env.example"
    echo "    Hãy điền TELEGRAM_BOT_TOKEN vào file $DIR/.env rồi chạy lại."
    exit 1
fi

# Chạy bot
cd "$DIR"
echo "Khởi động bot..."
python main.py
