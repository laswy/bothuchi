# Bothuchi — Telegram Bot Quản Lý Crypto & Tài Chính Cá Nhân

Bot Telegram tích hợp quản lý danh mục crypto và thu chi tài chính cá nhân, kèm HTML dashboard trực quan có thể truy cập từ trình duyệt.

---

## Tính Năng

### 📈 Crypto
- Ghi lệnh mua/bán bằng lệnh nhanh hoặc nhập tự nhiên (`mua BTC 0.01 giá 70k`)
- Xem danh mục với giá thực tế từ CoinGecko (donut chart + bảng lợi nhuận)
- Biểu đồ giá lịch sử theo kỳ (tuần / tháng / năm / toàn bộ)
- Map token symbol → CoinGecko ID
- Import từ CSV/Excel, export toàn bộ lịch sử giao dịch
- Xóa giao dịch lẻ hoặc reset toàn bộ danh mục
- Gửi ảnh danh mục lên kênh Telegram

### 💰 Thu Chi Tài Chính
- Nhập thu nhập / chi tiêu bằng ngôn ngữ tự nhiên (`30k ăn sáng`, `+2tr lương`)
- Phân loại chi tiêu tự động theo từ khóa
- Báo cáo theo tuần / tháng / năm / tất cả với biểu đồ đa chiều
- Đặt ngân sách theo danh mục, cảnh báo khi gần hết / vượt ngân sách
- 🔁 **Định kỳ**: tự động ghi thu/chi lặp lại hàng tháng (lương, tiền thuê, điện nước...)
- Import/export CSV hoặc Excel
- Gửi thông báo thu/chi lên kênh Telegram

### 🌐 HTML Dashboard
- Truy cập từ trình duyệt — dùng `/dashboard` trong bot để lấy link
- Lọc thu chi theo khoảng ngày, danh mục, từ khoá; hiển thị tổng và cân đối
- Thêm / sửa / xóa giao dịch không cần reload trang
- Biểu đồ xu hướng 13 tháng (Chart.js)
- Import file CSV/Excel và export dữ liệu trực tiếp từ trình duyệt
- 💾 **Backup & restore database** — tải xuống hoặc upload file `.db`
- Bảo vệ bằng `?token=...` khi deploy lên server

### ☁️ Deploy
- Hỗ trợ **webhook mode** để chạy trên Railway / Render / fly.io / VPS
- Chỉ cần đặt `WEBHOOK_URL` là bot tự chuyển sang webhook; để trống = polling tại máy
- Hỗ trợ **Cloudflare Tunnel** — chạy tại nhà, không cần mở port, HTTPS miễn phí
- Xem hướng dẫn chi tiết trong [`DEPLOY.md`](DEPLOY.md)

---

## Cài Đặt (Chạy Tại Máy)

### Yêu cầu
- Python 3.10+
- Token bot Telegram từ [@BotFather](https://t.me/BotFather)

### Bước 1 — Clone và cài thư viện

```bash
git clone https://github.com/laswy/bothuchi.git
cd bothuchi
pip install -r requirements.txt
```

### Bước 2 — Cấu hình `.env`

```bash
cp .env.example .env
```

Chỉnh sửa `.env`:

```env
TELEGRAM_BOT_TOKEN=your_token_here

# Để trống = chạy polling tại máy
# Điền URL = tự dùng webhook (deploy lên server)
# WEBHOOK_URL=https://mybot.up.railway.app

# Tùy chọn
# DASHBOARD_SECRET=mat_khau_kho_doan
# CHANNEL_CHAT_ID=-1001974996093
```

### Bước 3 — Chạy bot

**Linux/Mac:**
```bash
./run.sh
```

**Windows:** chạy `run.bat`

**Với Cloudflare Tunnel:**
```bash
./run.sh --tunnel
```

---

## Sử Dụng

### Menu 2 cấp trên Telegram

```
📈 Crypto              💰 Thu Chi
├ 📊 Danh Mục          ├ 💵 Thêm
├ ➕ Mua               ├ 🗑️ Xóa
├ ➖ Bán               ├ 🎯 Ngân Sách
├ 📈 Biểu Đồ          ├ 🔁 Định Kỳ
├ 📋 Báo Cáo          ├ 📋 Báo Cáo
├ 🔗 Map Token        ├ 📈 Biểu Đồ
├ ⬇️ Nhập             ├ ⬇️ Nhập File
└ ⬆️ Xuất             └ ⬆️ Xuất File
```

### Lệnh nhanh

| Lệnh | Mô tả |
|------|--------|
| `/start` | Bắt đầu, xem ID người dùng |
| `/dashboard` | Lấy link HTML dashboard |
| `/help` | Hướng dẫn đầy đủ |
| `/cp_add SYMBOL SL GIA [note]` | Ghi lệnh mua |
| `/cp_sell SYMBOL SL GIA [note]` | Ghi lệnh bán |
| `/cp_map SYMBOL CG_ID` | Map token → CoinGecko |
| `/cp_import` | Import CSV/Excel crypto |

### Nhập tự nhiên

```
mua BTC 0.01 giá 70k
bán SOL tất cả giá 100
30k ăn sáng ngày 26/7
+2tr lương tháng 8
café 45k hôm qua
Hóa đơn VNPT 250k ngày 1/6
```

### 🔁 Thu Chi Định Kỳ

Dùng menu **🔁 Định Kỳ** để thêm khoản thu/chi tự động:
- Bot tự ghi vào đúng ngày trong tháng lúc 8:00 sáng
- Hỗ trợ: ghi hàng tháng hoặc chỉ 1 tháng cụ thể
- Có thể sửa / xóa bất kỳ lúc nào

---

## Định Dạng File Import/Export

### Crypto (CSV/Excel)

| symbol | cg_id | side | qty | price_usd | fee_usd | note | created_at |
|--------|-------|------|-----|-----------|---------|------|------------|
| BTC | bitcoin | BUY | 0.01 | 50000 | 2.5 | spot | 2025-01-01 12:00:00 |

### Tài chính (CSV/Excel)

| Loại | Số tiền | Ghi chú | Danh mục/Nguồn | Ngày | ID |
|------|---------|---------|----------------|------|----|
| Chi tiêu | 50000 | Ăn trưa | Ăn uống | 2025-01-01 12:00:00 | 1 |
| Thu nhập | 2000000 | Lương | Lương | 2025-01-05 09:00:00 | 2 |

---

## Cấu Trúc Dự Án

```
bothuchi/
├── main.py          # Bot Telegram + HTTP/aiohttp server
├── requirements.txt
├── .env.example     # Template biến môi trường
├── Dockerfile       # Build image cho Docker/Railway
├── Procfile         # Railway / Render / Heroku
├── run.sh           # Script chạy trên Linux (có --tunnel flag)
├── run.bat          # Script chạy trên Windows
├── DEPLOY.md        # Hướng dẫn deploy Railway, fly.io, VPS, Cloudflare
└── univer_all_in_one.db  # SQLite (tự tạo khi chạy lần đầu)
```

Database gồm 8 bảng: `crypto_trades`, `crypto_map`, `crypto_prices`, `user_settings`, `expenses`, `incomes`, `budgets`, `recurring_transactions`.

---

## Deploy Lên Server (Webhook Mode)

Chỉ cần đặt `WEBHOOK_URL` — bot tự dùng webhook thay polling:

```env
WEBHOOK_URL=https://mybot.up.railway.app
WEBHOOK_SECRET=random_string
```

Khi webhook mode, **một server aiohttp duy nhất** phục vụ cả:
- `POST /wh/<token>` — Telegram gửi update
- `GET /` — HTML Dashboard
- `GET|POST /api/*` — Dashboard API

Xem hướng dẫn chi tiết từng nền tảng trong [`DEPLOY.md`](DEPLOY.md).

---

## Backup & Khôi Phục Dữ Liệu

Từ HTML Dashboard (nút ở đầu trang):
- **💾 Tải xuống DB** — download file `.db` về máy
- **⬆️ Upload DB** — upload file `.db` để ghi đè (có backup tự động)

Để DB không mất khi redeploy trên Railway:
- Vào Railway → service → **Volumes** → Add Volume mount `/data`
- Thêm biến: `UNIVER_DB_PATH=/data/univer_all_in_one.db`

---

## Yêu Cầu Kỹ Thuật

| Thư viện | Mục đích |
|----------|----------|
| `python-telegram-bot[job-queue,webhooks]==22.*` | Bot Telegram async + webhook + JobQueue |
| `aiohttp>=3.9` | Server webhook + dashboard (webhook mode) |
| `matplotlib` + `numpy` | Vẽ biểu đồ portfolio và thu chi |
| `requests` | Gọi CoinGecko API |
| `python-dotenv` | Đọc file `.env` |
| `openpyxl` | Import/export Excel |
| `pytz` | Múi giờ cho JobQueue định kỳ |
