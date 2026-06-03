# Hướng Dẫn Deploy (Webhook Mode)

Bot hỗ trợ **2 chế độ**:
- **Polling** (mặc định): chạy tại máy, không cần cấu hình gì thêm
- **Webhook**: Telegram chủ động đẩy tin — cần URL HTTPS công khai

Chỉ cần đặt `WEBHOOK_URL` là bot tự chuyển sang webhook mode.

---

## Cloudflare Tunnel (Chạy tại máy — Miễn phí, Khuyến nghị)

**Ưu điểm:** Không cần VPS, không cần mở port, không cần domain trả phí.  
Cloudflare làm HTTPS proxy miễn phí từ internet vào máy bạn.

### Yêu cầu
- Tài khoản Cloudflare miễn phí tại [cloudflare.com](https://cloudflare.com)
- Một domain (mua hoặc dùng domain miễn phí) đã thêm vào Cloudflare
- Máy chạy Linux/Windows/Mac

### Cài cloudflared

**Linux/Ubuntu:**
```bash
curl -L https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared jammy main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install cloudflared
```

**Windows:** Tải tại https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

### Thiết lập tunnel có tên (permanent URL)

```bash
# 1. Đăng nhập Cloudflare
cloudflared tunnel login

# 2. Tạo tunnel (đặt tên tùy ý)
cloudflared tunnel create bothuchi

# 3. Xem tunnel ID vừa tạo
cloudflared tunnel list
```

Tạo file cấu hình `~/.cloudflared/config.yml`:

```yaml
tunnel: <TUNNEL_ID>        # ID từ bước trên, dạng uuid
credentials-file: /home/<user>/.cloudflared/<TUNNEL_ID>.json

ingress:
  # Webhook Telegram → port 8443
  - hostname: bot.yourdomain.com
    service: http://localhost:8443

  # Dashboard HTML → port 8080
  - hostname: dash.yourdomain.com
    service: http://localhost:8080

  # Bắt buộc có dòng này ở cuối
  - service: http_status:404
```

```bash
# 4. Trỏ DNS subdomain vào tunnel
cloudflared tunnel route dns bothuchi bot.yourdomain.com
cloudflared tunnel route dns bothuchi dash.yourdomain.com

# 5. Chạy thử
cloudflared tunnel run bothuchi
```

### Cấu hình `.env`

```env
TELEGRAM_BOT_TOKEN=your_token
WEBHOOK_URL=https://bot.yourdomain.com
WEBHOOK_PORT=8443
WEBHOOK_SECRET=random_string_kho_doan
DASHBOARD_SECRET=mat_khau_dashboard
```

### Chạy bot + tunnel cùng lúc

**Terminal 1:**
```bash
./run.sh
```

**Terminal 2:**
```bash
cloudflared tunnel run bothuchi
```

Hoặc dùng 1 lệnh:
```bash
./run.sh & cloudflared tunnel run bothuchi
```

### Tự khởi động khi máy bật (Linux systemd)

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

---

### Nhanh hơn: Quick tunnel (không cần domain, URL tạm)

Dùng để **test thử** — URL thay đổi mỗi lần khởi động:

```bash
# Terminal 1: chạy bot (polling trước)
python main.py

# Terminal 2: lấy URL tạm
cloudflared tunnel --url http://localhost:8443
# → Nhận URL dạng: https://random-name.trycloudflare.com
```

Sau khi có URL, đặt vào `.env`:
```env
WEBHOOK_URL=https://random-name.trycloudflare.com
```
Rồi restart bot. Lưu ý: mỗi lần restart cloudflared thì phải đổi `WEBHOOK_URL`.

---

## Oracle Cloud Free Tier (VPS Miễn Phí Vĩnh Viễn — Khuyến nghị)

**Ưu điểm:** 2 VM ARM miễn phí mãi mãi, 24GB RAM tổng, ổ cứng vĩnh viễn — DB không bao giờ mất.

### Bước 1 — Tạo tài khoản & VM

1. Đăng ký tại [cloud.oracle.com](https://cloud.oracle.com) (cần thẻ tín dụng để xác minh, **không bị trừ tiền**)
2. Vào **Compute → Instances → Create Instance**
3. Cấu hình:
   - **Name**: `bothuchi`
   - **Image**: Ubuntu 22.04 (hoặc 24.04)
   - **Shape**: `VM.Standard.A1.Flex` (ARM — **Always Free**)
     - OCPUs: 2 | Memory: 12 GB *(hoặc 4 OCPU / 24GB nếu chỉ tạo 1 VM)*
   - **SSH keys**: tải lên public key của bạn (hoặc tạo mới và tải private key về)
4. Bấm **Create** → chờ VM chạy → copy **Public IP**

### Bước 2 — Mở port firewall Oracle

Oracle có 2 lớp firewall, phải mở cả hai:

**Lớp 1 — Security List (Oracle Console):**
- Vào VM → **Subnet** → **Security List** → **Add Ingress Rules**
- Thêm rule:
  ```
  Source CIDR: 0.0.0.0/0
  Protocol: TCP
  Port: 8080    ← dashboard
  ```
  *(Nếu dùng webhook trực tiếp, thêm thêm port 8443)*

**Lớp 2 — iptables (trong VM):**
```bash
sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8443 -j ACCEPT
sudo netfilter-persistent save
```

### Bước 3 — SSH vào VM và cài đặt tự động

```bash
ssh ubuntu@<PUBLIC_IP>

# Tải script cài đặt tự động
curl -O https://raw.githubusercontent.com/laswy/bothuchi/main/setup-oracle.sh
chmod +x setup-oracle.sh
./setup-oracle.sh
```

Script sẽ tự động:
- Cài Python 3, git, pip, netfilter-persistent
- Clone repo bothuchi
- Tạo venv và cài thư viện
- Tạo file `.env` và mở editor để bạn điền token
- Cài systemd service tự khởi động

### Bước 4 — Điền thông tin `.env`

```env
TELEGRAM_BOT_TOKEN=your_token_here

# Để trống = dùng polling (đơn giản, không cần domain)
# WEBHOOK_URL=

# Dashboard
HTML_PORT=8080
DASHBOARD_SECRET=mat_khau_kho_doan

# Kênh thông báo (tùy chọn)
# CHANNEL_CHAT_ID=-1001xxxxxxxxx
```

> **Dùng polling là đủ** trên Oracle Cloud — bot chạy 24/7, DB không mất, dashboard tại `http://<IP>:8080?user_id=YOUR_ID`

### Bước 5 — Khởi động bot

```bash
sudo systemctl start bothuchi
sudo systemctl status bothuchi   # kiểm tra đang chạy
sudo journalctl -u bothuchi -f   # xem log realtime
```

### Cập nhật code mới

```bash
cd ~/bothuchi
git pull origin main
sudo systemctl restart bothuchi
```

### (Tùy chọn) Webhook qua Cloudflare Tunnel

Nếu muốn webhook thay polling mà **không cần mua domain**:

```bash
# Cài cloudflared
curl -L https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared jammy main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install -y cloudflared

# Đăng nhập và tạo tunnel
cloudflared tunnel login
cloudflared tunnel create bothuchi

# Cài service
sudo cloudflared service install
```

Cấu hình `~/.cloudflared/config.yml`:
```yaml
tunnel: <TUNNEL_ID>
credentials-file: /home/ubuntu/.cloudflared/<TUNNEL_ID>.json
ingress:
  - hostname: bot.yourdomain.com
    service: http://localhost:8443
  - hostname: dash.yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
```

Thêm vào `.env`:
```env
WEBHOOK_URL=https://bot.yourdomain.com
WEBHOOK_PORT=8443
```

---

1. Push code lên GitHub
2. Vào [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
3. Thêm biến môi trường trong **Variables**:

```
TELEGRAM_BOT_TOKEN=your_token
WEBHOOK_URL=https://<tên-app>.up.railway.app
WEBHOOK_SECRET=random_string_kho_doan
DASHBOARD_SECRET=mat_khau_dashboard
```

> Railway tự set `PORT` — bot dùng luôn, không cần điền `WEBHOOK_PORT`.

4. Deploy → Railway cấp HTTPS tự động → Bot chạy ngay.

**Lưu ý database**: Railway có Volume, thêm volume mount `/data` để giữ DB khi restart.

---

## fly.io (Miễn phí 3 VM)

```bash
# Cài flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Tạo app (chạy 1 lần)
fly launch --no-deploy

# Đặt secrets
fly secrets set TELEGRAM_BOT_TOKEN=your_token
fly secrets set WEBHOOK_URL=https://<app-name>.fly.dev
fly secrets set WEBHOOK_SECRET=random_string
fly secrets set DASHBOARD_SECRET=mat_khau

# Tạo volume giữ DB
fly volumes create botdata --size 1

# Deploy
fly deploy
```

Thêm vào `fly.toml`:
```toml
[mounts]
  source = "botdata"
  destination = "/data"
```

---

## Render.com

1. New Web Service → connect GitHub repo
2. Environment: **Python 3**
3. Build command: `pip install -r requirements.txt`
4. Start command: `python main.py`
5. Thêm biến môi trường:

```
TELEGRAM_BOT_TOKEN=your_token
WEBHOOK_URL=https://<app-name>.onrender.com
WEBHOOK_SECRET=random_string
```

> Render free tier **spin down** sau 15 phút không hoạt động → bot phản hồi chậm lần đầu.
> Nên dùng gói trả phí $7/tháng để luôn bật.

---

## VPS (Ubuntu/Debian) với Nginx

### 1. Cài bot

```bash
git clone https://github.com/laswy/bothuchi.git
cd bothuchi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env   # điền token + WEBHOOK_URL
```

### 2. Cấu hình `.env`

```env
TELEGRAM_BOT_TOKEN=your_token
WEBHOOK_URL=https://yourdomain.com
WEBHOOK_PORT=8443
WEBHOOK_SECRET=random_string
HTML_PORT=8080
DASHBOARD_SECRET=mat_khau
```

### 3. Systemd service

```bash
sudo nano /etc/systemd/system/bothuchi.service
```

```ini
[Unit]
Description=Bothuchi Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bothuchi
EnvironmentFile=/home/ubuntu/bothuchi/.env
ExecStart=/home/ubuntu/bothuchi/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable bothuchi
sudo systemctl start bothuchi
sudo journalctl -u bothuchi -f   # xem log
```

### 4. Nginx reverse proxy

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    # SSL cert (dùng certbot: sudo certbot --nginx)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Webhook — forward đến PTB
    location /wh/ {
        proxy_pass http://127.0.0.1:8443;
        proxy_http_version 1.1;
    }

    # Dashboard HTML
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
    }
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## Docker (Mọi nền tảng)

```bash
# Build
docker build -t bothuchi .

# Chạy với volume giữ DB
docker run -d \
  --name bothuchi \
  --restart always \
  -p 8443:8443 \
  -p 8080:8080 \
  -v $(pwd)/data:/data \
  --env-file .env \
  bothuchi
```

---

## Kiểm tra webhook đã hoạt động

```bash
# Xem trạng thái webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

Kết quả OK:
```json
{
  "url": "https://yourdomain.com/wh/<TOKEN>",
  "has_custom_certificate": false,
  "pending_update_count": 0,
  "last_error_date": null
}
```

Nếu cần xóa webhook (quay lại polling):
```bash
curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
```
