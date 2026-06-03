#!/bin/bash
# Script cài đặt Bothuchi trên Oracle Cloud Free Tier (Ubuntu 22.04/24.04)
# Chạy: ./setup-oracle.sh

set -e
REPO="https://github.com/laswy/bothuchi.git"
INSTALL_DIR="$HOME/bothuchi"
SERVICE="bothuchi"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "=============================="
echo "  Bothuchi — Oracle Cloud Setup"
echo "=============================="
echo ""

# ── 1. Cập nhật hệ thống ──────────────────────────────
info "Cập nhật packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq git python3 python3-pip python3-venv \
     iptables netfilter-persistent iptables-persistent curl nano

# ── 2. Mở port firewall (iptables) ───────────────────
info "Mở port 8080 (dashboard) trong iptables..."
sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT -p tcp --dport 8443 -j ACCEPT 2>/dev/null || true
sudo netfilter-persistent save 2>/dev/null || true

# ── 3. Clone repo ─────────────────────────────────────
if [ -d "$INSTALL_DIR" ]; then
    warn "Thư mục $INSTALL_DIR đã tồn tại — cập nhật code..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    info "Clone repo bothuchi..."
    git clone "$REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# ── 4. Tạo venv và cài thư viện ───────────────────────
info "Tạo virtual environment..."
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip --quiet
info "Cài thư viện (có thể mất 1-2 phút)..."
.venv/bin/pip install -q --no-cache-dir -r requirements.txt

# ── 5. Tạo file .env ──────────────────────────────────
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    info "Đã tạo file .env"
fi

# ── 6. Cài systemd service ────────────────────────────
info "Cài systemd service..."
SERVICE_FILE="/etc/systemd/system/${SERVICE}.service"
PUBLIC_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo "unknown")

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Bothuchi Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/.venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE"

# ── 7. Xong ───────────────────────────────────────────
echo ""
echo "=============================="
echo -e "  ${GREEN}Cài đặt hoàn tất!${NC}"
echo "=============================="
echo ""
echo "Bước tiếp theo:"
echo ""
echo "  1. Điền TELEGRAM_BOT_TOKEN vào .env:"
echo "     nano $INSTALL_DIR/.env"
echo ""
echo "  2. Khởi động bot:"
echo "     sudo systemctl start $SERVICE"
echo ""
echo "  3. Xem log:"
echo "     sudo journalctl -u $SERVICE -f"
echo ""
echo "  4. Truy cập Dashboard:"
echo "     http://$PUBLIC_IP:8080?user_id=YOUR_TELEGRAM_ID"
echo ""
echo "  ⚠️  Nhớ mở port 8080 trong Oracle Security List:"
echo "     Compute → Instance → Subnet → Security List → Add Ingress Rule"
echo "     Source: 0.0.0.0/0 | Protocol: TCP | Port: 8080"
echo ""
warn "Cần cập nhật code? Chạy:"
echo "     cd $INSTALL_DIR && git pull && sudo systemctl restart $SERVICE"
echo ""
