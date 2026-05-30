# Bothuchi — Telegram Bot Quản Lý Crypto & Tài Chính Cá Nhân

Bot Telegram tích hợp quản lý danh mục crypto và thu chi tài chính cá nhân, kèm dashboard HTML trực quan chạy ngay trên máy.

---

## Tính năng

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
- Import/export CSV hoặc Excel
- Gửi thông báo thu/chi lên kênh Telegram

### 🌐 HTML Dashboard
- Truy cập từ trình duyệt tại `http://localhost:8080?user_id=YOUR_ID`
- Bảng danh mục crypto với Edit / Delete từng dòng
- Danh sách thu nhập và chi tiêu với CRUD đầy đủ
- Biểu đồ xu hướng 13 tháng (Chart.js)
- Import file CSV/Excel và export dữ liệu trực tiếp từ trình duyệt
- Bảo vệ dashboard bằng `?token=...` khi dùng Cloudflare Tunnel

---

## Cài Đặt

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

# Tuỳ chọn:
# UNIVER_DB_PATH=univer_all_in_one.db
# HTML_PORT=8080
# DASHBOARD_SECRET=mat_khau_kho_doan
# CHANNEL_CHAT_ID=-1001974996093
# FINANCE_CHANNEL_ID=-1001974996093
```

### Bước 3 — Chạy bot

```bash
python main.py
```

**Windows:** chạy `run.bat` (đã cấu hình sẵn đường dẫn venv).

---

## Sử Dụng

### Menu 2 cấp trên Telegram

```
📈 Crypto          💰 Thu Chi
├ 📊 Danh Mục      ├ 💵 Thêm
├ ➕ Mua           ├ 🗑️ Xóa
├ ➖ Bán           ├ 🎯 Ngân Sách
├ 📈 Biểu Đồ      ├ 📋 Báo Cáo
├ 📋 Báo Cáo      ├ 📈 Biểu Đồ
├ 🔗 Map Token    ├ ⬇️ Nhập File
├ ⬇️ Nhập         └ ⬆️ Xuất File
└ ⬆️ Xuất
```

### Lệnh nhanh

| Lệnh | Mô tả |
|------|--------|
| `/start` | Bắt đầu, xem ID người dùng |
| `/dashboard` | Xem link HTML dashboard |
| `/help` | Hướng dẫn nhanh |
| `/cp_add SYMBOL SL GIA [note]` | Ghi lệnh mua |
| `/cp_sell SYMBOL SL GIA [note]` | Ghi lệnh bán |
| `/cp_map SYMBOL CG_ID` | Map token |
| `/cp_import` | Import CSV/Excel giao dịch crypto |

### Nhập tự nhiên

```
mua BTC 0.01 giá 70k
bán SOL tất cả giá 100
30k ăn sáng ngày 26/7
+2tr lương tháng 8
café 45k hôm qua
```

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
├── main.py          # Bot Telegram + HTTP dashboard server (~3200 dòng)
├── requirements.txt
├── .env.example     # Template biến môi trường
├── run.bat          # Script chạy 1 lần trên Windows
└── univer_all_in_one.db  # SQLite (tự tạo khi chạy lần đầu)
```

Database gồm 7 bảng: `crypto_trades`, `crypto_map`, `crypto_prices`, `user_settings`, `expenses`, `incomes`, `budgets`.

---

## Mở Dashboard Công Khai (Cloudflare Tunnel)

Để truy cập dashboard từ ngoài mạng nội bộ mà không cần mở port:

```bash
cloudflared tunnel --url http://localhost:8080
```

Đặt `DASHBOARD_SECRET` trong `.env` để yêu cầu `?token=xxx` khi truy cập.

---

## Yêu Cầu Kỹ Thuật

| Thư viện | Mục đích |
|----------|----------|
| `python-telegram-bot==21.*` | Bot Telegram async |
| `matplotlib` + `numpy` | Vẽ biểu đồ portfolio và thu chi |
| `requests` | Gọi CoinGecko API |
| `python-dotenv` | Đọc file `.env` |
| `openpyxl` | Import/export Excel |
