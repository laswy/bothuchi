# -*- coding: utf-8 -*-
"""
Univer All-in-One Bot
- Telegram bot (python-telegram-bot v21 async)
- Crypto portfolio (CoinGecko, themes, charts)
- Personal finance (income/expense, budgets, reports, charts)
- HTML dashboard server
"""
from __future__ import annotations

import os, io, csv, sqlite3, datetime, tempfile, asyncio, traceback, re, threading, logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env")
except ImportError:
    pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as _fm
import matplotlib.colors as mcolors
from matplotlib.patches import FancyBboxPatch, Circle
from matplotlib import gridspec
import numpy as np
import requests
from typing import List, Dict, Optional

try:
    import openpyxl
    from openpyxl import load_workbook
except Exception:
    openpyxl = None
    load_workbook = None

from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters, ConversationHandler
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== CONFIG =====================
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DB_PATH = os.environ.get("UNIVER_DB_PATH", "univer_all_in_one.db")
HTML_PORT = int(os.environ.get("HTML_PORT", "8080"))
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

OWNER_USER_ID   = 679130099
CHANNEL_CHAT_ID = -1001974996093
FINANCE_CHANNEL_ID = "@congthuchi"

LARGE_AMOUNT_THRESHOLD = 100_000_000

# ===================== THEMES =====================
THEMES = {
    "dark": {
        "name": "🌑 Dark",
        "bg": "#0a0e27", "card_bg": "#151932",
        "text_primary": "#ffffff", "text_secondary": "#94a3b8",
        "accent": "#00d4ff",
        "chart_colors": ["#00d4ff","#00ff88","#ffd700","#ff6b6b","#c56cf0",
                         "#4834d4","#22a6b3","#f0932b","#eb4d4b","#6ab04c",
                         "#30336b","#95afc0","#535c68","#ff9ff3","#48dbfb"],
        "bg_dark": "#1a1a2e", "bg_header": "#16213e",
        "bg_row1": "#0f3460", "bg_row2": "#0e2954", "bg_total": "#16213e",
        "text_light": "#e8e8e8", "text_dim": "#a8a8a8",
        "positive": "#00ff88", "negative": "#ff4757", "neutral": "#ffd700",
        "border": "#2a2a3e",
    },
    "light": {
        "name": "☀️ Light",
        "bg": "#f0f4f8", "card_bg": "#ffffff",
        "text_primary": "#1a202c", "text_secondary": "#4a5568",
        "accent": "#3182ce",
        "chart_colors": ["#3182ce","#38a169","#d69e2e","#e53e3e","#805ad5",
                         "#2b6cb0","#2c7a7b","#c05621","#c53030","#276749",
                         "#553c9a","#2d3748","#718096","#d53f8c","#0987a0"],
        "bg_dark": "#f7fafc", "bg_header": "#e2e8f0",
        "bg_row1": "#edf2f7", "bg_row2": "#f7fafc", "bg_total": "#e2e8f0",
        "text_light": "#1a202c", "text_dim": "#718096",
        "positive": "#38a169", "negative": "#e53e3e", "neutral": "#d69e2e",
        "border": "#cbd5e0",
    },
    "neon": {
        "name": "💚 Neon",
        "bg": "#0d0d0d", "card_bg": "#1a1a1a",
        "text_primary": "#00ff41", "text_secondary": "#00cc33",
        "accent": "#00ff41",
        "chart_colors": ["#00ff41","#ff00ff","#00ffff","#ffff00","#ff6600",
                         "#ff0066","#66ff00","#0066ff","#ff3300","#00ff99",
                         "#ff00cc","#ccff00","#00ccff","#ff9900","#9900ff"],
        "bg_dark": "#0d0d0d", "bg_header": "#1a1a1a",
        "bg_row1": "#0a1a0a", "bg_row2": "#0d0d0d", "bg_total": "#1a1a1a",
        "text_light": "#00ff41", "text_dim": "#009922",
        "positive": "#00ff41", "negative": "#ff0066", "neutral": "#ffff00",
        "border": "#003300",
    },
    "bpink": {
        "name": "🩷 Black Pink",
        "bg": "#0d0010", "card_bg": "#1a0020",
        "text_primary": "#ffffff", "text_secondary": "#d4a0d4",
        "accent": "#ff69b4",
        "chart_colors": ["#ff69b4","#ff1493","#da70d6","#ba55d3","#9400d3",
                         "#ff85c8","#ff4da6","#e040fb","#ce93d8","#f48fb1",
                         "#ff80ab","#ea80fc","#b39ddb","#f8bbd0","#e1bee7"],
        "bg_dark": "#0d0010", "bg_header": "#1a0020",
        "bg_row1": "#250030", "bg_row2": "#1a0020", "bg_total": "#2d0040",
        "text_light": "#ffffff", "text_dim": "#d4a0d4",
        "positive": "#ff69b4", "negative": "#ff1744", "neutral": "#e040fb",
        "border": "#4a0060",
    },
}
DEFAULT_THEME = "dark"
_user_themes: Dict[int, str] = {}

# ===================== RATE LIMITER =====================
RATE_WINDOW = 60
RATE_MAX_CALLS = 10
_rate_store: Dict[int, list] = {}

def is_rate_limited(user_id: int) -> bool:
    now = datetime.datetime.now().timestamp()
    calls = [t for t in _rate_store.get(user_id, []) if now - t < RATE_WINDOW]
    if len(calls) >= RATE_MAX_CALLS:
        _rate_store[user_id] = calls
        return True
    calls.append(now)
    _rate_store[user_id] = calls
    return False

async def check_rate(update: Update) -> bool:
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text(f"⏳ Gửi lệnh quá nhanh. Chờ {RATE_WINDOW}s rồi thử lại.")
        return True
    return False

# ===================== DB MIGRATIONS =====================
_MIGRATIONS_DONE = False

def run_migrations():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Crypto tables
    cur.execute("""CREATE TABLE IF NOT EXISTS crypto_trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, symbol TEXT NOT NULL, cg_id TEXT,
        side TEXT NOT NULL, qty REAL NOT NULL, price_usd REAL NOT NULL,
        fee_usd REAL DEFAULT 0, note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS crypto_map (
        symbol TEXT PRIMARY KEY, cg_id TEXT NOT NULL, name TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS crypto_prices (
        cg_id TEXT NOT NULL, price_usd REAL NOT NULL,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY, theme TEXT NOT NULL DEFAULT 'dark')""")
    # Finance tables
    cur.execute("""CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, amount REAL, note TEXT, category TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS incomes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, amount REAL, source TEXT, note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS budgets (
        user_id INTEGER, category TEXT, amount REAL,
        PRIMARY KEY (user_id, category))""")
    conn.commit()
    conn.close()

def ensure_migrated():
    global _MIGRATIONS_DONE
    if not _MIGRATIONS_DONE:
        run_migrations()
        _MIGRATIONS_DONE = True

def db_conn():
    ensure_migrated()
    return sqlite3.connect(DB_PATH)

# ===================== CRYPTO DB =====================
def db_get_theme(user_id: int) -> str:
    if user_id in _user_themes:
        return _user_themes[user_id]
    conn = db_conn(); cur = conn.cursor()
    cur.execute("SELECT theme FROM user_settings WHERE user_id=?", (user_id,))
    row = cur.fetchone(); conn.close()
    theme = row[0] if row and row[0] in THEMES else DEFAULT_THEME
    _user_themes[user_id] = theme
    return theme

def db_set_theme(user_id: int, theme: str):
    if theme not in THEMES: theme = DEFAULT_THEME
    _user_themes[user_id] = theme
    conn = db_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO user_settings(user_id,theme) VALUES(?,?)
        ON CONFLICT(user_id) DO UPDATE SET theme=excluded.theme""", (user_id, theme))
    conn.commit(); conn.close()

def db_crypto_upsert_map(symbol: str, cg_id: str, name: Optional[str] = None):
    conn = db_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO crypto_map(symbol,cg_id,name) VALUES(?,?,?)
        ON CONFLICT(symbol) DO UPDATE SET cg_id=excluded.cg_id,
        name=COALESCE(excluded.name,crypto_map.name)""",
        (symbol.upper(), cg_id, name))
    conn.commit(); conn.close()

def db_crypto_get_map(symbol: str) -> Optional[str]:
    conn = db_conn(); cur = conn.cursor()
    cur.execute("SELECT cg_id FROM crypto_map WHERE symbol=?", (symbol.upper(),))
    row = cur.fetchone(); conn.close()
    return row[0] if row else None

def db_crypto_add_trade(user_id: int, symbol: str, side: str, qty: float,
                        price_usd: float, note: str = "",
                        created_at: Optional[datetime.datetime] = None,
                        cg_id: Optional[str] = None, fee_usd: float = 0.0):
    conn = db_conn(); cur = conn.cursor()
    if created_at is None: created_at = datetime.datetime.now()
    cur.execute("""INSERT INTO crypto_trades
        (user_id,symbol,cg_id,side,qty,price_usd,fee_usd,note,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        (user_id, symbol.upper(), cg_id, side.upper(), qty, price_usd,
         fee_usd, note, created_at.isoformat()))
    conn.commit(); conn.close()

def db_crypto_positions(user_id: int):
    ensure_migrated()
    conn = db_conn(); cur = conn.cursor()
    cur.execute("""SELECT symbol,
        SUM(CASE WHEN side='BUY' THEN qty ELSE -qty END) AS qty_net,
        SUM(CASE WHEN side='BUY' THEN qty*price_usd+fee_usd ELSE -(qty*price_usd) END) AS invested_usd
        FROM crypto_trades WHERE user_id=?
        GROUP BY symbol HAVING ABS(qty_net)>1e-12 ORDER BY symbol""", (user_id,))
    rows = cur.fetchall()
    result = []
    for symbol, qty_net, invested_usd in rows:
        cur.execute("""SELECT cg_id FROM crypto_trades
            WHERE user_id=? AND symbol=? AND cg_id IS NOT NULL
            ORDER BY created_at DESC LIMIT 1""", (user_id, symbol))
        row = cur.fetchone()
        cg_id = (row[0] if row and row[0] else None) or db_crypto_get_map(symbol) or cg_guess_id_from_symbol(symbol)
        result.append({"symbol": symbol, "qty": float(qty_net or 0),
                       "invested_usd": float(invested_usd or 0), "cg_id": cg_id})
    conn.close()
    return result

def db_crypto_all_trades(user_id: int):
    conn = db_conn(); cur = conn.cursor()
    cur.execute("""SELECT symbol,COALESCE(cg_id,''),side,qty,price_usd,
        fee_usd,COALESCE(note,''),created_at
        FROM crypto_trades WHERE user_id=? ORDER BY created_at ASC""", (user_id,))
    rows = cur.fetchall(); conn.close()
    return rows

def _get_held_qty(user_id: int, symbol: str) -> float:
    conn = db_conn(); cur = conn.cursor()
    cur.execute("""SELECT SUM(CASE WHEN side='BUY' THEN qty ELSE -qty END)
        FROM crypto_trades WHERE user_id=? AND symbol=?""",
        (user_id, symbol.upper()))
    row = cur.fetchone(); conn.close()
    return float(row[0] or 0) if row and row[0] is not None else 0.0

# ===================== FINANCE DB =====================
def db_add_income(user_id: int, amount: float, source: str, note: str,
                  created_at: datetime.datetime = None):
    conn = db_conn(); cur = conn.cursor()
    if created_at is None: created_at = datetime.datetime.now()
    cur.execute("INSERT INTO incomes(user_id,amount,source,note,created_at) VALUES(?,?,?,?,?)",
                (user_id, amount, source, note, created_at.isoformat()))
    conn.commit(); conn.close()

def db_add_expense(user_id: int, amount: float, note: str, category: str,
                   created_at: datetime.datetime = None):
    conn = db_conn(); cur = conn.cursor()
    if created_at is None: created_at = datetime.datetime.now()
    cur.execute("INSERT INTO expenses(user_id,amount,note,category,created_at) VALUES(?,?,?,?,?)",
                (user_id, amount, note, category, created_at.isoformat()))
    conn.commit(); conn.close()

def db_list_expenses_grouped(user_id: int, start_date=None, end_date=None):
    conn = db_conn(); cur = conn.cursor()
    q = "SELECT category,SUM(amount) FROM expenses WHERE user_id=?"
    params = [user_id]
    if start_date and end_date:
        q += " AND created_at>=? AND created_at<?"
        params += [start_date.isoformat(), (end_date+datetime.timedelta(days=1)).isoformat()]
    q += " GROUP BY category ORDER BY SUM(amount) DESC"
    cur.execute(q, tuple(params)); rows = cur.fetchall(); conn.close()
    return rows

def db_list_incomes_grouped(user_id: int, start_date=None, end_date=None):
    conn = db_conn(); cur = conn.cursor()
    q = "SELECT source,SUM(amount) FROM incomes WHERE user_id=?"
    params = [user_id]
    if start_date and end_date:
        q += " AND created_at>=? AND created_at<?"
        params += [start_date.isoformat(), (end_date+datetime.timedelta(days=1)).isoformat()]
    q += " GROUP BY source ORDER BY SUM(amount) DESC"
    cur.execute(q, tuple(params)); rows = cur.fetchall(); conn.close()
    return rows

def db_get_combined_summary(user_id: int, start_date=None, end_date=None):
    conn = db_conn(); cur = conn.cursor()
    params = [user_id]
    inc_q = "SELECT SUM(amount) FROM incomes WHERE user_id=?"
    exp_q = "SELECT SUM(amount) FROM expenses WHERE user_id=?"
    if start_date and end_date:
        extra = " AND created_at>=? AND created_at<?"
        inc_q += extra; exp_q += extra
        params += [start_date.isoformat(), (end_date+datetime.timedelta(days=1)).isoformat()]
    cur.execute(inc_q, tuple(params)); income = cur.fetchone()[0] or 0
    cur.execute(exp_q, tuple(params)); expense = cur.fetchone()[0] or 0
    conn.close()
    return income, expense, income - expense

def db_get_monthly_report(user_id, start_date=None, end_date=None):
    conn = db_conn(); cur = conn.cursor()
    params = [user_id]
    exp_q = "SELECT strftime('%Y-%m',created_at) as m,SUM(amount) FROM expenses WHERE user_id=?"
    inc_q = "SELECT strftime('%Y-%m',created_at) as m,SUM(amount) FROM incomes WHERE user_id=?"
    if start_date and end_date:
        extra = " AND created_at>=? AND created_at<?"
        exp_q += extra; inc_q += extra
        params += [start_date.isoformat(), (end_date+datetime.timedelta(days=1)).isoformat()]
    exp_q += " GROUP BY m ORDER BY m"; inc_q += " GROUP BY m ORDER BY m"
    cur.execute(exp_q, tuple(params)); expenses = cur.fetchall()
    cur.execute(inc_q, tuple(params)); incomes = cur.fetchall()
    conn.close()
    return expenses, incomes

def db_export_data(user_id: int):
    conn = db_conn(); cur = conn.cursor()
    cur.execute("""SELECT 'Chi tiêu',amount,note,category,created_at,id
        FROM expenses WHERE user_id=?
        UNION ALL
        SELECT 'Thu nhập',amount,note,source,created_at,id
        FROM incomes WHERE user_id=?
        ORDER BY created_at DESC""", (user_id, user_id))
    rows = cur.fetchall(); conn.close()
    return rows

def db_get_last_n_transactions(user_id: int, limit: int = 5):
    conn = db_conn(); cur = conn.cursor()
    cur.execute("""SELECT id,'expense',amount,note,category,created_at FROM expenses WHERE user_id=?
        UNION ALL
        SELECT id,'income',amount,note,source,created_at FROM incomes WHERE user_id=?
        ORDER BY created_at DESC LIMIT ?""", (user_id, user_id, limit))
    rows = cur.fetchall(); conn.close()
    return rows

def db_delete_transaction(transaction_id: int, transaction_type: str):
    conn = db_conn(); cur = conn.cursor()
    table = "expenses" if transaction_type == 'expense' else "incomes"
    cur.execute(f"DELETE FROM {table} WHERE id=?", (transaction_id,))
    conn.commit(); conn.close()

def db_reset_all_data(user_id: int):
    conn = db_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM incomes WHERE user_id=?", (user_id,))
    conn.commit(); conn.close()

def db_set_budget(user_id: int, category: str, amount: float):
    conn = db_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO budgets(user_id,category,amount) VALUES(?,?,?)
        ON CONFLICT(user_id,category) DO UPDATE SET amount=excluded.amount""",
        (user_id, category, amount))
    conn.commit(); conn.close()

def db_get_budgets(user_id: int):
    conn = db_conn(); cur = conn.cursor()
    cur.execute("SELECT category,amount FROM budgets WHERE user_id=?", (user_id,))
    rows = cur.fetchall(); conn.close()
    return {r[0]: r[1] for r in rows}

def db_delete_budget(user_id: int, category: str):
    conn = db_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM budgets WHERE user_id=? AND category=?", (user_id, category))
    conn.commit(); conn.close()

def get_month_range(dt: datetime.datetime):
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_m = (start.replace(day=28)+datetime.timedelta(days=4)).replace(day=1)
    end = (next_m-datetime.timedelta(days=1)).replace(hour=23, minute=59, second=59)
    return start, end

def db_sum_expense_by_category_in_period(user_id: int, category: str,
                                          start_date: datetime.datetime,
                                          end_date: datetime.datetime) -> float:
    conn = db_conn(); cur = conn.cursor()
    cur.execute("""SELECT COALESCE(SUM(amount),0) FROM expenses
        WHERE user_id=? AND category=? AND created_at>=? AND created_at<=?""",
        (user_id, category, start_date.isoformat(), end_date.isoformat()))
    val = cur.fetchone()[0] or 0.0; conn.close()
    return float(val)
# ===================== NLP PARSERS (Vietnamese) =====================
VIET_NUM = {
    "k": 1000, "nghin": 1000, "nghìn": 1000, "ngan": 1000, "ngàn": 1000,
    "tr": 1_000_000, "trieu": 1_000_000, "triệu": 1_000_000,
    "củ": 1_000_000, "cu": 1_000_000
}

CATEGORY_KEYWORDS = {
    "Ăn uống": ["ăn","ăn sáng","bữa sáng","sáng","trưa","chiều","tối","cafe","cà phê","trà sữa","quán","nhậu","uống","đi ăn","trà đá","buffet","liên hoan","bánh","kem","đồ uống","thức ăn","đặt món"],
    "Di chuyển": ["taxi","grab","xăng","vé xe","tàu","vé tàu","xe buýt","bus","gửi xe","bến","đi lại","đi xe","xe khách","máy bay","vé máy bay","xích lô","ô tô","đi grab","ship"],
    "Mua sắm": ["mua","đồ","áo","quần","giày","shopee","lazada","tiki","siêu thị","mua hàng","đặt hàng","order","đi chợ","mỹ phẩm","trang sức","phụ kiện"],
    "Hóa đơn": ["điện","nước","wifi","internet","cước","hóa đơn","tiền nhà","truyền hình","gas","rác thải","điện thoại","sim","4g","5g"],
    "Gia đình": ["gia đình","bà ngoại","bố mẹ","con","vợ","chồng","ông bà","anh chị","em","gia tộc","cháu"],
    "Sức khỏe": ["khám","thuốc","bệnh viện","y tế","khám bệnh","xét nghiệm","phẫu thuật","tiêm","bảo hiểm y tế","bảo hiểm sức khỏe"],
    "Giải trí": ["xem phim","anime","game","giải trí","nhạc","hát","karaoke","du lịch","chơi","coi phim","xem ca nhạc","thể thao"],
    "Đầu tư": ["đầu tư","crypto","coin","chứng khoán","cổ phiếu","trái phiếu","mua coin","mua cổ","vàng","bất động sản"],
    "Tiết kiệm": ["tiết kiệm","gửi tiết kiệm","mở sổ","sổ tiết kiệm","để dành","dành dụm"],
    "Khác": ["từ thiện","quà","ủng hộ","học phí","đào tạo","khóa học","mua tên miền","dịch vụ"]
}

INCOME_CATEGORY_KEYWORDS = {
    "Lương": ["lương","tiền công","tiền lương","lương tháng","salary","lương cơ bản","lương chính","lương thời vụ","lương ngày","lương tuần","phụ cấp","trợ cấp","tiền công nhật"],
    "Thưởng": ["thưởng","bonus","thưởng tết","thưởng quý","thưởng năm","thưởng doanh số","thưởng năng suất","thưởng thêm"],
    "Kinh doanh": ["kinh doanh","bán hàng","doanh thu","hoa hồng","chốt đơn","bán online","bán trực tiếp","lợi nhuận shop","thu bán hàng","thu từ bán","thu cửa hàng","thu quán"],
    "Được cho": ["được cho","được tặng","cho tiền","mừng tuổi","mừng cưới","tiền mừng","quà","cho","biếu","tặng","hỗ trợ","cha mẹ cho","người thân cho","bạn bè cho"],
    "Thu hồi nợ": ["trả nợ","thu hồi nợ","được trả","trả lại","người nợ trả","hoàn tiền","hoàn vốn","nhận lại tiền"],
    "Bán tài sản": ["bán tài sản","bán xe","bán nhà","thanh lý","bán đất","bán đồ","thanh lý hàng","bán máy","bán điện thoại","bán vàng","bán máy tính","bán laptop","bán đồ cũ"],
    "Lãi tiết kiệm": ["lãi tiết kiệm","tiền gửi","gửi tiết kiệm","lãi ngân hàng","lãi sổ tiết kiệm","tiền lãi tiết kiệm"],
    "Lãi đầu tư": ["lãi đầu tư","cổ tức","trái tức","lợi nhuận","lãi cổ phiếu","lãi coin","lãi crypto","lãi chứng khoán","lãi quỹ","lợi nhuận đầu tư","lãi trái phiếu","lãi bất động sản","P2P","Crypto"],
    "Khác": ["thu nhập khác","nguồn khác","không xác định","thu lặt vặt"]
}

INCOME_KEYWORDS = [kw for kws in INCOME_CATEGORY_KEYWORDS.values() for kw in kws]
DATE_KEYWORDS = {
    "hôm nay": 0, "hom nay": 0, "nay": 0,
    "hôm qua": -1, "hom qua": -1, "qua": -1,
    "hôm kia": -2, "hom kia": -2
}

def parse_vietnamese_amount(text: str):
    text = text.strip().lower().replace(",","").replace(" ","")
    m = re.match(r"^(\d+)(tr|trieu|triệu|củ|cu)(\d+)$", text)
    if m:
        return int(m.group(1))*1_000_000 + int(m.group(3))*100_000
    m = re.match(r"^(\d+)(k|nghin|nghìn|ngan|ngàn)(\d+)$", text)
    if m:
        return int(m.group(1))*1_000 + int(m.group(3))*100
    for key, mult in VIET_NUM.items():
        if text.endswith(key):
            num = text[:-len(key)]
            if num.isdigit():
                return int(num)*mult
    if text.isdigit():
        return int(text)
    return None

def parse_amount_loose(text: str):
    t = text.lower().replace(" ","")
    t = (t.replace("triệu","tr").replace("trieu","tr")
          .replace("nghìn","k").replace("nghin","k")
          .replace("ngàn","k").replace("ngan","k"))
    m = re.match(r'^(\d+)(tr)(\d+)$', t)
    if m: return int(m.group(1))*1_000_000 + int(m.group(3))*100_000
    m = re.match(r'^(\d+)(k)(\d+)$', t)
    if m: return int(m.group(1))*1_000 + int(m.group(3))*100
    m = re.search(r'(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)(k|tr)?', t)
    if not m: return None
    num, unit = m.group(1), m.group(2) or ""
    num = num.replace(".","").replace(",",".")
    try: val = float(num)
    except ValueError: return None
    if unit == "k": val *= 1000
    elif unit == "tr": val *= 1_000_000
    return round(val)

def parse_amount(text: str) -> float:
    v = parse_vietnamese_amount(text)
    if v is not None: return float(v)
    v2 = parse_amount_loose(text)
    if v2 is not None: return float(v2)
    t = str(text).lower().strip().replace(",","").replace(" ","")
    if t.endswith("tr"):
        try: return float(t[:-2])*1_000_000
        except Exception: pass
    if t.endswith("k"):
        try: return float(t[:-1])*1_000
        except Exception: pass
    return float(re.sub(r'[^0-9.]','',t) or 0)

def parse_date(date_str: str) -> datetime.datetime:
    today = datetime.date.today()
    try: return datetime.datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError: pass
    try: return datetime.datetime.strptime(f"{date_str}/{today.year}", "%d/%m/%Y")
    except ValueError: raise ValueError("Định dạng ngày không hợp lệ. Dùng DD/MM/YYYY hoặc DD/MM.")

def guess_type(text: str) -> str:
    low = text.lower()
    for kw in INCOME_KEYWORDS:
        if kw in low: return "income"
    return "expense"

def guess_category(text: str) -> str:
    low = text.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in low: return cat
    return "Khác"

def guess_income_source(text: str) -> str:
    low = text.lower()
    for src, kws in INCOME_CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in low: return src
    return "Khác"

def guess_date(text: str):
    low = text.lower()
    for k, delta in DATE_KEYWORDS.items():
        if k in low:
            return datetime.datetime.now() + datetime.timedelta(days=delta)
    m = re.search(r'(\d{1,2})[\/\-](\d{1,2})(?:[\/\-](\d{2,4}))?', low)
    if m:
        d, mth, yr = int(m.group(1)), int(m.group(2)), m.group(3)
        year = int(yr) if yr else datetime.datetime.now().year
        try: return datetime.datetime(year, mth, d)
        except ValueError: pass
    return datetime.datetime.now()

def clean_note(text: str) -> str:
    note = re.sub(r'\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?\s*(k|tr|triệu|nghìn|ngàn)?', '', text, flags=re.IGNORECASE)
    return note.strip(" -–—,.;:") or "Không ghi chú"

def nlp_parse_transaction(raw: str):
    amount = parse_amount_loose(raw)
    if amount is None or amount <= 0: return None
    tx_type = guess_type(raw)
    created_at = guess_date(raw)
    note = clean_note(raw)
    category = guess_income_source(raw) if tx_type == "income" else guess_category(raw)
    return {"type": tx_type, "amount": amount, "category": category, "note": note, "created_at": created_at}

# ===================== COINGECKO =====================
def cg_guess_id_from_symbol(symbol: str) -> Optional[str]:
    static = {
        "BTC":"bitcoin","ETH":"ethereum","ATOM":"cosmos","DYDX":"dydx-chain",
        "BABY":"babylon","DYM":"dymension","AURA":"aura-network","ZETA":"zetachain",
        "SOL":"solana","BNB":"binancecoin","TON":"the-open-network",
        "USDT":"tether","USDC":"usd-coin"
    }
    return static.get(symbol.upper())

def cg_simple_price_usd(cg_ids: List[str]) -> Dict[str, float]:
    if not cg_ids: return {}
    ids_param = ",".join(sorted(set(cg_ids)))
    url = f"{COINGECKO_BASE}/simple/price?ids={quote(ids_param)}&vs_currencies=usd"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return {k: float(v.get("usd",0) or 0) for k,v in r.json().items()}
    except Exception: pass
    return {}

def cg_market_chart_usd(cg_id: str, days: int = 365):
    interval = "hourly" if days <= 1 else "daily"
    url = f"{COINGECKO_BASE}/coins/{quote(cg_id)}/market_chart?vs_currency=usd&days={days}&interval={interval}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200: return {}
        out = {}
        for ts, price in r.json().get("prices", []):
            dt = datetime.datetime.utcfromtimestamp(ts/1000.0)
            label = dt.strftime('%H:%M') if days<=1 else dt.date().isoformat()
            out[label] = float(price)
        return out
    except Exception: return {}

def portfolio_history_series(user_id: int, days: int = 365):
    rows = db_crypto_all_trades(user_id)
    if not rows: return [], []
    trades_by_sym = {}; cg_ids = {}
    for symbol, cg_id, side, qty, price, fee, note, created_at in rows:
        sym = symbol.upper()
        trades_by_sym.setdefault(sym,[]).append((side, float(qty), created_at))
        if cg_id: cg_ids[sym] = cg_id
    for sym in trades_by_sym:
        if sym not in cg_ids:
            guess = db_crypto_get_map(sym) or cg_guess_id_from_symbol(sym)
            if guess: cg_ids[sym] = guess
    if not cg_ids: return [], []
    price_hist = {}; all_labels = set()
    for sym, cg in cg_ids.items():
        ph = cg_market_chart_usd(cg, days=days)
        if ph: price_hist[sym] = ph; all_labels.update(ph.keys())
    if not price_hist: return [], []
    labels = sorted(list(all_labels))
    norm_trades = {}
    for sym, arr in trades_by_sym.items():
        tmp = []
        for side, qty, at in arr:
            try: d = datetime.datetime.fromisoformat(at).date().isoformat()
            except Exception: d = str(at).split(" ")[0] if " " in str(at) else labels[0]
            tmp.append((d, side, qty))
        norm_trades[sym] = sorted(tmp, key=lambda x: x[0])
    qty_map = {sym: {} for sym in trades_by_sym}
    running = {sym: 0.0 for sym in trades_by_sym}
    for lb in labels:
        for sym in trades_by_sym:
            for td, side, qty in [t for t in norm_trades[sym] if t[0]==lb]:
                running[sym] += qty if side=="BUY" else -qty
            qty_map[sym][lb] = running[sym]
    values = []
    for lb in labels:
        total = sum(qty_map[sym].get(lb,0)*price_hist.get(sym,{}).get(lb,0) for sym in trades_by_sym)
        values.append(total)
    return labels, values

# ===================== CRYPTO CHARTS =====================
def _chart_font(size: int, bold: bool = False):
    weight = 'bold' if bold else 'normal'
    for name in ['Noto Sans','DejaVu Sans']:
        try: return _fm.FontProperties(family=name, size=size, weight=weight)
        except Exception: pass
    return _fm.FontProperties(size=size, weight=weight)

def gen_portfolio_donut_image(positions, prices, theme: str = DEFAULT_THEME) -> str:
    C = THEMES.get(theme, THEMES[DEFAULT_THEME])
    tokens_data = []
    total_value = 0.0
    for p in positions:
        sym = p.get("symbol","").upper(); qty = float(p.get("qty",0) or 0)
        cg = p.get("cg_id") or cg_guess_id_from_symbol(sym) or ""
        price_now = float(prices.get(cg,0) if cg else 0)
        value = qty * price_now
        if value > 0:
            tokens_data.append({'symbol':sym,'value':value,'qty':qty,'price':price_now})
            total_value += value
    tokens_data.sort(key=lambda x: x['value'], reverse=True)
    if not tokens_data:
        tokens_data = [{'symbol':'N/A','value':1.0,'qty':0,'price':0}]; total_value = 1.0
    if len(tokens_data) > 10:
        others = sum(t['value'] for t in tokens_data[10:])
        tokens_data = tokens_data[:10]
        if others > 0: tokens_data.append({'symbol':'Others','value':others,'qty':0,'price':0})
    for t in tokens_data: t['pct'] = t['value']/total_value*100 if total_value>0 else 0
    n = len(tokens_data); chart_colors = C['chart_colors'][:n]
    fig = plt.figure(figsize=(14,8), facecolor=C['bg'])
    ax_donut = fig.add_axes([0.02,0.08,0.44,0.80])
    ax_legend = fig.add_axes([0.48,0.05,0.50,0.85])
    ax_donut.set_facecolor(C['bg']); ax_legend.set_facecolor(C['bg'])
    ax_legend.axis('off'); ax_donut.set_aspect('equal')
    sizes = [t['value'] for t in tokens_data]
    explode = [0.04 if i<3 else 0 for i in range(n)]
    wedges,_ = ax_donut.pie(sizes, startangle=90, colors=chart_colors, explode=explode,
        wedgeprops=dict(width=0.42,edgecolor=C['bg'],linewidth=2))
    for i,w in enumerate(wedges): w.set_alpha(0.92 if i>=3 else 1.0)
    centre = Circle((0,0),0.53,fc=C['card_bg'],linewidth=2.5,edgecolor=C['accent'],zorder=10)
    ax_donut.add_artist(centre)
    ax_donut.text(0,0.13,'TONG GIA TRI',ha='center',va='center',
        fontproperties=_chart_font(9),color=C['text_secondary'],zorder=11)
    ax_donut.text(0,-0.08,f'${total_value:,.0f}',ha='center',va='center',
        fontproperties=_chart_font(18,bold=True),color=C['accent'],zorder=11)
    for wedge,token in zip(wedges,tokens_data):
        if token['pct'] < 4: continue
        ang = (wedge.theta2+wedge.theta1)/2.0; r=0.70
        ax_donut.text(r*np.cos(np.deg2rad(ang)),r*np.sin(np.deg2rad(ang)),
            f"{token['pct']:.0f}%",ha='center',va='center',
            fontproperties=_chart_font(9,bold=True),color='white',zorder=12)
    ax_legend.text(0.5,0.97,'CHI TIET DANH MUC',transform=ax_legend.transAxes,
        ha='center',fontproperties=_chart_font(14,bold=True),color=C['accent'])
    row_h=0.072; y0=0.90
    for i,token in enumerate(tokens_data):
        if i>=12: break
        y=y0-i*row_h; clr=chart_colors[i] if i<len(chart_colors) else C['accent']
        ax_legend.add_patch(FancyBboxPatch((0.03,y-0.055),0.94,row_h*0.88,
            boxstyle="round,pad=0.008",facecolor=C['card_bg'],edgecolor=clr,
            linewidth=1.5,alpha=0.85,transform=ax_legend.transAxes))
        ax_legend.text(0.07,y-0.018,f"#{i+1}" if i<10 else "~",
            transform=ax_legend.transAxes,fontproperties=_chart_font(9,bold=True),color=clr,va='center')
        ax_legend.text(0.18,y-0.018,token['symbol'],transform=ax_legend.transAxes,
            fontproperties=_chart_font(11,bold=True),color=C['text_primary'],va='center')
        ax_legend.text(0.52,y-0.018,f"${token['value']:,.2f}",transform=ax_legend.transAxes,
            fontproperties=_chart_font(10),color=C['text_primary'],va='center',ha='center')
        ax_legend.text(0.72,y-0.018,f"{token['pct']:.1f}%",transform=ax_legend.transAxes,
            fontproperties=_chart_font(10,bold=True),color=clr,va='center',ha='center')
        fill_w = 0.18*min(token['pct']/100,1.0)
        ax_legend.add_patch(FancyBboxPatch((0.78,y-0.030),0.18,0.012,
            boxstyle="round,pad=0",facecolor=C['card_bg'],edgecolor=C['text_secondary'],
            linewidth=0.8,alpha=0.6,transform=ax_legend.transAxes))
        if fill_w>0:
            ax_legend.add_patch(FancyBboxPatch((0.78,y-0.030),fill_w,0.012,
                boxstyle="round,pad=0",facecolor=clr,edgecolor='none',
                alpha=0.85,transform=ax_legend.transAxes))
    num_tok = len([t for t in tokens_data if t['symbol']!='Others'])
    avg_val = total_value/max(num_tok,1); top_tok = tokens_data[0]
    stats_y = 0.97-12*row_h-0.04
    ax_legend.add_patch(FancyBboxPatch((0.03,stats_y-0.08),0.94,0.095,
        boxstyle="round,pad=0.01",facecolor=C['card_bg'],edgecolor=C['accent'],
        linewidth=1.5,alpha=0.9,transform=ax_legend.transAxes))
    ax_legend.text(0.5,stats_y-0.015,'THONG KE',transform=ax_legend.transAxes,
        ha='center',fontproperties=_chart_font(10,bold=True),color=C['accent'])
    ax_legend.text(0.5,stats_y-0.052,
        f"So token: {num_tok}  |  TB/token: ${avg_val:,.0f}  |  Lon nhat: {top_tok['symbol']} (${top_tok['value']:,.0f})",
        transform=ax_legend.transAxes,ha='center',fontproperties=_chart_font(8.5),color=C['text_secondary'])
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    fig.text(0.5,0.97,'PHAN BO DANH MUC DAU TU CRYPTO',
        ha='center',fontproperties=_chart_font(16,bold=True),color=C['accent'])
    fig.text(0.5,0.01,f'Cap nhat: {timestamp}',
        ha='center',fontproperties=_chart_font(8),color=C['text_secondary'],style='italic')
    fd,path = tempfile.mkstemp(prefix="donut_",suffix=".png"); os.close(fd)
    plt.savefig(path,dpi=180,bbox_inches='tight',facecolor=C['bg'],edgecolor='none')
    plt.close(fig)
    return path

def gen_portfolio_table_image(positions, prices, theme: str = DEFAULT_THEME) -> str:
    C = THEMES.get(theme, THEMES[DEFAULT_THEME])
    rows = []; total_inv = total_val = 0.0
    for p in positions:
        sym=p.get("symbol","").upper(); qty=float(p.get("qty",0) or 0)
        inv=float(max(p.get("invested_usd",0) or 0,0))
        cg=p.get("cg_id") or cg_guess_id_from_symbol(sym) or ""
        price_now=float(prices.get(cg,0) if cg else 0)
        value=qty*price_now; pnl=value-inv; pct=(pnl/inv*100) if inv>1e-12 else 0
        rows.append({'symbol':sym,'qty':f"{qty:,.4f}".rstrip('0').rstrip('.'),'price':f"${price_now:,.2f}",
                     'value':f"${value:,.2f}",'invested':f"${inv:,.2f}",'pnl':f"${pnl:+,.2f}",
                     'pct':pct,'pct_str':f"{pct:+.2f}%"})
        total_inv+=inv; total_val+=value
    total_pnl=total_val-total_inv; total_pct=(total_pnl/total_inv*100) if total_inv>1e-12 else 0
    headers=["Token","So luong","Gia (USD)","Gia tri","Von","Lai/Lo","%"]
    table_data=[headers]
    for r in rows: table_data.append([r['symbol'],r['qty'],r['price'],r['value'],r['invested'],r['pnl'],r['pct_str']])
    if not rows: table_data.append(["N/A","0","$0.00","$0.00","$0.00","$0.00","+0.00%"])
    table_data.append(["TONG CONG","","",f"${total_val:,.2f}",f"${total_inv:,.2f}",f"${total_pnl:+,.2f}",f"{total_pct:+.2f}%"])
    n_rows=len(table_data); fig_h=max(4.5,1.2+0.55*n_rows)
    fig=plt.figure(figsize=(15,fig_h),facecolor=C['bg_dark'])
    ax=fig.add_subplot(111,facecolor=C['bg_dark']); ax.axis('off')
    tbl=ax.table(cellText=table_data,loc='center',cellLoc='center')
    tbl.auto_set_font_size(False); tbl.set_fontsize(10); tbl.scale(1,1.9)
    fp_hdr=_chart_font(10,bold=True); fp_cell=_chart_font(10); fp_bold=_chart_font(10,bold=True)
    for (i,j),cell in tbl.get_celld().items():
        cell.set_edgecolor(C['border']); cell.set_linewidth(0.5)
        if i==0:
            cell.set_facecolor(C['bg_header']); cell.get_text().set_fontproperties(fp_hdr)
            cell.get_text().set_color(C['accent']); cell.set_height(0.08)
        elif i==n_rows-1:
            cell.set_facecolor(C['bg_total']); cell.get_text().set_fontproperties(fp_bold)
            if j in (5,6):
                clr=C['positive'] if total_pnl>0 else (C['negative'] if total_pnl<0 else C['neutral'])
                cell.get_text().set_color(clr)
            else: cell.get_text().set_color(C['accent'])
            cell.set_height(0.08)
        else:
            cell.set_facecolor(C['bg_row1'] if i%2==0 else C['bg_row2'])
            cell.get_text().set_fontproperties(fp_bold if j==0 else fp_cell)
            if j in (5,6) and (i-1)<len(rows):
                pv=rows[i-1]['pct']
                clr=C['positive'] if pv>0 else (C['negative'] if pv<0 else C['neutral'])
                cell.get_text().set_color(clr)
            else: cell.get_text().set_color(C['text_light'])
    pnl_color=C['positive'] if total_pnl>0 else (C['negative'] if total_pnl<0 else C['neutral'])
    ax.text(0.5,1.06,'DANH MUC DAU TU CRYPTO',transform=ax.transAxes,ha='center',
        fontproperties=_chart_font(16,bold=True),color=C['accent'])
    ax.text(0.5,1.02,
        f"Tong: ${total_val:,.2f}  |  Von: ${total_inv:,.2f}  |  Lai/Lo: ${total_pnl:+,.2f} ({total_pct:+.2f}%)",
        transform=ax.transAxes,ha='center',fontproperties=_chart_font(10),color=pnl_color,style='italic')
    if total_inv>0:
        bar_ax=fig.add_axes([0.1,0.01,0.8,0.018])
        bar_ax.set_xlim(0,1); bar_ax.set_ylim(0,1); bar_ax.axis('off')
        bar_ax.add_patch(mpatches.Rectangle((0,0),1,1,facecolor=C['bg_header'],edgecolor=C['border'],linewidth=1))
        ratio=min(abs(total_pct)/100,1.0); bclr=C['positive'] if total_pnl>=0 else C['negative']
        x0=0.5 if total_pnl>=0 else 0.5-ratio*0.5
        bar_ax.add_patch(mpatches.Rectangle((x0,0),ratio*0.5,1,facecolor=bclr,alpha=0.75))
        bar_ax.axvline(0.5,color=C['accent'],linewidth=1.5,alpha=0.8)
    timestamp=datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    ax.text(0.99,-0.04,f"Cap nhat: {timestamp}",transform=ax.transAxes,ha='right',
        fontproperties=_chart_font(8),color=C['text_dim'],style='italic')
    plt.subplots_adjust(top=0.88,bottom=0.06,left=0.02,right=0.98)
    fd,path=tempfile.mkstemp(prefix="table_",suffix=".png"); os.close(fd)
    plt.savefig(path,dpi=180,bbox_inches='tight',facecolor=C['bg_dark'],edgecolor='none')
    plt.close(fig)
    return path
# ===================== FINANCE CHARTS =====================
def get_period_dates(period_choice: str):
    today = datetime.datetime.now()
    if period_choice == "week":
        start = (today - datetime.timedelta(days=today.weekday())).replace(hour=0,minute=0,second=0,microsecond=0)
        end = start + datetime.timedelta(days=6,hours=23,minutes=59,seconds=59)
        suffix = f"tuần này ({start.strftime('%d/%m')} - {end.strftime('%d/%m')})"
    elif period_choice == "month":
        start = today.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
        end = ((start.replace(day=28)+datetime.timedelta(days=4)) - datetime.timedelta(days=1)).replace(hour=23,minute=59,second=59)
        suffix = f"tháng này ({today.strftime('%m/%Y')})"
    elif period_choice == "year":
        start = today.replace(month=1,day=1,hour=0,minute=0,second=0,microsecond=0)
        end = today.replace(month=12,day=31,hour=23,minute=59,second=59)
        suffix = f"năm nay ({today.year})"
    elif period_choice == "all":
        start = end = None; suffix = "tất cả thời gian"
    else:
        return None, None, None
    return start, end, suffix

def gen_finance_charts(user_id: int, period_choice: str) -> list:
    """Return list of (BytesIO, caption) tuples for all generated charts."""
    start_date, end_date, title_suffix = get_period_dates(period_choice)
    charts = []

    # 1. Donut chi tiêu
    expenses_data = db_list_expenses_grouped(user_id, start_date, end_date)
    if expenses_data:
        labels = [r[0] for r in expenses_data]; sizes = [r[1] for r in expenses_data]
        if sum(sizes) > 0:
            fig, ax = plt.subplots(figsize=(8,8))
            colors = ['#FF7A7A','#3498DB','#F1C40F','#27AE60','#E74C3C','#689F38','#F39C12','#2980B9','#9B59B6','#1ABC9C']
            wedges,_,autotexts = ax.pie(sizes, colors=colors[:len(sizes)], startangle=90,
                counterclock=False, wedgeprops={'width':0.4,'edgecolor':'white','linewidth':2},
                autopct="%1.1f%%", pctdistance=0.85)
            for at in autotexts: at.set_color('black'); at.set_fontsize(14); at.set_fontweight('bold')
            plt.gca().add_artist(plt.Circle((0,0),0.6,fc='white'))
            total = sum(sizes)
            legend_labels = [f'{lb} ({sz/total*100:.1f}%)' for lb,sz in zip(labels,sizes)]
            ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1,0.5), fontsize=10)
            plt.title(f"Phân bổ Chi tiêu ({title_suffix})", fontsize=14, fontweight='bold', pad=15)
            buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='white')
            buf.seek(0); plt.close(fig)
            cap = f"🍩 Chi tiêu {title_suffix}\n💸 Tổng: {total:,.0f} VND"
            charts.append((buf, cap))

    # 2. Cột thu vs chi
    expenses_m, incomes_m = db_get_monthly_report(user_id, start_date, end_date)
    if expenses_m or incomes_m:
        all_months = sorted(set([e[0] for e in expenses_m]+[i[0] for i in incomes_m]))
        exp_dict = {m: a for m,a in expenses_m}; inc_dict = {m: a for m,a in incomes_m}
        exp_vals = [exp_dict.get(m,0) for m in all_months]
        inc_vals = [inc_dict.get(m,0) for m in all_months]
        x = np.arange(len(all_months))
        fig, ax = plt.subplots(figsize=(max(8,len(all_months)*1.2+2), 6))
        bars_inc = ax.bar(x-0.2, inc_vals, 0.4, label='Thu nhập', color='#2E8B57', alpha=0.8, edgecolor='white')
        bars_exp = ax.bar(x+0.2, exp_vals, 0.4, label='Chi tiêu', color='#DC143C', alpha=0.8, edgecolor='white')
        ax.set_xticks(x); ax.set_xticklabels(all_months, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel("Số tiền (VND)"); ax.set_title(f"Thu Chi ({title_suffix})", fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3); ax.legend(loc='upper left')
        for bar in bars_inc:
            h = bar.get_height()
            if h > 0: ax.text(bar.get_x()+bar.get_width()/2, h*1.01, f'{int(h):,}', ha='center', va='bottom', fontsize=8, color='#2E8B57', fontweight='bold')
        for bar in bars_exp:
            h = bar.get_height()
            if h > 0: ax.text(bar.get_x()+bar.get_width()/2, h*1.01, f'{int(h):,}', ha='center', va='bottom', fontsize=8, color='#DC143C', fontweight='bold')
        ti = sum(inc_vals); te = sum(exp_vals); nb = ti-te
        bbox_c = '#E8F5E8' if nb>=0 else '#FFE8E8'; tc = '#2E8B57' if nb>=0 else '#DC143C'
        ax.text(0.98,0.98,f"Tổng thu: {ti:,}\nTổng chi: {te:,}\nCân đối: {nb:,}",
            transform=ax.transAxes, va='top', ha='right', fontsize=9,
            bbox=dict(boxstyle='round,pad=0.4',facecolor=bbox_c,alpha=0.8),color=tc,fontweight='bold')
        plt.tight_layout()
        buf = io.BytesIO(); plt.savefig(buf,format='png',bbox_inches='tight',dpi=150,facecolor='white')
        buf.seek(0); plt.close(fig)
        cap = f"📊 Thu chi {title_suffix}\n💰 Thu: {ti:,.0f}  💸 Chi: {te:,.0f}  {'✅' if nb>=0 else '⚠️'} Cân đối: {nb:,.0f}"
        charts.append((buf, cap))

    # 3. Heatmap (week/month/year)
    if period_choice in ("week","month","year"):
        conn = db_conn(); cur = conn.cursor()
        today_d = datetime.date.today()
        if period_choice == "week":
            sd = today_d - datetime.timedelta(days=today_d.weekday())
            ed = sd + datetime.timedelta(days=6)
            grp = "strftime('%Y-%m-%d',created_at)"; x_label = "day"
            htitle = "Heatmap Chi Tiêu Theo Ngày (Tuần này)"
        elif period_choice == "month":
            sd = today_d.replace(day=1)
            nm = (sd.replace(day=28)+datetime.timedelta(days=4)).replace(day=1)
            ed = nm - datetime.timedelta(days=1)
            grp = "strftime('%Y-%m-%d',created_at)"; x_label = "day"
            htitle = "Heatmap Chi Tiêu Theo Ngày (Tháng này)"
        else:
            sd = today_d.replace(month=1,day=1); ed = today_d.replace(month=12,day=31)
            grp = "strftime('%Y-%m',created_at)"; x_label = "month"
            htitle = "Heatmap Chi Tiêu Theo Tháng (Năm nay)"
        end_incl = ed + datetime.timedelta(days=1)
        cur.execute(f"SELECT {grp},category,SUM(amount) FROM expenses WHERE user_id=? AND created_at>=? AND created_at<? GROUP BY 1,2 ORDER BY 1",
                    (user_id, sd.isoformat(), end_incl.isoformat()))
        rows = cur.fetchall(); conn.close()
        if rows:
            if x_label == "day":
                x_vals = []; d = sd
                while d <= ed: x_vals.append(d.isoformat()); d += datetime.timedelta(days=1)
            else:
                x_vals = []; y,m = sd.year,sd.month
                while (y<ed.year) or (y==ed.year and m<=ed.month):
                    x_vals.append(f"{y:04d}-{m:02d}"); m+=1
                    if m>12: m=1; y+=1
            cats = sorted({r[1] for r in rows})
            dmap = {(x,c):0 for x in x_vals for c in cats}
            for x,c,v in rows:
                if x in x_vals: dmap[(x,c)]=v
            heat = np.array([[dmap[(x,c)] for c in cats] for x in x_vals],dtype=float)
            cmap = mcolors.LinearSegmentedColormap.from_list('heat',['#f0f0f0','#ffcc66','#ff3300'])
            norm = mcolors.Normalize(vmin=0,vmax=heat.max() if heat.size else 1)
            fig,ax = plt.subplots(figsize=(max(8,len(cats)*1.2+2),max(4,len(x_vals)*0.4+2)))
            im = ax.imshow(heat,aspect='auto',cmap=cmap,norm=norm)
            plt.colorbar(im,ax=ax,label='Số tiền (VND)')
            ax.set_xticks(np.arange(len(cats))); ax.set_xticklabels(cats,rotation=45,ha='right',fontsize=9)
            ax.set_yticks(np.arange(len(x_vals))); ax.set_yticklabels(x_vals,fontsize=8)
            ax.set_title(htitle,fontsize=13,fontweight='bold',pad=10)
            maxv = heat.max() if heat.size else 0
            for i in range(len(x_vals)):
                for j in range(len(cats)):
                    val=heat[i,j]
                    if val>0:
                        tc='white' if maxv>0 and val>0.6*maxv else 'black'
                        ax.text(j,i,f"{int(val):,}",ha='center',va='center',fontsize=7,color=tc)
            plt.tight_layout()
            buf=io.BytesIO(); plt.savefig(buf,format='png',bbox_inches='tight',dpi=150,facecolor='white')
            buf.seek(0); plt.close(fig)
            charts.append((buf,f"🔥 {htitle}"))
    return charts

# ===================== HTML DASHBOARD =====================
def _make_html(user_id: Optional[int] = None) -> str:
    crypto_rows = ""
    finance_html = ""
    crypto_total = 0.0
    if user_id:
        try:
            positions = db_crypto_positions(user_id)
            cg_ids = [p["cg_id"] for p in positions if p["cg_id"]]
            prices = cg_simple_price_usd(cg_ids) if cg_ids else {}
            for p in positions:
                sym=p["symbol"]; qty=float(p["qty"]); inv=float(p["invested_usd"])
                cg=p["cg_id"] or ""; price=float(prices.get(cg,0))
                val=qty*price; pnl=val-inv; pct=(pnl/inv*100) if inv>0 else 0
                crypto_total+=val
                color="#00ff88" if pnl>=0 else "#ff4757"
                crypto_rows+=f"<tr><td>{sym}</td><td>{qty:g}</td><td>${price:,.2f}</td><td>${val:,.2f}</td><td>${inv:,.2f}</td><td style='color:{color}'>${pnl:+,.2f} ({pct:+.1f}%)</td></tr>"
        except Exception as e:
            crypto_rows = f"<tr><td colspan='6'>Lỗi: {e}</td></tr>"
        try:
            income, expense, balance = db_get_combined_summary(user_id)
            bal_color="#00ff88" if balance>=0 else "#ff4757"
            finance_html = f"""
            <div class="card">
              <h2>💵 Tài Chính Cá Nhân</h2>
              <div class="stats">
                <div class="stat green">📈 Thu nhập<br><b>{income:,.0f} đ</b></div>
                <div class="stat red">📉 Chi tiêu<br><b>{expense:,.0f} đ</b></div>
                <div class="stat" style="color:{bal_color}">💰 Số dư<br><b>{balance:,.0f} đ</b></div>
              </div>
            </div>"""
        except Exception as e:
            finance_html = f"<div class='card'><p>Lỗi finance: {e}</p></div>"
    ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    uid_note = f"User ID: {user_id}" if user_id else "Thêm ?user_id=ID vào URL để xem dữ liệu"
    return f"""<!DOCTYPE html><html lang="vi"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Univer Bot Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0e27;color:#e8e8e8;font-family:'Segoe UI',sans-serif;padding:20px}}
h1{{color:#00d4ff;text-align:center;margin-bottom:8px;font-size:1.8em}}
.subtitle{{text-align:center;color:#94a3b8;margin-bottom:24px;font-size:.9em}}
.card{{background:#151932;border-radius:12px;padding:20px;margin-bottom:20px;border:1px solid #2a2a3e}}
.card h2{{color:#00d4ff;margin-bottom:16px;font-size:1.2em}}
table{{width:100%;border-collapse:collapse;font-size:.9em}}
th{{background:#16213e;color:#00d4ff;padding:10px 8px;text-align:left}}
td{{padding:8px;border-bottom:1px solid #2a2a3e}}
tr:hover td{{background:#1e2a4a}}
.stats{{display:flex;gap:16px;flex-wrap:wrap}}
.stat{{flex:1;min-width:120px;background:#0f3460;border-radius:8px;padding:14px;text-align:center;font-size:.95em}}
.stat.green{{color:#00ff88}}.stat.red{{color:#ff4757}}
.total{{color:#00d4ff;font-weight:bold;margin-top:12px;font-size:1em}}
footer{{text-align:center;color:#535c68;margin-top:20px;font-size:.8em}}
</style></head><body>
<h1>🤖 Univer Bot Dashboard</h1>
<div class="subtitle">{uid_note} · Cập nhật: {ts}</div>
<div class="card">
  <h2>🪙 Danh Mục Crypto</h2>
  <table><thead><tr><th>Token</th><th>Số lượng</th><th>Giá</th><th>Giá trị</th><th>Vốn</th><th>Lãi/Lỗ</th></tr></thead>
  <tbody>{crypto_rows if crypto_rows else '<tr><td colspan="6" style="color:#94a3b8">Chưa có dữ liệu</td></tr>'}</tbody></table>
  <p class="total">Tổng: ${crypto_total:,.2f} USD</p>
</div>
{finance_html}
<footer>Univer All-in-One Bot · Port {HTML_PORT}</footer>
</body></html>"""

class _DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path); qs = parse_qs(parsed.query)
        uid = None
        try: uid = int(qs["user_id"][0])
        except Exception: pass
        html = _make_html(uid).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(html)))
        self.end_headers(); self.wfile.write(html)
    def log_message(self, *a): pass

def start_html_server():
    server = HTTPServer(("0.0.0.0", HTML_PORT), _DashboardHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    logger.info(f"HTML dashboard running on port {HTML_PORT}")
    return server

# ===================== KEYBOARDS =====================
# ─── Home ───────────────────────────────────────────────────────────────
BTN_HOME_CRYPTO  = "📈 Crypto"
BTN_HOME_FINANCE = "💰 Thu Chi"
BTN_BACK         = "🔙 Trang Chủ"

# ─── Crypto submenu ─────────────────────────────────────────────────────
BTN_PORTFOLIO = "📊 Danh Mục"
BTN_BUY       = "➕ Mua"
BTN_SELL      = "➖ Bán"
BTN_MAP       = "🔗 Map Token"
BTN_CIMPORT   = "⬇️ Nhập"
BTN_CEXPORT   = "⬆️ Xuất"

# ─── Finance submenu ────────────────────────────────────────────────────
BTN_FADD    = "💵 Thêm"
BTN_FDEL    = "🗑️ Xóa"
BTN_BUDGET  = "🎯 Ngân Sách"
BTN_FIMPORT = "⬇️ Nhập File"
BTN_FEXPORT = "⬆️ Xuất File"

# ─── Shared (route by user_data['submenu']) ──────────────────────────────
BTN_CHART  = "📈 Biểu Đồ"
BTN_REPORT = "📋 Báo Cáo"

ALL_MENU_BTNS = {
    BTN_HOME_CRYPTO, BTN_HOME_FINANCE, BTN_BACK,
    BTN_PORTFOLIO, BTN_BUY, BTN_SELL, BTN_MAP, BTN_CIMPORT, BTN_CEXPORT,
    BTN_FADD, BTN_FDEL, BTN_BUDGET, BTN_FIMPORT, BTN_FEXPORT,
    BTN_CHART, BTN_REPORT,
}

def home_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        [KeyboardButton(BTN_HOME_CRYPTO)],
        [KeyboardButton(BTN_HOME_FINANCE)],
    ], resize_keyboard=True)

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return home_keyboard()

def crypto_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        [KeyboardButton(BTN_PORTFOLIO), KeyboardButton(BTN_BUY)],
        [KeyboardButton(BTN_SELL),      KeyboardButton(BTN_CHART)],
        [KeyboardButton(BTN_REPORT),    KeyboardButton(BTN_MAP)],
        [KeyboardButton(BTN_CIMPORT),   KeyboardButton(BTN_CEXPORT)],
        [KeyboardButton(BTN_BACK)],
    ], resize_keyboard=True)

def finance_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        [KeyboardButton(BTN_FADD),    KeyboardButton(BTN_FDEL)],
        [KeyboardButton(BTN_BUDGET)],
        [KeyboardButton(BTN_REPORT),  KeyboardButton(BTN_CHART)],
        [KeyboardButton(BTN_FIMPORT), KeyboardButton(BTN_FEXPORT)],
        [KeyboardButton(BTN_BACK)],
    ], resize_keyboard=True)

def _submenu_keyboard(user_data: dict) -> ReplyKeyboardMarkup:
    submenu = user_data.get('submenu')
    if submenu == 'finance': return finance_menu_keyboard()
    if submenu == 'crypto':  return crypto_menu_keyboard()
    return home_keyboard()

def _clear_keep_submenu(user_data: dict) -> None:
    submenu = user_data.get('submenu')
    user_data.clear()
    if submenu: user_data['submenu'] = submenu


# ===================== CRYPTO HELPERS =====================
def _build_positions_and_prices(user_id: int):
    positions = db_crypto_positions(user_id)
    ids = [p["cg_id"] or cg_guess_id_from_symbol(p["symbol"]) for p in positions if (p["cg_id"] or cg_guess_id_from_symbol(p["symbol"]))]
    return positions, cg_simple_price_usd(ids)

def _parse_price(s: str) -> Optional[float]:
    s = s.lower().replace(',','').strip()
    try:
        if s.endswith('k'): return float(s[:-1])*1_000
        if s.endswith('m'): return float(s[:-1])*1_000_000
        if s.endswith('b'): return float(s[:-1])*1_000_000_000
        return float(s)
    except Exception: return None

def _parse_natural_trade(text: str, user_id: int = 0):
    text = text.strip()
    side = None
    for kw in ['bán','ban','sell']:
        if text.lower().startswith(kw): side='SELL'; text=text[len(kw):].strip(); break
    if side is None:
        for kw in ['mua','buy']:
            if text.lower().startswith(kw): side='BUY'; text=text[len(kw):].strip(); break
    if side is None: return None
    parts = text.split()
    if not parts: return None
    symbol = parts[0].upper(); text = ' '.join(parts[1:]).strip()
    text = re.sub(r'\b(gia|giá|price|@)\b',' ',text,flags=re.IGNORECASE).strip()
    text = re.sub(r'\s+',' ',text)
    parts = text.split()
    if len(parts) < 2: return None
    qty_raw = parts[0].lower(); price_raw = parts[1]
    note = ' '.join(parts[2:]).strip() if len(parts)>2 else ''
    qty = None
    if qty_raw in ('tất cả','tat ca','hết','het','all','toàn bộ','toan bo'):
        if side=='SELL' and user_id: qty = _get_held_qty(user_id,symbol)
        else: return None
    elif re.fullmatch(r'[\d.,]+\s*%',qty_raw) or re.fullmatch(r'[\d.,]+pct',qty_raw):
        pct_val = float(re.sub(r'[%pct]','',qty_raw).replace(',',''))
        if side=='SELL' and user_id: qty = _get_held_qty(user_id,symbol)*pct_val/100
        else: return None
    else: qty = _parse_price(qty_raw)
    if qty is None or qty<=0: return None
    price = _parse_price(price_raw)
    if price is None or price<=0: return None
    return side, symbol, qty, price, note

async def _execute_trade(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         side: str, symbol: str, qty: float, price: float, note: str):
    user_id = update.effective_user.id
    if side=='SELL':
        held = _get_held_qty(user_id,symbol)
        if qty > held+1e-9:
            await update.message.reply_text(f"⚠️ Bạn chỉ đang giữ {held:g} {symbol}, không thể bán {qty:g}.")
            return
    cg_id = db_crypto_get_map(symbol) or cg_guess_id_from_symbol(symbol)
    if cg_id: db_crypto_upsert_map(symbol,cg_id)
    db_crypto_add_trade(user_id,symbol,side,qty,price,note=note,cg_id=cg_id)
    action="MUA" if side=='BUY' else "BAN"
    msg=f"✅ {action} {symbol}: {qty:g} @ ${price:,.4g} = ${qty*price:,.2f} USD"
    if note: msg+=f"\nGhi chú: {note}"
    await update.message.reply_text(msg)

async def send_portfolio_images(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    positions, prices = _build_positions_and_prices(user_id)
    if not positions:
        await context.bot.send_message(chat_id,"Danh mục trống. Dùng ➕ Mua để thêm giao dịch.")
        return
    theme = db_get_theme(user_id)
    donut = table = None
    try:
        donut = await asyncio.to_thread(gen_portfolio_donut_image,positions,prices,theme)
        table = await asyncio.to_thread(gen_portfolio_table_image,positions,prices,theme)
        with open(donut,"rb") as f1: await context.bot.send_photo(chat_id,f1)
        with open(table,"rb") as f2: await context.bot.send_photo(chat_id,f2,caption="📋 Danh mục")
        if user_id==OWNER_USER_ID:
            try:
                with open(donut,"rb") as fc:
                    await context.bot.send_photo(CHANNEL_CHAT_ID,fc,
                        caption=f"📊 Phân bổ danh mục — {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
            except Exception as ce:
                await context.bot.send_message(chat_id,f"⚠️ Không gửi được lên channel: {ce!r}")
    except Exception as e:
        await context.bot.send_message(chat_id,f"⚠️ Lỗi khi tạo ảnh: {e!r}")
    finally:
        for fp in (donut,table):
            try:
                if fp and os.path.exists(fp): os.remove(fp)
            except Exception: pass

# ===================== CRYPTO IMPORT/EXPORT =====================
def _normalize_datetime_str(val) -> Optional[str]:
    if val is None: return None
    try:
        if hasattr(val,"year") and hasattr(val,"month"): return val.strftime("%Y-%m-%d %H:%M:%S")
    except Exception: pass
    s = str(val).strip()
    if not s: return None
    for f in ["%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%d","%d/%m/%Y %H:%M","%d/%m/%Y"]:
        try: return datetime.datetime.strptime(s,f).strftime("%Y-%m-%d %H:%M:%S")
        except Exception: continue
    try: return datetime.datetime.fromisoformat(s).strftime("%Y-%m-%d %H:%M:%S")
    except Exception: pass
    raise ValueError(f"Invalid datetime: {s}")

def _parse_trades_from_excel(bio) -> list:
    if load_workbook is None:
        raise RuntimeError("Excel import requires openpyxl: pip install openpyxl")
    bio.seek(0)
    wb = load_workbook(filename=bio,read_only=True,data_only=True)
    ws = wb["Trades"] if "Trades" in wb.sheetnames else wb.active
    header_cells = next(ws.iter_rows(min_row=1,max_row=1,values_only=False))
    headers = [c.value.strip() if isinstance(c.value,str) else (c.value or "") for c in header_cells]
    norm = {str(h).strip().lower():i for i,h in enumerate(headers) if str(h).strip()}
    def gv(rv,*names):
        for n in names:
            k=n.lower()
            if k in norm and norm[k]<len(rv): return rv[norm[k]]
        return None
    rows = []
    for r in ws.iter_rows(min_row=2,values_only=True):
        if r is None or all((v is None or (isinstance(v,str) and not v.strip())) for v in r): continue
        rows.append({"date":gv(r,"date","created_at"),"exchange":gv(r,"exchange"),"symbol":gv(r,"symbol","asset","token"),
                     "pair":gv(r,"pair"),"side":gv(r,"side","action"),"quantity":gv(r,"quantity","qty","amount"),
                     "price":gv(r,"price","price_usd"),"fee":gv(r,"fee","fee_usd"),
                     "fee_currency":gv(r,"feecurrency","fee_currency"),"note":gv(r,"note","memo","comment"),
                     "created_at":gv(r,"created_at")})
    if not rows: raise ValueError(f"No data rows. Headers: {list(norm.keys())}")
    return rows

async def cp_import_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_rate(update): return
    doc = None
    if update.message and update.message.document: doc = update.message.document
    if not doc and update.message and update.message.reply_to_message and update.message.reply_to_message.document:
        doc = update.message.reply_to_message.document
    if not doc:
        await update.message.reply_text("Gửi file CSV hoặc Excel rồi reply `/cp_import`.",parse_mode="Markdown"); return
    await update.message.reply_text("📥 Đang xử lý file...")
    fobj = await context.bot.get_file(doc.file_id)
    bio = io.BytesIO(); await fobj.download_to_memory(out=bio); bio.seek(0)
    filename=(doc.file_name or "").lower(); mime=(doc.mime_type or "").lower()
    ok=fail=0; user=update.effective_user
    try:
        if filename.endswith((".xlsx",".xlsm")) or "spreadsheetml" in mime:
            for row in _parse_trades_from_excel(bio):
                try:
                    sym=(row.get("symbol") or "").strip().upper()
                    side=(row.get("side") or "").strip().upper()
                    qty=float(row.get("quantity") or 0); price=float(row.get("price") or 0)
                    fee=float(row.get("fee") or 0) if str(row.get("fee") or "").strip() else 0.0
                    note=(row.get("note") or "").strip()
                    at_raw=row.get("created_at"); created_at=None
                    if at_raw not in (None,""):
                        try: created_at=datetime.datetime.fromisoformat(_normalize_datetime_str(at_raw))
                        except Exception: pass
                    cg_id=db_crypto_get_map(sym) or cg_guess_id_from_symbol(sym)
                    if cg_id: db_crypto_upsert_map(sym,cg_id)
                    if not sym or side not in ("BUY","SELL") or qty<=0 or price<=0: fail+=1; continue
                    db_crypto_add_trade(user.id,sym,side,qty,price,note=note,cg_id=cg_id,fee_usd=fee,created_at=created_at)
                    ok+=1
                except Exception: fail+=1
        else:
            for row in csv.DictReader(io.TextIOWrapper(bio,encoding="utf-8")):
                try:
                    sym=(row.get("symbol") or row.get("Symbol") or "").strip().upper()
                    side=(row.get("side") or row.get("Side") or "").strip().upper()
                    qty=float(row.get("qty") or row.get("quantity") or row.get("Quantity") or 0)
                    price=float(row.get("price") or row.get("price_usd") or row.get("Price") or 0)
                    fee=float(row.get("fee") or row.get("Fee") or 0) if str(row.get("fee") or row.get("Fee") or "").strip() else 0.0
                    note=(row.get("note") or row.get("Note") or "").strip()
                    cg_id=(row.get("cg_id") or row.get("CG_ID") or "").strip() or None
                    at_raw=(row.get("created_at") or row.get("CreatedAt") or "").strip()
                    if not sym or side not in ("BUY","SELL") or qty<=0 or price<=0: fail+=1; continue
                    created_at=None
                    if at_raw:
                        try: created_at=datetime.datetime.fromisoformat(at_raw)
                        except Exception: pass
                    if not cg_id: cg_id=db_crypto_get_map(sym) or cg_guess_id_from_symbol(sym)
                    if cg_id: db_crypto_upsert_map(sym,cg_id)
                    db_crypto_add_trade(user.id,sym,side,qty,price,note=note,cg_id=cg_id,fee_usd=fee,created_at=created_at)
                    ok+=1
                except Exception: fail+=1
    except RuntimeError as e:
        await update.message.reply_text(f"❌ {e}"); return
    await update.message.reply_text(f"✅ Đã nhập {ok} giao dịch, lỗi {fail}.")

# ===================== CRYPTO COMMAND HANDLERS =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_migrated()
    await update.message.reply_text(
        "👋 Chào mừng! Bot quản lý *Crypto* + *Thu Chi* tài chính.\n"
        "Dùng bàn phím bên dưới hoặc gõ /help để xem hướng dẫn.",
        parse_mode="Markdown", reply_markup=main_menu_keyboard())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *HƯỚNG DẪN NHANH*\n\n"
        "*📈 CRYPTO* (bấm 📈 Crypto)\n"
        "• 📊 Danh Mục → xem portfolio\n"
        "• ➕ Mua / ➖ Bán → hướng dẫn lệnh\n"
        "• 📈 Biểu Đồ → biểu đồ portfolio\n"
        "• 📋 Báo Cáo → tóm tắt portfolio\n"
        "• `mua BTC 0.01 giá 70k` → ghi ngay\n"
        "• `/cp_add SYMBOL SL GIA [note]`\n"
        "• `/cp_sell SYMBOL SL GIA [note]`\n\n"
        "*💰 THU CHI* (bấm 💰 Thu Chi)\n"
        "• 💵 Thêm → thêm thu/chi\n"
        "• 🗑️ Xóa → xóa giao dịch\n"
        "• 📋 Báo Cáo → báo cáo kỳ\n"
        "• 📈 Biểu Đồ → biểu đồ thu chi\n"
        "• 🎯 Ngân Sách → đặt/xem ngân sách\n"
        "• Nhập nhanh: `20k ăn sáng` hoặc `+500k lương`\n\n"
        "*🌐 HTML Dashboard*\n"
        f"• Truy cập: `http://IP:{HTML_PORT}?user_id=YOUR_ID`"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=_submenu_keyboard(context.user_data))

async def cp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_rate(update): return
    await send_portfolio_images(update.effective_chat.id,update.effective_user.id,context)

async def cp_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_rate(update): return
    ensure_migrated()
    args = context.args
    if len(args)<3:
        await update.message.reply_text("Cú pháp: /cp_add SYMBOL SL GIA [note]\nVD: /cp_add BTC 0.01 70000"); return
    symbol=args[0].upper()
    try: qty=float(args[1]); price=float(args[2])
    except Exception: await update.message.reply_text("Số lượng & giá không hợp lệ."); return
    note=" ".join(args[3:]).strip() if len(args)>3 else ""
    if qty<=0 or price<=0: await update.message.reply_text("Số lượng & giá phải > 0"); return
    await _execute_trade(update,context,'BUY',symbol,qty,price,note)

async def cp_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_rate(update): return
    ensure_migrated()
    args = context.args
    if len(args)<3:
        await update.message.reply_text("Cú pháp: /cp_sell SYMBOL SL GIA [note]\nVD: /cp_sell SOL 10 87"); return
    symbol=args[0].upper()
    try: qty=float(args[1]); price=float(args[2])
    except Exception: await update.message.reply_text("Số lượng & giá không hợp lệ."); return
    note=" ".join(args[3:]).strip() if len(args)>3 else ""
    if qty<=0 or price<=0: await update.message.reply_text("Số lượng & giá phải > 0"); return
    await _execute_trade(update,context,'SELL',symbol,qty,price,note)

async def cp_map_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_rate(update): return
    args = context.args
    if len(args)<2: await update.message.reply_text("Cú pháp: /cp_map SYMBOL CG_ID"); return
    symbol,cg_id = args[0].upper(),args[1]
    db_crypto_upsert_map(symbol,cg_id)
    await update.message.reply_text(f"✅ Đã map {symbol} → {cg_id}")

async def theme_select_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    theme_key = q.data.split(":")[1]
    if theme_key not in THEMES: await q.edit_message_text("❌ Theme không hợp lệ."); return
    db_set_theme(q.from_user.id,theme_key)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(
        f"{'✅ ' if k==theme_key else ''}{v['name']}",callback_data=f"SET_THEME:{k}")
        for k,v in THEMES.items()]])
    await q.edit_message_text(f"✅ Theme: {THEMES[theme_key]['name']}. Bấm 📋 Danh mục để thấy kết quả.",reply_markup=kb)

async def handle_crypto_menu_btns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_rate(update): return
    text=(update.message.text or "").strip(); user_id=update.effective_user.id
    if text==BTN_PORTFOLIO:
        try: await send_portfolio_images(update.effective_chat.id,user_id,context)
        except Exception as e: await update.message.reply_text(f"Chưa có dữ liệu.\nLỗi: {e}")
    elif text==BTN_BUY:
        await update.message.reply_text("➕ *MUA*: `/cp_add SYMBOL SL GIA [note]`\nVD: `/cp_add BTC 0.01 70000`\nHoặc gõ: `mua BTC 0.01 giá 70k`",parse_mode="Markdown")
    elif text==BTN_SELL:
        await update.message.reply_text("➖ *BÁN*: `/cp_sell SYMBOL SL GIA [note]`\nVD: `/cp_sell SOL 10 87`\nHoặc gõ: `bán SOL tất cả giá 100`",parse_mode="Markdown")
    elif text==BTN_MAP:
        await update.message.reply_text("🔗 *MAP TOKEN*: `/cp_map SYMBOL CG_ID`\nVD: `/cp_map ATOM cosmos`",parse_mode="Markdown")
    elif text==BTN_CIMPORT:
        tmp_fd,tmp=tempfile.mkstemp(prefix="crypto_tpl_",suffix=".csv"); os.close(tmp_fd)
        with open(tmp,"w",newline="",encoding="utf-8") as tf:
            tw=csv.writer(tf)
            tw.writerow(["symbol","cg_id","side","qty","price_usd","fee_usd","note","created_at"])
            tw.writerow(["ATOM","cosmos","BUY","1","10.0","0","","2025-01-01 12:00:00"])
            tw.writerow(["BTC","bitcoin","BUY","0.01","50000","2.5","spot","2025-02-01 20:30:00"])
        try:
            with open(tmp,"rb") as f:
                await update.message.reply_document(f,filename="crypto_import_template.csv",caption="📄 File mẫu. Điền rồi gửi lại + reply `/cp_import`.")
        finally:
            try: os.remove(tmp)
            except Exception: pass
    elif text==BTN_CEXPORT:
        rows=db_crypto_all_trades(user_id)
        if not rows: await update.message.reply_text("Chưa có giao dịch để xuất."); return
        fd,path=tempfile.mkstemp(prefix="portfolio_",suffix=".csv"); os.close(fd)
        with open(path,"w",newline="",encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(["symbol","cg_id","side","qty","price_usd","fee_usd","note","created_at"])
            for r in rows: w.writerow(r)
        try:
            with open(path,"rb") as f: await update.message.reply_document(f,filename="crypto_portfolio.csv",caption="✅ Đã xuất.")
        finally:
            try: os.remove(path)
            except Exception: pass

# ===================== 2-LEVEL MENU NAVIGATION =====================
async def handle_home_crypto_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['submenu'] = 'crypto'
    await update.message.reply_text("📈 *Crypto*:", parse_mode="Markdown", reply_markup=crypto_menu_keyboard())

async def handle_home_finance_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['submenu'] = 'finance'
    await update.message.reply_text("💰 *Thu Chi*:", parse_mode="Markdown", reply_markup=finance_menu_keyboard())

async def handle_back_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('submenu', None)
    await update.message.reply_text("Menu chính:", reply_markup=home_keyboard())

async def handle_budget_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Đặt ngân sách", callback_data="budget_menu_set")],
        [InlineKeyboardButton("📋 Xem ngân sách",  callback_data="budget_menu_view")],
        [InlineKeyboardButton("❌ Hủy",            callback_data="cancel_action")],
    ])
    await update.message.reply_text("🎯 *Ngân Sách*:", parse_mode="Markdown", reply_markup=kb)

async def handle_budget_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.data == "budget_menu_set":
        await q.edit_message_text(
            "📝 Dùng lệnh:\n`/ngansach <Danh mục> <Số tiền>`\nVD: `/ngansach Ăn uống 3000000`",
            parse_mode="Markdown")
    elif q.data == "budget_menu_view":
        budgets = db_get_budgets(q.from_user.id)
        if not budgets:
            await q.edit_message_text("Chưa có ngân sách nào. Dùng /ngansach để đặt.")
            return
        lines = ["🎯 *Ngân Sách Hiện Tại:*"]
        for cat, amt in budgets.items():
            lines.append(f"• {cat}: `{amt:,.0f} đ`")
        await q.edit_message_text("\n".join(lines), parse_mode="Markdown")

async def handle_shared_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes 📈 Biểu Đồ and 📋 Báo Cáo based on user_data['submenu']."""
    submenu = context.user_data.get('submenu', 'finance')
    text = (update.message.text or "").strip()
    if submenu == 'crypto':
        if text == BTN_CHART:
            try: await send_portfolio_images(update.effective_chat.id, update.effective_user.id, context)
            except Exception as e: await update.message.reply_text(f"Chưa có dữ liệu.\nLỗi: {e}")
        elif text == BTN_REPORT:
            await cp_cmd(update, context)
    else:
        if text == BTN_CHART:
            await chart_start(update, context)
        elif text == BTN_REPORT:
            await report_start(update, context)

# ===================== FINANCE CONVERSATION STATES =====================
CHOOSING_INCOME_AMOUNT, CHOOSING_INCOME_NOTE, CHOOSING_INCOME_DATE, CHOOSING_INCOME_SOURCE, CONFIRM_INCOME_AMOUNT = range(5)
CHOOSING_EXPENSE_AMOUNT, CHOOSING_EXPENSE_NOTE, CHOOSING_EXPENSE_DATE, CHOOSING_EXPENSE_CATEGORY, CONFIRM_EXPENSE_AMOUNT = range(5,10)
CHOOSING_ADD_TYPE = 10
CHOOSING_REPORT_PERIOD = 11
CHOOSING_SUPPLEMENT_TYPE = 12
DELETE_CHOOSING_ACTION = 13
DELETE_INDIVIDUAL_LISTING = 14
DELETE_INDIVIDUAL_CONFIRM = 15
RESET_DATA_CONFIRM_STEP1 = 16
RESET_DATA_CONFIRM_STEP2 = 17
CHOOSING_CHART_PERIOD = 18
EXPORT_CHOOSING_FORMAT = 19
CHOOSING_IMPORT_ACTION = 20
IMPORT_FILE_UPLOADED = 21

# ===================== FINANCE HELPERS =====================
def anonymize_name(name: str) -> str:
    if not name: return "****"
    if len(name)<2: return "*"
    return '*'*(len(name)-1)+name[-1]

async def post_to_channel(context: ContextTypes.DEFAULT_TYPE, message: str):
    try:
        await context.bot.send_message(chat_id=FINANCE_CHANNEL_ID,text=message,parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Không đăng được lên kênh: {e}")

async def send_or_update_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str = "Menu chính:"):
    kbd = _submenu_keyboard(context.user_data)
    if update.callback_query:
        try: await update.callback_query.edit_message_text(message_text,reply_markup=kbd)
        except Exception: await update.callback_query.message.reply_text(message_text,reply_markup=kbd)
    elif update.message:
        await update.message.reply_text(message_text,reply_markup=kbd)

async def end_conv(update: Update, context: ContextTypes.DEFAULT_TYPE, msg: str) -> int:
    _clear_keep_submenu(context.user_data)
    await send_or_update_main_menu(update,context,msg)
    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await end_conv(update,context,'Đã hủy thao tác.')

async def cancel_conversation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await end_conv(update,context,'Đã hủy thao tác.')

# ===================== ADD FINANCE FLOW =====================
async def handle_add_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    _clear_keep_submenu(context.user_data)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Thu nhập (Hôm nay)",callback_data="add_type_income_today")],
        [InlineKeyboardButton("Chi tiêu (Hôm nay)",callback_data="add_type_expense_today")],
        [InlineKeyboardButton("Bổ sung giao dịch",callback_data="add_type_supplement")],
        [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]
    ])
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Bạn muốn thêm loại giao dịch nào?",reply_markup=kb)
    else:
        await update.message.reply_text("Bạn muốn thêm loại giao dịch nào?",reply_markup=kb)
    return CHOOSING_ADD_TYPE

async def choose_add_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer(); choice=q.data
    if choice=="add_type_income_today":
        context.user_data['transaction_type']="income"; context.user_data['created_at']=datetime.datetime.now()
        await q.edit_message_text("Nhập số tiền thu nhập (VD: 5tr, 200k):"); return CHOOSING_INCOME_AMOUNT
    elif choice=="add_type_expense_today":
        context.user_data['transaction_type']="expense"; context.user_data['created_at']=datetime.datetime.now()
        await q.edit_message_text("Nhập số tiền chi tiêu (VD: 5tr2, 100k):"); return CHOOSING_EXPENSE_AMOUNT
    elif choice=="add_type_supplement":
        kb=InlineKeyboardMarkup([[InlineKeyboardButton("Thu nhập",callback_data="supplement_type_income")],
            [InlineKeyboardButton("Chi tiêu",callback_data="supplement_type_expense")],
            [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]])
        await q.edit_message_text("Bổ sung Thu nhập hay Chi tiêu?",reply_markup=kb); return CHOOSING_SUPPLEMENT_TYPE
    return await cancel_conversation_callback(update,context)

async def choose_supplement_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer(); choice=q.data
    context.user_data.pop('created_at',None)
    if choice=="supplement_type_income":
        context.user_data['transaction_type']="income"
        await q.edit_message_text("Nhập số tiền thu nhập:"); return CHOOSING_INCOME_AMOUNT
    elif choice=="supplement_type_expense":
        context.user_data['transaction_type']="expense"
        await q.edit_message_text("Nhập số tiền chi tiêu:"); return CHOOSING_EXPENSE_AMOUNT
    return await cancel_conversation_callback(update,context)

def _income_source_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Lương",callback_data="income_source_Lương"),InlineKeyboardButton("Thưởng",callback_data="income_source_Thưởng")],
        [InlineKeyboardButton("Kinh doanh",callback_data="income_source_Kinh doanh"),InlineKeyboardButton("Được cho",callback_data="income_source_Được cho")],
        [InlineKeyboardButton("Thu hồi nợ",callback_data="income_source_Thu hồi nợ"),InlineKeyboardButton("Bán tài sản",callback_data="income_source_Bán tài sản")],
        [InlineKeyboardButton("Lãi tiết kiệm",callback_data="income_source_Lãi tiết kiệm"),InlineKeyboardButton("Lãi đầu tư",callback_data="income_source_Lãi đầu tư")],
        [InlineKeyboardButton("Khác",callback_data="income_source_Khác")],
        [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]
    ])

def _expense_cat_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Ăn uống",callback_data="expense_category_Ăn uống"),InlineKeyboardButton("Di chuyển",callback_data="expense_category_Di chuyển")],
        [InlineKeyboardButton("Mua sắm",callback_data="expense_category_Mua sắm"),InlineKeyboardButton("Hóa đơn",callback_data="expense_category_Hóa đơn")],
        [InlineKeyboardButton("Gia đình",callback_data="expense_category_Gia đình"),InlineKeyboardButton("Sức khỏe",callback_data="expense_category_Sức khỏe")],
        [InlineKeyboardButton("Giải trí",callback_data="expense_category_Giải trí"),InlineKeyboardButton("Đầu tư",callback_data="expense_category_Đầu tư")],
        [InlineKeyboardButton("Tiết kiệm",callback_data="expense_category_Tiết kiệm"),InlineKeyboardButton("Khác",callback_data="expense_category_Khác")],
        [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]
    ])

async def get_income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount=parse_amount(update.message.text)
        if amount<=0: await update.message.reply_text("Số tiền phải > 0:"); return CHOOSING_INCOME_AMOUNT
        if amount>LARGE_AMOUNT_THRESHOLD:
            context.user_data['amount_to_confirm']=amount
            kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Đúng vậy",callback_data="confirm_amount_yes")],
                [InlineKeyboardButton("❌ Nhập lại",callback_data="confirm_amount_no")],
                [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]])
            await update.message.reply_text(f"Chắc chắn thu {amount:,.0f} đ? (số lớn)",reply_markup=kb)
            return CONFIRM_INCOME_AMOUNT
        context.user_data['amount']=amount
        await update.message.reply_text("Nhập ghi chú cho khoản thu:"); return CHOOSING_INCOME_NOTE
    except Exception: await update.message.reply_text("Không hợp lệ. Thử lại (VD: 5tr, 200k):"); return CHOOSING_INCOME_AMOUNT

async def confirm_income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    if q.data=="confirm_amount_yes":
        context.user_data['amount']=context.user_data.pop('amount_to_confirm')
        await q.edit_message_text("Đã xác nhận. Nhập ghi chú:"); return CHOOSING_INCOME_NOTE
    elif q.data=="confirm_amount_no":
        context.user_data.pop('amount_to_confirm',None)
        await q.edit_message_text("Nhập lại số tiền:"); return CHOOSING_INCOME_AMOUNT
    return await cancel_conversation_callback(update,context)

async def get_income_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['note']=update.message.text
    if 'created_at' in context.user_data:
        await update.message.reply_text("Chọn nguồn thu nhập:",reply_markup=_income_source_kb()); return CHOOSING_INCOME_SOURCE
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("Hôm nay",callback_data="date_today_income")],
        [InlineKeyboardButton("Ngày khác",callback_data="date_other_income")],
        [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]])
    await update.message.reply_text("Giao dịch vào ngày nào?",reply_markup=kb); return CHOOSING_INCOME_DATE

async def choose_income_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    if q.data=="date_today_income":
        context.user_data['created_at']=datetime.datetime.now()
        await q.edit_message_text("Chọn nguồn thu nhập:",reply_markup=_income_source_kb()); return CHOOSING_INCOME_SOURCE
    elif q.data=="date_other_income":
        await q.edit_message_text("Nhập ngày (VD: 25/06/2024 hoặc 15/1):"); return CHOOSING_INCOME_DATE
    return await cancel_conversation_callback(update,context)

async def get_income_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['created_at']=parse_date(update.message.text)
        await update.message.reply_text("Chọn nguồn thu nhập:",reply_markup=_income_source_kb()); return CHOOSING_INCOME_SOURCE
    except ValueError as e:
        await update.message.reply_text(f"{e} Nhập lại ngày:"); return CHOOSING_INCOME_DATE

async def get_income_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    source=q.data.replace("income_source_","")
    user_id=q.from_user.id; user_name=q.from_user.full_name
    amount=context.user_data.get('amount'); note=context.user_data.get('note')
    created_at=context.user_data.get('created_at')
    db_add_income(user_id,amount,source,note,created_at)
    await q.edit_message_text(f"✅ Thu nhập: {amount:,.0f} đ - {source} ({note}) ngày {created_at.strftime('%d/%m/%Y')}")
    await post_to_channel(context,
        f"🔔 *Thu nhập mới*\n💰 `{amount:,.0f} đ`\n📌 {source}\n📝 {note}\n📅 {created_at.strftime('%d/%m/%Y')}\n👤 `{anonymize_name(user_name)}`")
    return await end_conv(update,context,"✅ Thu nhập đã lưu.")

async def get_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount=parse_amount(update.message.text)
        if amount<=0: await update.message.reply_text("Số tiền phải > 0:"); return CHOOSING_EXPENSE_AMOUNT
        if amount>LARGE_AMOUNT_THRESHOLD:
            context.user_data['amount_to_confirm']=amount
            kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Đúng vậy",callback_data="confirm_amount_yes")],
                [InlineKeyboardButton("❌ Nhập lại",callback_data="confirm_amount_no")],
                [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]])
            await update.message.reply_text(f"Chắc chắn chi {amount:,.0f} đ? (số lớn)",reply_markup=kb)
            return CONFIRM_EXPENSE_AMOUNT
        context.user_data['amount']=amount
        await update.message.reply_text("Nhập ghi chú cho khoản chi:"); return CHOOSING_EXPENSE_NOTE
    except Exception: await update.message.reply_text("Không hợp lệ. Thử lại (VD: 5tr2, 100k):"); return CHOOSING_EXPENSE_AMOUNT

async def confirm_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    if q.data=="confirm_amount_yes":
        context.user_data['amount']=context.user_data.pop('amount_to_confirm')
        await q.edit_message_text("Đã xác nhận. Nhập ghi chú:"); return CHOOSING_EXPENSE_NOTE
    elif q.data=="confirm_amount_no":
        context.user_data.pop('amount_to_confirm',None)
        await q.edit_message_text("Nhập lại số tiền:"); return CHOOSING_EXPENSE_AMOUNT
    return await cancel_conversation_callback(update,context)

async def get_expense_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['note']=update.message.text
    if 'created_at' in context.user_data:
        await update.message.reply_text("Chọn danh mục chi tiêu:",reply_markup=_expense_cat_kb()); return CHOOSING_EXPENSE_CATEGORY
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("Hôm nay",callback_data="date_today_expense")],
        [InlineKeyboardButton("Ngày khác",callback_data="date_other_expense")],
        [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]])
    await update.message.reply_text("Giao dịch vào ngày nào?",reply_markup=kb); return CHOOSING_EXPENSE_DATE

async def choose_expense_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    if q.data=="date_today_expense":
        context.user_data['created_at']=datetime.datetime.now()
        await q.edit_message_text("Chọn danh mục chi tiêu:",reply_markup=_expense_cat_kb()); return CHOOSING_EXPENSE_CATEGORY
    elif q.data=="date_other_expense":
        await q.edit_message_text("Nhập ngày (VD: 25/06/2024 hoặc 15/1):"); return CHOOSING_EXPENSE_DATE
    return await cancel_conversation_callback(update,context)

async def get_expense_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['created_at']=parse_date(update.message.text)
        await update.message.reply_text("Chọn danh mục chi tiêu:",reply_markup=_expense_cat_kb()); return CHOOSING_EXPENSE_CATEGORY
    except ValueError as e:
        await update.message.reply_text(f"{e} Nhập lại ngày:"); return CHOOSING_EXPENSE_DATE

async def get_expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    category=q.data.replace("expense_category_","")
    user_id=q.from_user.id; user_name=q.from_user.full_name
    amount=context.user_data.get('amount'); note=context.user_data.get('note')
    created_at=context.user_data.get('created_at')
    db_add_expense(user_id,amount,note,category,created_at)
    await q.edit_message_text(f"✅ Chi tiêu: {amount:,.0f} đ - {note} ({category}) ngày {created_at.strftime('%d/%m/%Y')}")
    budgets=db_get_budgets(user_id); budget_amt=budgets.get(category)
    if budget_amt:
        m_start,m_end=get_month_range(created_at)
        spent=db_sum_expense_by_category_in_period(user_id,category,m_start,m_end)
        ratio=spent/budget_amt if budget_amt>0 else 0
        if ratio>=1.0:
            await q.message.reply_text(f"🚨 *VƯỢT NGÂN SÁCH* {category}: {spent:,.0f}/{budget_amt:,.0f} đ",parse_mode='Markdown')
        elif ratio>=0.9:
            await q.message.reply_text(f"⚠️ *GẦN HẾT NGÂN SÁCH* {category}: {spent:,.0f}/{budget_amt:,.0f} đ (≥90%)",parse_mode='Markdown')
    await post_to_channel(context,
        f"🔔 *Chi tiêu mới*\n💸 `{amount:,.0f} đ`\n📌 {category}\n📝 {note}\n📅 {created_at.strftime('%d/%m/%Y')}\n👤 `{anonymize_name(user_name)}`")
    return await end_conv(update,context,"✅ Chi tiêu đã lưu.")

# ===================== DELETE FLOW =====================
async def handle_delete_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    _clear_keep_submenu(context.user_data)
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("Xóa giao dịch",callback_data="delete_action_individual")],
        [InlineKeyboardButton("Đặt lại toàn bộ",callback_data="delete_action_reset_all")],
        [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]])
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Bạn muốn làm gì?",reply_markup=kb)
    else:
        await update.message.reply_text("Bạn muốn làm gì?",reply_markup=kb)
    return DELETE_CHOOSING_ACTION

async def choose_delete_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    if q.data=="delete_action_individual":
        user_id=update.effective_user.id; txs=db_get_last_n_transactions(user_id,5)
        if not txs: return await end_conv(update,context,"Chưa có giao dịch để xóa.")
        msg="5 giao dịch gần nhất:\n\n"; kb=[]
        for i,t in enumerate(txs):
            tid,ttype,amount,note,cat,cat_str=t
            tname="Chi tiêu" if ttype=="expense" else "Thu nhập"
            dt=datetime.datetime.fromisoformat(cat_str).strftime('%d/%m/%Y')
            msg+=f"*{i+1}.* [{tname}] {amount:,.0f} đ - `{note}` ({cat}) - {dt}\n"
            kb.append([InlineKeyboardButton(f"Xóa mục {i+1}",callback_data=f"delete_id_{tid}_{ttype}")])
        kb.append([InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")])
        await q.edit_message_text(msg,reply_markup=InlineKeyboardMarkup(kb),parse_mode='Markdown')
        return DELETE_INDIVIDUAL_LISTING
    elif q.data=="delete_action_reset_all":
        kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Có, chắc chắn",callback_data="reset_confirm_1_yes")],
            [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]])
        await q.edit_message_text("Xóa TẤT CẢ dữ liệu tài chính? Không thể hoàn tác.",reply_markup=kb)
        return RESET_DATA_CONFIRM_STEP1
    return await cancel_conversation_callback(update,context)

async def delete_choose_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    parts=q.data.split('_'); trans_id=int(parts[2]); trans_type=parts[3]
    context.user_data['id_to_delete']=trans_id; context.user_data['type_to_delete']=trans_type
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Xác nhận XÓA",callback_data="confirm_delete_yes")],
        [InlineKeyboardButton("❌ Hủy",callback_data="cancel_action")]])
    await q.edit_message_text(f"Xóa giao dịch ID {trans_id} ({'Thu nhập' if trans_type=='income' else 'Chi tiêu'})?",reply_markup=kb)
    return DELETE_INDIVIDUAL_CONFIRM

async def delete_confirm_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    if q.data=="confirm_delete_yes":
        db_delete_transaction(context.user_data.get('id_to_delete'),context.user_data.get('type_to_delete'))
        return await end_conv(update,context,"✅ Đã xóa giao dịch.")
    return await end_conv(update,context,"Đã hủy.")

async def reset_data_confirmation_1_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    if q.data=="reset_confirm_1_yes":
        kb=InlineKeyboardMarkup([[InlineKeyboardButton("🔥 XÓA TẤT CẢ",callback_data="reset_confirm_2_yes")],
            [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]])
        await q.edit_message_text("Xác nhận cuối: XÓA toàn bộ dữ liệu? Không thể khôi phục.",reply_markup=kb)
        return RESET_DATA_CONFIRM_STEP2
    return await cancel_conversation_callback(update,context)

async def reset_data_confirmation_2_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    if q.data=="reset_confirm_2_yes":
        db_reset_all_data(q.from_user.id)
        return await end_conv(update,context,"✅ Đã xóa toàn bộ dữ liệu.")
    return await end_conv(update,context,"Đã hủy.")

# ===================== REPORT & CHART FLOWS =====================
async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    _clear_keep_submenu(context.user_data)
    kb=InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Theo tuần",callback_data="report_period_week")],
        [InlineKeyboardButton("📆 Theo tháng",callback_data="report_period_month")],
        [InlineKeyboardButton("🗓️ Theo năm",callback_data="report_period_year")],
        [InlineKeyboardButton("⏰ Toàn bộ",callback_data="report_period_all")],
        [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]
    ])
    msg="📊 *CHỌN KỲ BÁO CÁO*\nChọn khoảng thời gian:"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg,reply_markup=kb,parse_mode='Markdown')
    else:
        await update.message.reply_text(msg,reply_markup=kb,parse_mode='Markdown')
    return CHOOSING_REPORT_PERIOD

async def generate_report_for_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    if q.data=="cancel_action": return await cancel_conversation_callback(update,context)
    period=q.data.replace("report_period_",""); user_id=q.from_user.id
    loading=await q.edit_message_text("⏳ Đang tạo báo cáo...")
    start_date,end_date,title_suffix=get_period_dates(period)
    income,expense,balance=db_get_combined_summary(user_id,start_date,end_date)
    incomes_g=db_list_incomes_grouped(user_id,start_date,end_date)
    expenses_g=db_list_expenses_grouped(user_id,start_date,end_date)
    report=(f"📋 *BÁO CÁO {title_suffix.upper()}*\n{'='*30}\n\n"
            f"💼 *TỔNG QUAN*\n"
            f"┃ 📈 Thu nhập: `{income:,.0f} VND`\n"
            f"┃ 📉 Chi tiêu: `{expense:,.0f} VND`\n"
            f"┃ 💰 Số dư: `{balance:,.0f} VND`\n\n")
    if incomes_g:
        report+="💵 *CHI TIẾT THU NHẬP*\n"
        for i,(src,tot) in enumerate(incomes_g,1):
            pct=(tot/income*100) if income>0 else 0
            report+=f"{i}. **{src}**: `{tot:,.0f}` ({pct:.1f}%)\n"
        report+="\n"
    else: report+="⚠️ *Chưa có thu nhập trong kỳ*\n\n"
    if expenses_g:
        report+="💸 *CHI TIẾT CHI TIÊU*\n"
        for i,(cat,tot) in enumerate(expenses_g,1):
            pct=(tot/expense*100) if expense>0 else 0
            report+=f"{i}. **{cat}**: `{tot:,.0f}` ({pct:.1f}%)\n"
        report+="\n"
    else: report+="✅ *Không có chi tiêu trong kỳ*\n\n"
    budgets=db_get_budgets(user_id)
    if period=="month" and budgets and expenses_g:
        report+="⚠️ *NGÂN SÁCH*\n"
        for cat,tot in expenses_g:
            lim=budgets.get(cat)
            if not lim: continue
            ratio=tot/lim if lim>0 else 0
            if ratio>=1.0: report+=f"- {cat}: `{tot:,.0f}/{lim:,.0f}` 🚨 VƯỢT\n"
            elif ratio>=0.9: report+=f"- {cat}: `{tot:,.0f}/{lim:,.0f}` ⚠️ GẦN\n"
        report+="\n"
    report+=("📊 *ĐÁNH GIÁ*: Tích cực! 🎉" if balance>0 else
             "📊 *ĐÁNH GIÁ*: Cân bằng ⚖️" if balance==0 else
             "📊 *ĐÁNH GIÁ*: Cần cân nhắc ⚠️")
    await loading.delete()
    await q.message.reply_text(report,parse_mode='Markdown')
    return await end_conv(update,context,"✅ Báo cáo hoàn tất.")

async def chart_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    _clear_keep_submenu(context.user_data)
    kb=InlineKeyboardMarkup([
        [InlineKeyboardButton("Theo tuần",callback_data="chart_period_week")],
        [InlineKeyboardButton("Theo tháng",callback_data="chart_period_month")],
        [InlineKeyboardButton("Theo năm",callback_data="chart_period_year")],
        [InlineKeyboardButton("Toàn bộ",callback_data="chart_period_all")],
        [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]
    ])
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Xem biểu đồ theo kỳ nào?",reply_markup=kb)
    else:
        await update.message.reply_text("Xem biểu đồ theo kỳ nào?",reply_markup=kb)
    return CHOOSING_CHART_PERIOD

async def generate_charts_for_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    if q.data=="cancel_action": return await cancel_conversation_callback(update,context)
    period=q.data.replace("chart_period_",""); user_id=q.from_user.id
    _,_,title_suffix=get_period_dates(period)
    msg=await q.edit_message_text(f"⏳ Đang tạo biểu đồ {title_suffix}...")
    charts=await asyncio.to_thread(gen_finance_charts,user_id,period)
    if not charts:
        await msg.delete()
        return await end_conv(update,context,f"Không có dữ liệu trong {title_suffix}.")
    await msg.delete()
    for buf,cap in charts:
        buf.seek(0)
        await q.message.reply_photo(photo=buf,caption=cap)
    return await end_conv(update,context,"✅ Biểu đồ hoàn tất.")

# ===================== EXPORT / IMPORT FINANCE FLOWS =====================
async def export_file_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    _clear_keep_submenu(context.user_data)
    user_id=update.effective_user.id
    rows=db_export_data(user_id)
    if not rows:
        return await end_conv(update,context,"⚠️ Chưa có dữ liệu để xuất.")
    kb=InlineKeyboardMarkup([
        [InlineKeyboardButton("Xuất ra CSV",callback_data="export_csv")],
        [InlineKeyboardButton("Xuất ra Excel",callback_data="export_excel")],
        [InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]
    ])
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Xuất dữ liệu ra định dạng nào?",reply_markup=kb)
    else:
        await update.message.reply_text("Xuất dữ liệu ra định dạng nào?",reply_markup=kb)
    return EXPORT_CHOOSING_FORMAT

async def handle_export_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q=update.callback_query; await q.answer()
    if q.data=="cancel_action": return await cancel_conversation_callback(update,context)
    user_id=q.from_user.id; rows=db_export_data(user_id)
    if not rows: return await end_conv(update,context,"⚠️ Không có dữ liệu.")
    loading=await q.edit_message_text("⏳ Đang chuẩn bị file...")
    prefix=f"finance_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    headers=['Loại','Số tiền','Ghi chú','Danh mục/Nguồn','Ngày','ID']
    if q.data=="export_csv":
        buf=io.StringIO()
        w=csv.writer(buf); w.writerow(headers)
        for r in rows: w.writerow(r)
        data=buf.getvalue().encode('utf-8-sig')
        await q.message.reply_document(document=data,filename=f'{prefix}.csv',caption="📁 Dữ liệu tài chính (CSV)")
    elif q.data=="export_excel":
        if openpyxl is None:
            await loading.delete()
            return await end_conv(update,context,"❌ Cần cài openpyxl: pip install openpyxl")
        wb=openpyxl.Workbook(); ws=wb.active; ws.title="Finance"
        ws.append(headers)
        for r in rows: ws.append(list(r))
        buf=io.BytesIO(); wb.save(buf); buf.seek(0)
        await q.message.reply_document(document=buf.getvalue(),filename=f'{prefix}.xlsx',caption="📁 Dữ liệu tài chính (Excel)")
    await loading.delete()
    return await end_conv(update,context,"✅ Xuất file hoàn tất.")

async def import_file_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    _clear_keep_submenu(context.user_data)
    msg=("📥 *NHẬP DỮ LIỆU TÀI CHÍNH*\n\n"
         "File cần có 5 cột:\n`Loại` | `Số tiền` | `Ghi chú` | `Danh mục/Nguồn` | `Ngày`\n\n"
         "Ví dụ:\n`Chi tiêu | 50000 | Ăn trưa | Ăn uống | 2024-07-28`\n\n"
         "Gửi file .csv hoặc .xlsx ngay bây giờ.")
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Hủy bỏ",callback_data="cancel_action")]])
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg,reply_markup=kb,parse_mode='Markdown')
    else:
        await update.message.reply_text(msg,reply_markup=kb,parse_mode='Markdown')
    return IMPORT_FILE_UPLOADED

async def handle_import_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id=update.effective_user.id; doc=update.message.document
    fname=(doc.file_name or "").lower()
    if not (fname.endswith('.csv') or fname.endswith('.xlsx')):
        await update.message.reply_text("⚠️ Chỉ hỗ trợ .csv hoặc .xlsx. Thử lại.")
        return IMPORT_FILE_UPLOADED
    await update.message.reply_text("⏳ Đang xử lý file...")
    fobj=await doc.get_file(); bio=io.BytesIO()
    await fobj.download_to_memory(bio); bio.seek(0)
    ok_income=ok_expense=fail=0
    try:
        if fname.endswith('.xlsx'):
            if load_workbook is None:
                return await end_conv(update,context,"❌ Cần cài openpyxl: pip install openpyxl")
            wb=load_workbook(filename=bio,read_only=True,data_only=True)
            ws=wb.active
            hrow=next(ws.iter_rows(min_row=1,max_row=1,values_only=True))
            hdrs=[str(h).strip().lower().replace(' ','_') if h else '' for h in hrow]
            col=lambda n: hdrs.index(n) if n in hdrs else -1
            for r in ws.iter_rows(min_row=2,values_only=True):
                if not r or all(v is None or str(v).strip()=='' for v in r): continue
                try:
                    ttype=str(r[col('loại')]).strip().lower() if col('loại')>=0 else ''
                    amount=float(r[col('số_tiền')]) if col('số_tiền')>=0 else 0
                    note=str(r[col('ghi_chú')]).strip() if col('ghi_chú')>=0 else ''
                    cat=str(r[col('danh_mục/nguồn')]).strip() if col('danh_mục/nguồn')>=0 else ''
                    raw_date=r[col('ngày')] if col('ngày')>=0 else None
                    if hasattr(raw_date,'year'): dt=raw_date if hasattr(raw_date,'hour') else datetime.datetime.combine(raw_date,datetime.time())
                    else: dt=datetime.datetime.fromisoformat(str(raw_date).split('T')[0]) if raw_date else datetime.datetime.now()
                    if ttype in ('thu nhập','thu nhap'):
                        db_add_income(user_id,amount,cat,note,dt); ok_income+=1
                    elif ttype in ('chi tiêu','chi tieu'):
                        db_add_expense(user_id,amount,note,cat,dt); ok_expense+=1
                    else: fail+=1
                except Exception: fail+=1
        else:
            reader=csv.DictReader(io.TextIOWrapper(bio,encoding='utf-8'))
            for r in reader:
                try:
                    cols={k.strip().lower().replace(' ','_'):v for k,v in r.items()}
                    ttype=(cols.get('loại') or '').strip().lower()
                    amount=float(cols.get('số_tiền') or cols.get('so_tien') or 0)
                    note=(cols.get('ghi_chú') or cols.get('ghi_chu') or '').strip()
                    cat=(cols.get('danh_mục/nguồn') or cols.get('danh_muc/nguon') or '').strip()
                    raw_date=(cols.get('ngày') or cols.get('ngay') or '').strip()
                    try: dt=datetime.datetime.fromisoformat(raw_date)
                    except Exception: dt=datetime.datetime.now()
                    if ttype in ('thu nhập','thu nhap'):
                        db_add_income(user_id,amount,cat,note,dt); ok_income+=1
                    elif ttype in ('chi tiêu','chi tieu'):
                        db_add_expense(user_id,amount,note,cat,dt); ok_expense+=1
                    else: fail+=1
                except Exception: fail+=1
    except Exception as e:
        logger.error(f"Import error user {user_id}: {e}")
        return await end_conv(update,context,f"❌ Lỗi xử lý file: {e}")
    total=ok_income+ok_expense
    return await end_conv(update,context,
        f"✅ Nhập thành công {total} giao dịch:\n- {ok_income} thu nhập\n- {ok_expense} chi tiêu\n- {fail} lỗi bỏ qua")

# ===================== BUDGET COMMANDS =====================
async def budget_set_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tokens=(update.message.text or "").strip().split()
    if len(tokens)<3:
        await update.message.reply_text("Cú pháp: /ngansach <Danh mục> <Số tiền>\nVD: /ngansach Ăn uống 3tr"); return
    category=" ".join(tokens[1:-1]).strip()
    try:
        amount=parse_amount(tokens[-1])
        if amount<=0: raise ValueError
        db_set_budget(update.effective_user.id,category,amount)
        await update.message.reply_text(f"✅ Đặt ngân sách *{category}*: `{amount:,.0f} đ`/tháng",parse_mode='Markdown')
    except Exception:
        await update.message.reply_text("Số tiền không hợp lệ. Thử: /ngansach Ăn uống 3tr")

async def budget_list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.effective_user.id; budgets=db_get_budgets(user_id)
    if not budgets: await update.message.reply_text("Chưa đặt ngân sách nào."); return
    now=datetime.datetime.now(); m_start,m_end=get_month_range(now)
    lines=["📋 *NGÂN SÁCH THÁNG NÀY*"]
    for cat,lim in budgets.items():
        spent=db_sum_expense_by_category_in_period(user_id,cat,m_start,m_end)
        ratio=spent/lim if lim>0 else 0
        status="🚨 VƯỢT" if ratio>=1.0 else ("⚠️ GẦN" if ratio>=0.9 else "✅ OK")
        lines.append(f"- {cat}: {spent:,.0f}/{lim:,.0f} đ ({ratio*100:.0f}%)  {status}")
    await update.message.reply_text("\n".join(lines),parse_mode='Markdown')

async def budget_delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args=(update.message.text or "").split(maxsplit=1)
    if len(args)<2: await update.message.reply_text("Cú pháp: /xoa_ngansach <Danh mục>"); return
    category=args[1].strip(); db_delete_budget(update.effective_user.id,category)
    await update.message.reply_text(f"🗑️ Đã xóa ngân sách *{category}*",parse_mode='Markdown')

# ===================== UNIFIED TEXT HANDLER (catch-all) =====================
async def unified_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_rate(update): return
    text=(update.message.text or "").strip(); user_id=update.effective_user.id
    # Try crypto natural trade first
    parsed=_parse_natural_trade(text,user_id)
    if parsed:
        side,symbol,qty,price,note=parsed
        await _execute_trade(update,context,side,symbol,qty,price,note); return
    # Try finance NLP
    parsed_f=nlp_parse_transaction(text)
    if parsed_f and parsed_f["amount"]>0:
        if parsed_f["type"]=="income":
            db_add_income(user_id,parsed_f["amount"],parsed_f["category"],parsed_f["note"],parsed_f["created_at"])
            msg=(f"✅ *Thu nhập*: `{parsed_f['amount']:,.0f} đ`\n"
                 f"• Nguồn: *{parsed_f['category']}*\n• Ghi chú: _{parsed_f['note']}_\n• Ngày: {parsed_f['created_at'].strftime('%d/%m/%Y')}")
        else:
            db_add_expense(user_id,parsed_f["amount"],parsed_f["note"],parsed_f["category"],parsed_f["created_at"])
            msg=(f"✅ *Chi tiêu*: `{parsed_f['amount']:,.0f} đ`\n"
                 f"• Danh mục: *{parsed_f['category']}*\n• Ghi chú: _{parsed_f['note']}_\n• Ngày: {parsed_f['created_at'].strftime('%d/%m/%Y')}")
            budgets=db_get_budgets(user_id); budget_amt=budgets.get(parsed_f["category"])
            if budget_amt:
                m_start,m_end=get_month_range(parsed_f["created_at"])
                spent=db_sum_expense_by_category_in_period(user_id,parsed_f["category"],m_start,m_end)
                ratio=spent/budget_amt if budget_amt>0 else 0
                if ratio>=1.0: msg+=f"\n\n🚨 *VƯỢT NGÂN SÁCH* {parsed_f['category']}: {spent:,.0f}/{budget_amt:,.0f} đ"
                elif ratio>=0.9: msg+=f"\n\n⚠️ *GẦN HẾT NGÂN SÁCH* {parsed_f['category']}: {spent:,.0f}/{budget_amt:,.0f} đ"
        await update.message.reply_text(msg,parse_mode='Markdown')
        await update.message.reply_text("Giao dịch đã ghi nhận.",reply_markup=main_menu_keyboard())
        return
    # Fallback
    await update.message.reply_text("Không nhận diện được lệnh. Dùng các nút menu bên dưới:",reply_markup=main_menu_keyboard())

# ===================== ERROR HANDLER =====================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    try: err="".join(traceback.format_exception(None,context.error,context.error.__traceback__))
    except Exception: err=str(context.error)
    logger.error(f"Update {update} caused error:\n{err}")
    try:
        chat_id=update.effective_chat.id if update and hasattr(update,"effective_chat") else None
        if chat_id: await context.bot.send_message(chat_id,"⚠️ Có lỗi xảy ra. Hãy thử lại.")
    except Exception: pass

# ===================== BUILD APP =====================
def build_app() -> "Application":
    run_migrations()
    app = Application.builder().token(BOT_TOKEN).build()

    # Finance ConversationHandlers (register FIRST for priority)
    add_conv=ConversationHandler(
        entry_points=[CommandHandler("them",handle_add_button),
                      MessageHandler(filters.Regex(f"^{re.escape(BTN_FADD)}$"),handle_add_button)],
        states={
            CHOOSING_ADD_TYPE:[CallbackQueryHandler(choose_add_type_callback,pattern="^add_type_")],
            CHOOSING_SUPPLEMENT_TYPE:[CallbackQueryHandler(choose_supplement_type_callback,pattern="^supplement_type_")],
            CHOOSING_INCOME_AMOUNT:[MessageHandler(filters.TEXT & ~filters.COMMAND,get_income_amount)],
            CONFIRM_INCOME_AMOUNT:[CallbackQueryHandler(confirm_income_amount,pattern="^confirm_amount_")],
            CHOOSING_INCOME_NOTE:[MessageHandler(filters.TEXT & ~filters.COMMAND,get_income_note)],
            CHOOSING_INCOME_DATE:[CallbackQueryHandler(choose_income_date,pattern="^date_"),
                                  MessageHandler(filters.TEXT & ~filters.COMMAND,get_income_date_input)],
            CHOOSING_INCOME_SOURCE:[CallbackQueryHandler(get_income_source,pattern="^income_source_")],
            CHOOSING_EXPENSE_AMOUNT:[MessageHandler(filters.TEXT & ~filters.COMMAND,get_expense_amount)],
            CONFIRM_EXPENSE_AMOUNT:[CallbackQueryHandler(confirm_expense_amount,pattern="^confirm_amount_")],
            CHOOSING_EXPENSE_NOTE:[MessageHandler(filters.TEXT & ~filters.COMMAND,get_expense_note)],
            CHOOSING_EXPENSE_DATE:[CallbackQueryHandler(choose_expense_date,pattern="^date_"),
                                   MessageHandler(filters.TEXT & ~filters.COMMAND,get_expense_date_input)],
            CHOOSING_EXPENSE_CATEGORY:[CallbackQueryHandler(get_expense_category,pattern="^expense_category_")],
        },
        fallbacks=[CommandHandler("cancel",cancel_conversation),
                   CallbackQueryHandler(cancel_conversation_callback,pattern="^cancel_action$")],
    )
    delete_conv=ConversationHandler(
        entry_points=[CommandHandler("xoa",handle_delete_button),
                      MessageHandler(filters.Regex(f"^{re.escape(BTN_FDEL)}$"),handle_delete_button)],
        states={
            DELETE_CHOOSING_ACTION:[CallbackQueryHandler(choose_delete_action,pattern="^delete_action_")],
            DELETE_INDIVIDUAL_LISTING:[CallbackQueryHandler(delete_choose_item,pattern="^delete_id_")],
            DELETE_INDIVIDUAL_CONFIRM:[CallbackQueryHandler(delete_confirm_action,pattern="^confirm_delete_")],
            RESET_DATA_CONFIRM_STEP1:[CallbackQueryHandler(reset_data_confirmation_1_handler,pattern="^reset_confirm_1_")],
            RESET_DATA_CONFIRM_STEP2:[CallbackQueryHandler(reset_data_confirmation_2_handler,pattern="^reset_confirm_2_")],
        },
        fallbacks=[CommandHandler("cancel",cancel_conversation),
                   CallbackQueryHandler(cancel_conversation_callback,pattern="^cancel_action$")],
    )
    report_conv=ConversationHandler(
        entry_points=[CommandHandler("baocao",report_start)],
        states={CHOOSING_REPORT_PERIOD:[CallbackQueryHandler(generate_report_for_period,pattern="^report_period_|^cancel_action$")]},
        fallbacks=[CommandHandler("cancel",cancel_conversation),
                   CallbackQueryHandler(cancel_conversation_callback,pattern="^cancel_action$")],
    )
    chart_conv=ConversationHandler(
        entry_points=[CommandHandler("bieudo",chart_start)],
        states={CHOOSING_CHART_PERIOD:[CallbackQueryHandler(generate_charts_for_period,pattern="^chart_period_|^cancel_action$")]},
        fallbacks=[CommandHandler("cancel",cancel_conversation),
                   CallbackQueryHandler(cancel_conversation_callback,pattern="^cancel_action$")],
    )
    export_conv=ConversationHandler(
        entry_points=[CommandHandler("xuatfile",export_file_start),
                      MessageHandler(filters.Regex(f"^{re.escape(BTN_FEXPORT)}$"),export_file_start)],
        states={EXPORT_CHOOSING_FORMAT:[CallbackQueryHandler(handle_export_choice,pattern="^export_|^cancel_action$")]},
        fallbacks=[CommandHandler("cancel",cancel_conversation),
                   CallbackQueryHandler(cancel_conversation_callback,pattern="^cancel_action$")],
    )
    import_conv=ConversationHandler(
        entry_points=[CommandHandler("nhapfile",import_file_start),
                      MessageHandler(filters.Regex(f"^{re.escape(BTN_FIMPORT)}$"),import_file_start)],
        states={IMPORT_FILE_UPLOADED:[MessageHandler(filters.Document.ALL,handle_import_file_upload)]},
        fallbacks=[CommandHandler("cancel",cancel_conversation),
                   CallbackQueryHandler(cancel_conversation_callback,pattern="^cancel_action$")],
    )

    app.add_handler(add_conv)
    app.add_handler(delete_conv)
    app.add_handler(report_conv)
    app.add_handler(chart_conv)
    app.add_handler(export_conv)
    app.add_handler(import_conv)

    # Commands
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("help",help_cmd))
    app.add_handler(CommandHandler("cp",cp_cmd))
    app.add_handler(CommandHandler("cp_add",cp_add))
    app.add_handler(CommandHandler("cp_sell",cp_sell))
    app.add_handler(CommandHandler("cp_map",cp_map_cmd))
    app.add_handler(CommandHandler("cp_import",cp_import_cmd))
    app.add_handler(CommandHandler("ngansach",budget_set_cmd))
    app.add_handler(CommandHandler("xem_ngansach",budget_list_cmd))
    app.add_handler(CommandHandler("xoa_ngansach",budget_delete_cmd))
    app.add_handler(CommandHandler("cancel",cancel_conversation))

    # Home navigation buttons
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(f"^{re.escape(BTN_HOME_CRYPTO)}$"), handle_home_crypto_btn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(f"^{re.escape(BTN_HOME_FINANCE)}$"), handle_home_finance_btn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(f"^{re.escape(BTN_BACK)}$"), handle_back_btn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(f"^{re.escape(BTN_BUDGET)}$"), handle_budget_btn))

    # Shared chart/report buttons (routed by submenu state)
    shared_btn_pattern = f"^({'|'.join(re.escape(b) for b in [BTN_CHART, BTN_REPORT])})$"
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(shared_btn_pattern), handle_shared_btn))

    # Crypto menu buttons
    crypto_btn_pattern = f"^({'|'.join(re.escape(b) for b in [BTN_PORTFOLIO,BTN_BUY,BTN_SELL,BTN_MAP,BTN_CIMPORT,BTN_CEXPORT])})$"
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(crypto_btn_pattern), handle_crypto_menu_btns))

    # Callbacks
    app.add_handler(CallbackQueryHandler(theme_select_cb,         pattern="^SET_THEME:"))
    app.add_handler(CallbackQueryHandler(handle_budget_menu_callback, pattern="^budget_menu_"))
    # Global fallbacks for chart/report when triggered via handle_shared_btn (outside ConvHandler)
    app.add_handler(CallbackQueryHandler(generate_charts_for_period,  pattern="^chart_period_"))
    app.add_handler(CallbackQueryHandler(generate_report_for_period,  pattern="^report_period_"))

    # Unified catch-all (natural trade + finance NLP)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unified_text_handler))

    app.add_error_handler(error_handler)
    return app

# ===================== MAIN =====================
if __name__ == "__main__":
    start_html_server()
    app = build_app()
    logger.info(f"Bot đang chạy... HTML dashboard port {HTML_PORT}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
