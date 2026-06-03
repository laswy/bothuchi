#!/bin/bash
# Chạy bot Bothuchi trên Linux
# Hỗ trợ: nhập token, dọn bộ nhớ, cài systemd service

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"
SERVICE_NAME="bothuchi"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# ─── Màu sắc ──────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()      { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()     { echo -e "${RED}[ERR]${NC}   $*" >&2; }

# ═══════════════════════════════════════════════════════════
#  1. DỌN DẸP BỘ NHỚ
# ═══════════════════════════════════════════════════════════
cleanup_memory() {
    info "Dọn dẹp bộ nhớ..."

    # Xoá __pycache__ và file .pyc
    find "$DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$DIR" -name "*.pyc" -delete 2>/dev/null || true
    find "$DIR" -name "*.pyo" -delete 2>/dev/null || true

    # Xoá pip cache
    if command -v pip3 &>/dev/null; then
        pip3 cache purge 2>/dev/null || true
    fi
    if [ -f "$VENV/bin/pip" ]; then
        "$VENV/bin/pip" cache purge 2>/dev/null || true
    fi

    # Xoá log cũ (giữ 3 file gần nhất)
    if [ -d "$DIR/logs" ]; then
        ls -t "$DIR/logs"/*.log 2>/dev/null | tail -n +4 | xargs rm -f 2>/dev/null || true
    fi

    # Giải phóng page cache nếu là root
    if [ "$(id -u)" -eq 0 ]; then
        sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
        ok "Đã giải phóng page cache (root)"
    fi

    ok "Dọn dẹp hoàn tất"
}

# ═══════════════════════════════════════════════════════════
#  2. CẤU HÌNH .env / TOKEN
# ═══════════════════════════════════════════════════════════
setup_env() {
    # Tạo .env từ mẫu nếu chưa có
    if [ ! -f "$DIR/.env" ]; then
        if [ -f "$DIR/.env.example" ]; then
            cp "$DIR/.env.example" "$DIR/.env"
            info "Đã tạo .env từ .env.example"
        else
            touch "$DIR/.env"
            info "Đã tạo file .env trống"
        fi
    fi

    # Đọc token hiện tại
    local current_token=""
    current_token=$(grep -E '^TELEGRAM_BOT_TOKEN=' "$DIR/.env" | cut -d'=' -f2- | tr -d '"'"'" 2>/dev/null || true)

    if [ -z "$current_token" ]; then
        echo ""
        warn "Chưa có TELEGRAM_BOT_TOKEN trong .env"
        echo -n "  Nhập Telegram Bot Token (lấy từ @BotFather): "
        read -r token_input
        token_input="${token_input// /}"   # bỏ khoảng trắng

        if [ -z "$token_input" ]; then
            err "Token không được để trống. Hãy chạy lại."
            exit 1
        fi

        # Ghi vào .env
        if grep -q '^TELEGRAM_BOT_TOKEN=' "$DIR/.env" 2>/dev/null; then
            sed -i "s|^TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=${token_input}|" "$DIR/.env"
        else
            echo "TELEGRAM_BOT_TOKEN=${token_input}" >> "$DIR/.env"
        fi
        ok "Đã lưu token vào .env"
    else
        ok "Token hiện tại: ${current_token:0:10}... (đã có)"
    fi
}

# ═══════════════════════════════════════════════════════════
#  3. CÀI ĐẶT SYSTEMD SERVICE (chạy mặc định theo hệ thống)
# ═══════════════════════════════════════════════════════════
install_service() {
    if [ "$(id -u)" -ne 0 ]; then
        warn "Cần quyền root để cài systemd service. Bỏ qua bước này."
        warn "Chạy lại bằng: sudo $0 --install"
        return
    fi

    info "Cài đặt systemd service: ${SERVICE_NAME}"

    local python_path="$VENV/bin/python"
    [ -f "$python_path" ] || python_path="$(command -v python3)"

    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Bothuchi Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$(logname 2>/dev/null || echo "$SUDO_USER" || echo "root")
WorkingDirectory=${DIR}
EnvironmentFile=${DIR}/.env
ExecStart=${python_path} ${DIR}/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "${SERVICE_NAME}.service"
    ok "Service đã được cài và bật tự động khi khởi động"
    echo ""
    echo "  Các lệnh hữu ích:"
    echo "    sudo systemctl start   ${SERVICE_NAME}   # Khởi động"
    echo "    sudo systemctl stop    ${SERVICE_NAME}   # Dừng"
    echo "    sudo systemctl status  ${SERVICE_NAME}   # Trạng thái"
    echo "    sudo journalctl -fu    ${SERVICE_NAME}   # Xem log"
}

# ═══════════════════════════════════════════════════════════
#  4. TẠO VENV & CÀI PACKAGE
# ═══════════════════════════════════════════════════════════
setup_venv() {
    if [ ! -d "$VENV" ]; then
        info "Tạo virtual environment..."
        python3 -m venv "$VENV"
        "$VENV/bin/python" -m ensurepip --upgrade 2>/dev/null || true
        "$VENV/bin/pip" install --upgrade pip --quiet
    fi

    source "$VENV/bin/activate"

    info "Cài / cập nhật thư viện..."
    pip install -q --no-cache-dir -r "$DIR/requirements.txt"
    ok "Thư viện sẵn sàng"
}

# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════

# Xử lý tham số
case "${1:-}" in
    --install)
        setup_env
        setup_venv
        install_service
        exit 0
        ;;
    --clean)
        cleanup_memory
        exit 0
        ;;
    --uninstall)
        if [ "$(id -u)" -ne 0 ]; then err "Cần quyền root."; exit 1; fi
        systemctl disable --now "${SERVICE_NAME}.service" 2>/dev/null || true
        rm -f "$SERVICE_FILE"
        systemctl daemon-reload
        ok "Đã gỡ service ${SERVICE_NAME}"
        exit 0
        ;;
    --tunnel)
        TUNNEL=true
        ;;
    --help|-h)
        echo "Cách dùng: $0 [--install | --clean | --uninstall | --tunnel | --help]"
        echo "  (không tham số)  Dọn bộ nhớ, kiểm tra token, rồi chạy bot"
        echo "  --install        Cài systemd service (tự động khởi động)"
        echo "  --clean          Chỉ dọn bộ nhớ"
        echo "  --uninstall      Gỡ systemd service"
        echo "  --tunnel         Chạy kèm cloudflared tunnel"
        exit 0
        ;;
    "")
        TUNNEL=false
        ;;
    *)
        err "Tham số không hợp lệ: ${1}. Dùng --help để xem hướng dẫn."
        exit 1
        ;;
esac

# Luồng chạy chính
cleanup_memory
setup_env
setup_venv

# Load .env
set -a
# shellcheck disable=SC1091
source "$DIR/.env"
set +a

# Hiển thị chế độ
if [ -n "${WEBHOOK_URL:-}" ]; then
    info "Chế độ: Webhook → ${WEBHOOK_URL}"
else
    info "Chế độ: Polling (thêm WEBHOOK_URL vào .env để dùng webhook)"
fi

# Tunnel nếu cần
if [ "${TUNNEL:-false}" = true ]; then
    if ! command -v cloudflared &>/dev/null; then
        err "cloudflared chưa được cài. Xem DEPLOY.md"
        exit 1
    fi
    info "Khởi động cloudflared tunnel..."
    cloudflared tunnel run bothuchi &
    TUNNEL_PID=$!
    trap "kill \$TUNNEL_PID 2>/dev/null" EXIT
fi

cd "$DIR"
ok "Khởi động bot..."
exec python main.py
