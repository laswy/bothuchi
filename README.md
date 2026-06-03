# Bothuchi — Telegram Bot Quản Lý Crypto & Tài Chính Cá Nhân

Bot Telegram song ngữ (EN/VI) tích hợp quản lý danh mục crypto, thu chi tài chính cá nhân và HTML Dashboard trực quan có thể truy cập từ trình duyệt.

---

## Tính Năng

### 📈 Crypto
- Ghi lệnh mua/bán bằng lệnh nhanh hoặc nhập tự nhiên (`mua BTC 0.01 giá 70k`)
- Xem danh mục với giá thực tế từ CoinGecko (donut chart + bảng lợi nhuận)
- Biểu đồ giá lịch sử theo kỳ (tuần / tháng / năm / toàn bộ)
- Map token symbol → CoinGecko ID
- Import từ CSV/Excel, export toàn bộ lịch sử giao dịch
- Xóa giao dịch lẻ hoặc reset toàn bộ danh mục

### 💰 Thu Chi Tài Chính
- Nhập thu nhập / chi tiêu bằng ngôn ngữ tự nhiên (`30k ăn sáng`, `+2tr lương`)
- Phân loại chi tiêu tự động theo từ khóa
- Báo cáo theo tuần / tháng / năm / tất cả với biểu đồ đa chiều
- Đặt ngân sách theo danh mục, cảnh báo khi gần hết / vượt ngân sách
- 🔁 **Định kỳ**: tự động ghi thu/chi lặp lại hàng tháng (lương, tiền thuê, điện nước...)
- Import/export CSV hoặc Excel

### 🌐 HTML Dashboard
- Truy cập từ trình duyệt — dùng `/dashboard` hoặc menu **⚙️ Cài Đặt → Dashboard**
- Tự động hiển thị theo ngôn ngữ người dùng (EN/VI) khi có `?user_id=ID` trên URL
- Lọc thu chi theo khoảng ngày, danh mục, từ khoá; hiển thị tổng và cân đối
- Thêm / sửa / xóa giao dịch không cần reload trang
- Biểu đồ xu hướng 13 tháng (Chart.js)
- Import file CSV/Excel và export dữ liệu trực tiếp từ trình duyệt
- 💾 **Backup & restore database** — tải xuống hoặc upload file `.db`
- Bảo vệ bằng `?token=...` khi deploy lên server

### 🌍 Song Ngữ & Tiền Tệ
- Chuyển ngôn ngữ bất kỳ lúc nào: 🇬🇧 English / 🇻🇳 Tiếng Việt
- Hỗ trợ hiển thị số tiền theo **VND (đ)** hoặc **USD ($)**
- Chọn ngôn ngữ tự động đặt tiền tệ mặc định (EN → USD, VI → VND)
- Tất cả menu, báo cáo, prompt đều theo ngôn ngữ đã chọn
- Chỉnh thêm qua `/currency` hoặc menu **⚙️ Cài Đặt**

### ⚙️ Settings (Menu Cài Đặt)
- Nút **⚙️ Cài Đặt** ngay trên màn hình chính
- Thay đổi ngôn ngữ, tiền tệ và lấy link Dashboard — tất cả trong một chỗ

### ☁️ Deploy
- Chạy **polling** tại máy (mặc định)
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
📈 Crypto              💰 Finance / Thu Chi      ⚙️ Settings / Cài Đặt
├ 📊 Portfolio         ├ 💵 Add / Thêm            ├ 🌐 Language / Ngôn Ngữ
├ ➕ Buy / Mua         ├ 🗑️ Delete / Xóa          ├ 💱 Currency / Tiền Tệ
├ ➖ Sell / Bán        ├ 🎯 Budget / Ngân Sách     └ 🌐 Dashboard
├ 📈 Chart             ├ 🔁 Recurring / Định Kỳ
├ 📋 Report            ├ 📋 Report / Báo Cáo
├ 🔗 Map Token         ├ 📈 Chart / Biểu Đồ
├ ⬇️ Import            ├ ⬇️ Import File
└ ⬆️ Export            └ ⬆️ Export File
```

### Lệnh nhanh

| Lệnh | Mô tả |
|------|--------|
| `/start` | Bắt đầu, xem ID người dùng |
| `/dashboard` | Lấy link HTML dashboard |
| `/help` | Hướng dẫn đầy đủ |
| `/language` | Chọn ngôn ngữ |
| `/currency` | Chọn VND hoặc USD |
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
├── main.py          # Bot Telegram + HTTP server + NLP + Dashboard
├── strings.py       # Chuỗi song ngữ EN/VI cho toàn bộ bot
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
| `python-telegram-bot[job-queue]==22.*` | Bot Telegram async + JobQueue |
| `matplotlib` + `numpy` | Vẽ biểu đồ portfolio và thu chi |
| `requests` | Gọi CoinGecko API + tỷ giá VND/USD |
| `python-dotenv` | Đọc file `.env` |
| `openpyxl` | Import/export Excel |
| `pytz` | Múi giờ cho JobQueue định kỳ |

---

## Lịch Sử Phiên Bản

### v2.0 — Settings Menu + Dashboard i18n *(hiện tại)*
- Thêm nút **⚙️ Settings / Cài Đặt** vào menu chính
- Settings menu tích hợp: ngôn ngữ, tiền tệ, link dashboard — trong một chỗ
- HTML Dashboard tự động hiển thị theo ngôn ngữ user (EN/VI) — toàn bộ text, modal, alert JS
- Chọn ngôn ngữ tự động đặt tiền tệ mặc định (EN → USD, VI → VND)
- Sửa lỗi nhập số thập phân USD (`20.5` bị parse thành `2050`)
- Sửa lỗi crash khi chọn ngôn ngữ (incompatible keyboard type với `edit_message_text`)

### v1.5 — Song Ngữ EN/VI + Tiền Tệ VND/USD
- Toàn bộ UI bot (menu, prompt, báo cáo, thông báo) theo ngôn ngữ đã chọn
- Nhãn danh mục thu/chi hiển thị dịch (Salary, Food & Drink...) nhưng lưu DB tiếng Việt
- Hỗ trợ hiển thị và nhập số tiền theo VND hoặc USD với tỷ giá thực tế
- Lệnh `/currency` để chọn tiền tệ độc lập với ngôn ngữ
- Tỷ giá VND/USD lấy từ `open.er-api.com`, cache 1 giờ

### v1.4 — Recurring Transactions (Thu Chi Định Kỳ)
- Giao dịch tự động hàng tháng (lương, tiền thuê, điện nước...)
- Chọn ngày trong tháng và tần suất (hàng tháng / 1 lần/năm)
- Tự ghi lúc 8:00 sáng đúng ngày đã đặt
- Quản lý qua menu 🔁 (xem, sửa số tiền/ghi chú, xóa)

### v1.3 — HTML Dashboard Nâng Cao
- Full CRUD (thêm/sửa/xóa) cho Crypto và Thu Chi trực tiếp từ trình duyệt
- Lọc giao dịch theo ngày, danh mục, từ khoá với quick-filter buttons
- Biểu đồ xu hướng 13 tháng + donut chart thu nhập/chi tiêu
- Backup & restore database ngay từ giao diện web
- Bảo vệ Dashboard bằng `DASHBOARD_SECRET`

### v1.2 — Cloudflare Tunnel + Cải Thiện Deployment
- Hỗ trợ Cloudflare Tunnel (`run.sh --tunnel`) — HTTPS tại máy không cần mở port
- Auto-retry port nếu `8080` bị chiếm (thử `8081`–`8089`)
- `run.sh` cho Linux/Mac, `run.bat` cho Windows với venv tự động
- Hướng dẫn deploy Oracle Cloud Free Tier

### v1.1 — HTML Dashboard + Ngân Sách
- Dashboard web đầu tiên: xem danh mục crypto + tổng quan thu chi
- Đặt ngân sách theo danh mục, cảnh báo khi đạt 90% / 100%
- Import/export CSV & Excel cho cả Crypto và Tài Chính
- Lệnh `/dashboard` để lấy link, hiển thị ID user lúc `/start`

### v1.0 — Ra Mắt
- Bot Telegram quản lý Crypto: mua/bán, portfolio, biểu đồ giá, map CoinGecko
- Thu chi tài chính bằng ngôn ngữ tự nhiên tiếng Việt
- Báo cáo theo tuần/tháng/năm với matplotlib charts
- SQLite database local, polling mode
