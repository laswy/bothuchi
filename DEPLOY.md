# Hướng Dẫn Deploy (Webhook Mode)

Bot hỗ trợ **2 chế độ**:
- **Polling** (mặc định): chạy tại máy, không cần cấu hình gì thêm
- **Webhook**: Telegram chủ động đẩy tin — cần URL HTTPS công khai

Chỉ cần đặt `WEBHOOK_URL` là bot tự chuyển sang webhook mode.

---

## Railway.app (Dễ nhất)

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
