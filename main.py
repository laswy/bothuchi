# -*- coding: utf-8 -*-
"""
Univer Crypto Portfolio Bot
- Telegram bot (python-telegram-bot v21 async)
- Portfolio in USD using CoinGecko
- Donut (allocation by value) + Table image on /cp and 📋 Danh mục
- Import/Export CSV hoặc Excel with clear success/error counts
"""
from __future__ import annotations

import os
import io
import csv
import sqlite3
import datetime as _dt
import tempfile
import asyncio
import traceback
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env")
except ImportError:
    pass  # python-dotenv not installed, rely on env vars set externally
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from typing import List, Dict, Tuple, Optional
import requests
try:
    from openpyxl import load_workbook
except Exception:
    load_workbook = None
from urllib.parse import quote

from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)

# Charts
import matplotlib
matplotlib.use("Agg")
from matplotlib import gridspec

# ===================== CONFIG =====================
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]  # set in .env
DB_PATH = os.environ.get("UNIVER_DB_PATH", "univer_all_in_one.db")
CRYPTO_DB_PATH = DB_PATH  # merge: use one SQLite file for all modules
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# ===================== CHANNEL PUSH =====================
OWNER_USER_ID  = 679130099          # @htmtma — chỉ user này mới trigger gửi channel
CHANNEL_CHAT_ID = -1001974996093    # @shinronv

# ===================== THEMES =====================
THEMES = {
    "dark": {
        "name": "🌑 Dark",
        # Donut
        "bg": "#0a0e27", "card_bg": "#151932",
        "text_primary": "#ffffff", "text_secondary": "#94a3b8",
        "accent": "#00d4ff",
        "chart_colors": ["#00d4ff","#00ff88","#ffd700","#ff6b6b","#c56cf0",
                         "#4834d4","#22a6b3","#f0932b","#eb4d4b","#6ab04c",
                         "#30336b","#95afc0","#535c68","#ff9ff3","#48dbfb"],
        # Table
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

# theme per user — lưu trong memory (reset khi restart) và SQLite
_user_themes: Dict[int, str] = {}

# ===================== RATE LIMITER =====================
# Giới hạn: mỗi user tối đa RATE_MAX_CALLS lệnh trong RATE_WINDOW giây
RATE_WINDOW = 60   # giây
RATE_MAX_CALLS = 10

_rate_store: Dict[int, list] = {}  # user_id -> [timestamp, ...]

def is_rate_limited(user_id: int) -> bool:
    now = _dt.datetime.now().timestamp()
    calls = _rate_store.get(user_id, [])
    # Xóa các call cũ ngoài window
    calls = [t for t in calls if now - t < RATE_WINDOW]
    if len(calls) >= RATE_MAX_CALLS:
        _rate_store[user_id] = calls
        return True
    calls.append(now)
    _rate_store[user_id] = calls
    return False

async def check_rate(update: Update) -> bool:
    """Trả về True nếu bị giới hạn (đã reply thông báo). False nếu OK."""
    user_id = update.effective_user.id
    if is_rate_limited(user_id):
        await update.message.reply_text(
            f"⏳ Bạn gửi lệnh quá nhanh. Vui lòng chờ {RATE_WINDOW} giây rồi thử lại."
        )
        return True
    return False

# --- lazy migration guard for crypto DB ---
# ===================== DB =====================


def run_migrations():
    conn = sqlite3.connect(CRYPTO_DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA user_version")
    ver_row = cur.fetchone()
    ver = ver_row[0] if ver_row and ver_row[0] is not None else 0

    # Create required tables (idempotent)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crypto_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            cg_id TEXT,
            side TEXT NOT NULL,
            qty REAL NOT NULL,
            price_usd REAL NOT NULL,
            fee_usd REAL DEFAULT 0,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crypto_map (
            symbol TEXT PRIMARY KEY,
            cg_id TEXT NOT NULL,
            name TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crypto_prices (
            cg_id TEXT NOT NULL,
            price_usd REAL NOT NULL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            theme TEXT NOT NULL DEFAULT 'dark'
        )
    """)

    # Bump version at least to 1
    if ver < 1:
        cur.execute("PRAGMA user_version = 1")

    conn.commit()
    conn.close()


_MIGRATIONS_DONE = False
def ensure_migrated():
    global _MIGRATIONS_DONE
    if not _MIGRATIONS_DONE:
        run_migrations()
        _MIGRATIONS_DONE = True


def db_conn():
    ensure_migrated()
    return sqlite3.connect(CRYPTO_DB_PATH)

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
    if theme not in THEMES:
        theme = DEFAULT_THEME
    _user_themes[user_id] = theme
    conn = db_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_settings(user_id, theme) VALUES(?,?)
        ON CONFLICT(user_id) DO UPDATE SET theme=excluded.theme
    """, (user_id, theme))
    conn.commit(); conn.close()

def db_crypto_upsert_map(symbol: str, cg_id: str, name: Optional[str] = None):
    conn = db_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO crypto_map(symbol, cg_id, name)
        VALUES (?, ?, ?)
        ON CONFLICT(symbol) DO UPDATE SET cg_id=excluded.cg_id, name=COALESCE(excluded.name, crypto_map.name)
    """, (symbol.upper(), cg_id, name))
    conn.commit(); conn.close()

def db_crypto_get_map(symbol: str) -> Optional[str]:
    conn = db_conn(); cur = conn.cursor()
    cur.execute("SELECT cg_id FROM crypto_map WHERE symbol = ?", (symbol.upper(),))
    row = cur.fetchone(); conn.close()
    return row[0] if row else None

def db_crypto_add_trade(user_id: int, symbol: str, side: str, qty: float, price_usd: float,
                        note: str = "", created_at: Optional[_dt.datetime] = None,
                        cg_id: Optional[str] = None, fee_usd: float = 0.0):
    conn = db_conn(); cur = conn.cursor()
    if created_at is None:
        created_at = _dt.datetime.now()
    cur.execute("""
        INSERT INTO crypto_trades (user_id, symbol, cg_id, side, qty, price_usd, fee_usd, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, symbol.upper(), cg_id, side.upper(), qty, price_usd, fee_usd, note, created_at.isoformat()))
    conn.commit(); conn.close()

def db_crypto_positions(user_id: int):
    """Aggregate net qty and invested USD per symbol for a user; attach a reasonable cg_id per symbol."""
    ensure_migrated()
    conn = db_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            SELECT symbol,
                   SUM(CASE WHEN side='BUY' THEN qty ELSE -qty END) AS qty_net,
                   SUM(CASE WHEN side='BUY' THEN qty*price_usd + fee_usd ELSE -(qty*price_usd) END) AS invested_usd
            FROM crypto_trades
            WHERE user_id = ?
            GROUP BY symbol
            HAVING ABS(qty_net) > 1e-12
            ORDER BY symbol
        """, (user_id,))
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        # If tables are missing for some reason, migrate and retry once
        run_migrations()
        cur.execute("""
            SELECT symbol,
                   SUM(CASE WHEN side='BUY' THEN qty ELSE -qty END) AS qty_net,
                   SUM(CASE WHEN side='BUY' THEN qty*price_usd + fee_usd ELSE -(qty*price_usd) END) AS invested_usd
            FROM crypto_trades
            WHERE user_id = ?
            GROUP BY symbol
            HAVING ABS(qty_net) > 1e-12
            ORDER BY symbol
        """, (user_id,))
        rows = cur.fetchall()

    result = []
    for symbol, qty_net, invested_usd in rows:
        # Prefer the latest non-null cg_id in trades; otherwise fallback to mapping table; otherwise guess
        cur.execute("""
            SELECT cg_id
            FROM crypto_trades
            WHERE user_id = ? AND symbol = ? AND cg_id IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id, symbol))
        row = cur.fetchone()
        cg_id = (row[0] if row and row[0] else None) or db_crypto_get_map(symbol) or cg_guess_id_from_symbol(symbol)
        result.append({
            "symbol": symbol,
            "qty": float(qty_net or 0.0),
            "invested_usd": float(invested_usd or 0.0),
            "cg_id": cg_id
        })
    conn.close()
    return result


def db_crypto_all_trades(user_id: int):
    conn = db_conn(); cur = conn.cursor()
    cur.execute("""
        SELECT symbol, COALESCE(cg_id,''), side, qty, price_usd, fee_usd, COALESCE(note,''), created_at
        FROM crypto_trades
        WHERE user_id = ?
        ORDER BY created_at ASC
    """, (user_id,))
    rows = cur.fetchall(); conn.close()
    return rows

# ===================== COINGECKO =====================
def cg_guess_id_from_symbol(symbol: str) -> Optional[str]:
    s = symbol.upper()
    static = {
        "BTC": "bitcoin", "ETH": "ethereum", "ATOM": "cosmos", "DYDX": "dydx-chain",
        "BABY": "babylon", "DYM": "dymension", "AURA": "aura-network", "ZETA": "zetachain",
        "SOL": "solana", "BNB": "binancecoin", "TON": "the-open-network",
        "USDT": "tether", "USDC": "usd-coin"
    }
    return static.get(s)

def cg_simple_price_usd(cg_ids: List[str]) -> Dict[str, float]:
    if not cg_ids: return {}
    ids_param = ",".join(sorted(set(cg_ids)))
    url = f"{COINGECKO_BASE}/simple/price?ids={quote(ids_param)}&vs_currencies=usd"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {k: float(v.get("usd", 0.0) or 0.0) for k, v in data.items()}
    except Exception:
        pass
    return {}

# ===================== HISTORY SERIES (for performance chart) =====================
def cg_market_chart_usd(cg_id: str, days: int = 365):
    """Return dict {label: price}. Daily for days>1, hourly for days<=1."""
    interval = "hourly" if days <= 1 else "daily"
    url = f"{COINGECKO_BASE}/coins/{quote(cg_id)}/market_chart?vs_currency=usd&days={days}&interval={interval}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return {}
        data = r.json()
        out = {}
        for ts, price in data.get("prices", []):
            dt = _dt.datetime.utcfromtimestamp(ts/1000.0)
            label = dt.strftime('%H:%M') if days <= 1 else dt.date().isoformat()
            out[label] = float(price)
        return out
    except Exception:
        return {}

def portfolio_history_series(user_id: int, days: int = 365):
    """Compute portfolio value series for last `days` using users' net quantities and CoinGecko prices."""
    rows = db_crypto_all_trades(user_id)
    if not rows:
        return [], []

    # Aggregate trades per symbol and get cg_ids
    trades_by_sym = {}
    cg_ids = {}
    for symbol, cg_id, side, qty, price, fee, note, created_at in rows:
        sym = symbol.upper()
        trades_by_sym.setdefault(sym, []).append((side, float(qty), created_at))
        if cg_id: cg_ids[sym] = cg_id

    # Fill cg_id gaps with mapping/static guesses
    for sym in trades_by_sym:
        if sym not in cg_ids:
            guess = db_crypto_get_map(sym) or cg_guess_id_from_symbol(sym)
            if guess: cg_ids[sym] = guess

    if not cg_ids:
        return [], []

    # Fetch price series for each symbol
    price_hist = {}
    all_labels = set()
    for sym, cg in cg_ids.items():
        ph = cg_market_chart_usd(cg, days=days)
        if not ph: 
            continue
        price_hist[sym] = ph
        all_labels.update(ph.keys())

    if not price_hist:
        return [], []

    labels = sorted(list(all_labels))

    # Normalize trade timestamps to labels (date component)
    norm_trades_by_sym = {}
    for sym, arr in trades_by_sym.items():
        tmp = []
        for side, qty, at in arr:
            try:
                d = _dt.datetime.fromisoformat(at).date().isoformat()
            except Exception:
                try:
                    d = str(at).split(" ")[0]
                except Exception:
                    d = labels[0]
            tmp.append((d, side, qty))
        tmp.sort(key=lambda x: x[0])
        norm_trades_by_sym[sym] = tmp

    # Rolling net qty per label
    qty_by_sym_by_label = {sym: {} for sym in trades_by_sym}
    running_qty = {sym: 0.0 for sym in trades_by_sym}
    for lb in labels:
        for sym in trades_by_sym:
            for td, side, qty in [t for t in norm_trades_by_sym[sym] if t[0] == lb]:
                running_qty[sym] += qty if side == "BUY" else -qty
            qty_by_sym_by_label[sym][lb] = running_qty[sym]

    # Compute portfolio value per label
    values = []
    for lb in labels:
        total = 0.0
        for sym in trades_by_sym:
            price = price_hist.get(sym, {}).get(lb, None)
            if price is None: 
                continue
            total += qty_by_sym_by_label[sym].get(lb, 0.0) * price
        values.append(total)

    return labels, values

# ===================== CHART (Donut + Table) =====================
import matplotlib.font_manager as _fm

def _chart_font(size: int, bold: bool = False):
    weight = 'bold' if bold else 'normal'
    for name in ['Noto Sans', 'DejaVu Sans']:
        try:
            return _fm.FontProperties(family=name, size=size, weight=weight)
        except Exception:
            pass
    return _fm.FontProperties(size=size, weight=weight)

def gen_portfolio_donut_image(positions, prices, theme: str = DEFAULT_THEME) -> str:
    C = THEMES.get(theme, THEMES[DEFAULT_THEME])

    tokens_data = []
    total_value = 0.0
    for p in positions:
        sym = p.get("symbol", "").upper()
        qty = float(p.get("qty", 0) or 0)
        cg  = p.get("cg_id") or cg_guess_id_from_symbol(sym) or ""
        price_now = float(prices.get(cg, 0.0) if cg else 0.0)
        value = qty * price_now
        if value > 0:
            tokens_data.append({'symbol': sym or "N/A", 'value': value, 'qty': qty, 'price': price_now})
            total_value += value

    tokens_data.sort(key=lambda x: x['value'], reverse=True)
    if not tokens_data:
        tokens_data = [{'symbol': 'N/A', 'value': 1.0, 'qty': 0, 'price': 0}]
        total_value = 1.0
    if len(tokens_data) > 10:
        others_val = sum(t['value'] for t in tokens_data[10:])
        tokens_data = tokens_data[:10]
        if others_val > 0:
            tokens_data.append({'symbol': 'Others', 'value': others_val, 'qty': 0, 'price': 0})
    for t in tokens_data:
        t['pct'] = t['value'] / total_value * 100 if total_value > 0 else 0

    n = len(tokens_data)
    chart_colors = C['chart_colors'][:n]

    fig = plt.figure(figsize=(14, 8), facecolor=C['bg'])
    ax_donut  = fig.add_axes([0.02, 0.08, 0.44, 0.80])
    ax_legend = fig.add_axes([0.48, 0.05, 0.50, 0.85])
    ax_donut.set_facecolor(C['bg'])
    ax_legend.set_facecolor(C['bg'])
    ax_legend.axis('off')
    ax_donut.set_aspect('equal')

    sizes   = [t['value'] for t in tokens_data]
    explode = [0.04 if i < 3 else 0 for i in range(n)]
    wedges, _ = ax_donut.pie(
        sizes, startangle=90, colors=chart_colors, explode=explode,
        wedgeprops=dict(width=0.42, edgecolor=C['bg'], linewidth=2),
    )
    for i, w in enumerate(wedges):
        w.set_alpha(0.92 if i >= 3 else 1.0)

    centre = Circle((0, 0), 0.53, fc=C['card_bg'], linewidth=2.5,
                    edgecolor=C['accent'], zorder=10)
    ax_donut.add_artist(centre)
    ax_donut.text(0, 0.13, 'TONG GIA TRI', ha='center', va='center',
                  fontproperties=_chart_font(9), color=C['text_secondary'], zorder=11)
    ax_donut.text(0, -0.08, f'${total_value:,.0f}', ha='center', va='center',
                  fontproperties=_chart_font(18, bold=True), color=C['accent'], zorder=11)

    for wedge, token in zip(wedges, tokens_data):
        if token['pct'] < 4:
            continue
        ang = (wedge.theta2 + wedge.theta1) / 2.0
        r   = 0.70
        x   = r * np.cos(np.deg2rad(ang))
        y   = r * np.sin(np.deg2rad(ang))
        ax_donut.text(x, y, f"{token['pct']:.0f}%", ha='center', va='center',
                      fontproperties=_chart_font(9, bold=True), color='white', zorder=12)

    ax_legend.text(0.5, 0.97, 'CHI TIET DANH MUC', transform=ax_legend.transAxes,
                   ha='center', fontproperties=_chart_font(14, bold=True), color=C['accent'])

    row_h     = 0.072
    y0        = 0.90
    col_sym   = 0.18
    col_val   = 0.52
    col_pct   = 0.72
    col_bar_x = 0.78
    col_bar_w = 0.18

    for i, token in enumerate(tokens_data):
        if i >= 12:
            break
        y   = y0 - i * row_h
        clr = chart_colors[i] if i < len(chart_colors) else C['accent']

        ax_legend.add_patch(FancyBboxPatch(
            (0.03, y - 0.055), 0.94, row_h * 0.88,
            boxstyle="round,pad=0.008",
            facecolor=C['card_bg'], edgecolor=clr,
            linewidth=1.5, alpha=0.85,
            transform=ax_legend.transAxes))

        ax_legend.text(0.07, y - 0.018, f"#{i+1}" if i < 10 else "~",
                       transform=ax_legend.transAxes,
                       fontproperties=_chart_font(9, bold=True), color=clr, va='center')
        ax_legend.text(col_sym, y - 0.018, token['symbol'],
                       transform=ax_legend.transAxes,
                       fontproperties=_chart_font(11, bold=True), color=C['text_primary'], va='center')
        ax_legend.text(col_val, y - 0.018, f"${token['value']:,.2f}",
                       transform=ax_legend.transAxes,
                       fontproperties=_chart_font(10), color=C['text_primary'], va='center', ha='center')
        ax_legend.text(col_pct, y - 0.018, f"{token['pct']:.1f}%",
                       transform=ax_legend.transAxes,
                       fontproperties=_chart_font(10, bold=True), color=clr, va='center', ha='center')
        ax_legend.add_patch(FancyBboxPatch(
            (col_bar_x, y - 0.030), col_bar_w, 0.012,
            boxstyle="round,pad=0", facecolor=C['card_bg'],
            edgecolor=C['text_secondary'], linewidth=0.8, alpha=0.6,
            transform=ax_legend.transAxes))
        fill_w = col_bar_w * min(token['pct'] / 100, 1.0)
        if fill_w > 0:
            ax_legend.add_patch(FancyBboxPatch(
                (col_bar_x, y - 0.030), fill_w, 0.012,
                boxstyle="round,pad=0", facecolor=clr,
                edgecolor='none', alpha=0.85,
                transform=ax_legend.transAxes))

    num_tok = len([t for t in tokens_data if t['symbol'] != 'Others'])
    avg_val = total_value / max(num_tok, 1)
    top_tok = tokens_data[0]
    stats_y = 0.97 - 12 * row_h - 0.04
    ax_legend.add_patch(FancyBboxPatch(
        (0.03, stats_y - 0.08), 0.94, 0.095,
        boxstyle="round,pad=0.01",
        facecolor=C['card_bg'], edgecolor=C['accent'],
        linewidth=1.5, alpha=0.9,
        transform=ax_legend.transAxes))
    ax_legend.text(0.5, stats_y - 0.015, 'THONG KE',
                   transform=ax_legend.transAxes, ha='center',
                   fontproperties=_chart_font(10, bold=True), color=C['accent'])
    ax_legend.text(0.5, stats_y - 0.052,
                   f"So token: {num_tok}  |  TB/token: ${avg_val:,.0f}  |  Lon nhat: {top_tok['symbol']} (${top_tok['value']:,.0f})",
                   transform=ax_legend.transAxes, ha='center',
                   fontproperties=_chart_font(8.5), color=C['text_secondary'])

    timestamp = _dt.datetime.now().strftime("%d/%m/%Y %H:%M")
    fig.text(0.5, 0.97, 'PHAN BO DANH MUC DAU TU CRYPTO',
             ha='center', fontproperties=_chart_font(16, bold=True), color=C['accent'])
    fig.text(0.5, 0.01, f'Cap nhat: {timestamp}',
             ha='center', fontproperties=_chart_font(8), color=C['text_secondary'], style='italic')
    for yline in (0.945, 0.025):
        fig.add_artist(plt.Line2D([0.05, 0.95], [yline, yline],
                                  linewidth=1, color=C['accent'], alpha=0.4,
                                  transform=fig.transFigure))

    fd, path = tempfile.mkstemp(prefix="donut_", suffix=".png")
    os.close(fd)
    plt.savefig(path, dpi=180, bbox_inches='tight', facecolor=C['bg'], edgecolor='none')
    plt.close(fig)
    return path


def gen_portfolio_table_image(positions, prices, theme: str = DEFAULT_THEME) -> str:
    C = THEMES.get(theme, THEMES[DEFAULT_THEME])

    rows = []
    total_inv = total_val = 0.0
    for p in positions:
        sym  = p.get("symbol", "").upper()
        qty  = float(p.get("qty", 0) or 0)
        inv  = float(max(p.get("invested_usd", 0) or 0, 0))
        cg   = p.get("cg_id") or cg_guess_id_from_symbol(sym) or ""
        price_now = float(prices.get(cg, 0.0) if cg else 0.0)
        value = qty * price_now
        pnl   = value - inv
        pct   = (pnl / inv * 100) if inv > 1e-12 else 0.0
        rows.append({'symbol': sym, 'qty': f"{qty:,.4f}".rstrip('0').rstrip('.'),
                     'price': f"${price_now:,.2f}", 'value': f"${value:,.2f}",
                     'invested': f"${inv:,.2f}", 'pnl': f"${pnl:+,.2f}",
                     'pct': pct, 'pct_str': f"{pct:+.2f}%"})
        total_inv += inv
        total_val += value

    total_pnl = total_val - total_inv
    total_pct = (total_pnl / total_inv * 100) if total_inv > 1e-12 else 0.0

    headers = ["Token", "So luong", "Gia (USD)", "Gia tri", "Von", "Lai/Lo", "%"]
    table_data = [headers]
    for r in rows:
        table_data.append([r['symbol'], r['qty'], r['price'], r['value'],
                           r['invested'], r['pnl'], r['pct_str']])
    if not rows:
        table_data.append(["N/A", "0", "$0.00", "$0.00", "$0.00", "$0.00", "+0.00%"])
    table_data.append(["TONG CONG", "", "",
                       f"${total_val:,.2f}", f"${total_inv:,.2f}",
                       f"${total_pnl:+,.2f}", f"{total_pct:+.2f}%"])

    n_rows  = len(table_data)
    fig_h   = max(4.5, 1.2 + 0.55 * n_rows)
    fig = plt.figure(figsize=(15, fig_h), facecolor=C['bg_dark'])
    ax  = fig.add_subplot(111, facecolor=C['bg_dark'])
    ax.axis('off')

    tbl = ax.table(cellText=table_data, loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.9)

    fp_hdr  = _chart_font(10, bold=True)
    fp_cell = _chart_font(10)
    fp_bold = _chart_font(10, bold=True)

    for (i, j), cell in tbl.get_celld().items():
        cell.set_edgecolor(C['border'])
        cell.set_linewidth(0.5)
        if i == 0:
            cell.set_facecolor(C['bg_header'])
            cell.get_text().set_fontproperties(fp_hdr)
            cell.get_text().set_color(C['accent'])
            cell.set_height(0.08)
        elif i == n_rows - 1:
            cell.set_facecolor(C['bg_total'])
            cell.get_text().set_fontproperties(fp_bold)
            if j in (5, 6):
                clr = C['positive'] if total_pnl > 0 else (C['negative'] if total_pnl < 0 else C['neutral'])
                cell.get_text().set_color(clr)
            else:
                cell.get_text().set_color(C['accent'])
            cell.set_height(0.08)
        else:
            cell.set_facecolor(C['bg_row1'] if i % 2 == 0 else C['bg_row2'])
            cell.get_text().set_fontproperties(fp_bold if j == 0 else fp_cell)
            if j in (5, 6) and (i - 1) < len(rows):
                pv  = rows[i - 1]['pct']
                clr = C['positive'] if pv > 0 else (C['negative'] if pv < 0 else C['neutral'])
                cell.get_text().set_color(clr)
            else:
                cell.get_text().set_color(C['text_light'])

    pnl_color = C['positive'] if total_pnl > 0 else (C['negative'] if total_pnl < 0 else C['neutral'])
    ax.text(0.5, 1.06, 'DANH MUC DAU TU CRYPTO',
            transform=ax.transAxes, ha='center',
            fontproperties=_chart_font(16, bold=True), color=C['accent'])
    ax.text(0.5, 1.02,
            f"Tong: ${total_val:,.2f}  |  Von: ${total_inv:,.2f}  |  Lai/Lo: ${total_pnl:+,.2f} ({total_pct:+.2f}%)",
            transform=ax.transAxes, ha='center',
            fontproperties=_chart_font(10), color=pnl_color, style='italic')

    if total_inv > 0:
        bar_ax = fig.add_axes([0.1, 0.01, 0.8, 0.018])
        bar_ax.set_xlim(0, 1); bar_ax.set_ylim(0, 1); bar_ax.axis('off')
        bar_ax.add_patch(mpatches.Rectangle((0, 0), 1, 1,
                         facecolor=C['bg_header'], edgecolor=C['border'], linewidth=1))
        ratio = min(abs(total_pct) / 100, 1.0)
        bclr  = C['positive'] if total_pnl >= 0 else C['negative']
        x0    = 0.5 if total_pnl >= 0 else 0.5 - ratio * 0.5
        bar_ax.add_patch(mpatches.Rectangle((x0, 0), ratio * 0.5, 1, facecolor=bclr, alpha=0.75))
        bar_ax.axvline(0.5, color=C['accent'], linewidth=1.5, alpha=0.8)

    timestamp = _dt.datetime.now().strftime("%d/%m/%Y %H:%M")
    ax.text(0.99, -0.04, f"Cap nhat: {timestamp}",
            transform=ax.transAxes, ha='right',
            fontproperties=_chart_font(8), color=C['text_dim'], style='italic')

    plt.subplots_adjust(top=0.88, bottom=0.06, left=0.02, right=0.98)
    fd, path = tempfile.mkstemp(prefix="table_", suffix=".png")
    os.close(fd)
    plt.savefig(path, dpi=180, bbox_inches='tight', facecolor=C['bg_dark'], edgecolor='none')
    plt.close(fig)
    return path


# ===================== COMBINED IMAGE: Performance(1Y) + Donut + Table =====================
def gen_portfolio_overview_with_perf(user_id: int, positions, prices) -> str:
    # Data for donut/table
    labels, values, invested_list, pnl_list, prices_now, qtys = [], [], [], [], [], []
    for p in positions:
        sym = p.get("symbol", "")
        qty = float(p.get("qty", 0.0) or 0.0)
        invested = float(max(p.get("invested_usd", 0.0) or 0.0, 0.0))
        cg_id = p.get("cg_id") or cg_guess_id_from_symbol(sym) or ""
        price_now = float(prices.get(cg_id, 0.0) if cg_id else 0.0)
        value_now = qty * price_now
        pnl = value_now - invested

        labels.append(sym or "N/A")
        qtys.append(qty)
        values.append(value_now)
        invested_list.append(invested)
        pnl_list.append(pnl)
        prices_now.append(price_now)

    total_invested = sum(invested_list)
    total_value = sum(values)
    total_pnl = total_value - total_invested
    total_pct = (total_pnl / total_invested * 100.0) if total_invested > 1e-12 else 0.0

    # History 1Y
    dates, hist_values = portfolio_history_series(user_id, days=365)

    # Layout: 3 rows
    # Row0: Performance line (1Y)
    # Row1: Donut (allocation)
    # Row2: Table
    fig = plt.figure(figsize=(14, 12))
    gs = gridspec.GridSpec(3, 1, height_ratios=[1.6, 1.2, 1.8])

    # Performance
    ax_perf = fig.add_subplot(gs[0, 0])
    if not dates or not hist_values:
        dates = ["N/A"]; hist_values = [0.0]
    ax_perf.plot(dates, hist_values)
    ax_perf.set_title("Hiệu suất danh mục (1Y)")
    ax_perf.set_ylabel("USD")
    ax_perf.tick_params(axis='x', rotation=45)

    # Donut
    ax_donut = fig.add_subplot(gs[1, 0])
    labs = labels[:] if labels else ["N/A"]
    vals = values[:] if labels else [1.0]
    tot = sum(vals)
    fracs = [1.0/len(labs)]*len(labs) if tot<=0 else [v/tot for v in vals]
    ax_donut.pie(fracs, labels=labs, autopct="%1.1f%%", wedgeprops=dict(width=0.4))
    ax_donut.set_title("Tỷ trọng danh mục theo giá trị hiện tại")

    # Table
    ax_table = fig.add_subplot(gs[2, 0])
    ax_table.axis("off")
    header = ["Token", "Qty", "Giá now", "Giá trị", "Vốn", "P/L", "P/L %"]
    table_data = [header]
    if labels:
        for i, sym in enumerate(labels):
            inv = invested_list[i]
            val = values[i]
            pnl = pnl_list[i]
            qty_txt = f"{qtys[i]:g}"
            price_now_txt = f"{prices_now[i]:,.2f}"
            pct = (pnl/inv*100) if inv > 1e-12 else 0.0
            table_data.append([sym, qty_txt, price_now_txt, f"{val:,.2f}", f"{inv:,.2f}", f"{pnl:,.2f}", f"{pct:+.2f}%"])
    else:
        table_data.append(["N/A", "0", "0.00", "0.00", "0.00", "0.00", "+0.00%"])
    table_data.append(["TỔNG", "", "", f"{total_value:,.2f}", f"{total_invested:,.2f}", f"{total_pnl:,.2f}", f"{total_pct:+.2f}%"])
    table = ax_table.table(cellText=table_data, loc="center", cellLoc="center")
    table.scale(1, 1.2)
    ax_table.set_title("Chi tiết danh mục (bảng)")

    fig.tight_layout()
    fd, path = tempfile.mkstemp(prefix="cp_overview_", suffix=".png"); os.close(fd)
    plt.savefig(path, dpi=160); plt.close(fig)
    return path

# ===================== UI =====================

# Tên nút bấm (Reply Keyboard) — dùng làm key nhận message
BTN_PORTFOLIO  = "📋 Danh mục"
BTN_BUY        = "➕ Mua"
BTN_SELL       = "➖ Bán"
BTN_THEME      = "🎨 Theme"
BTN_MAP        = "🔗 Map token"
BTN_IMPORT     = "⬇️ Nhập CSV/Excel"
BTN_EXPORT     = "⬆️ Xuất CSV/Excel"
BTN_HELP       = "❓ Hướng dẫn"

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Bàn phím nổi cố định phía dưới chat."""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(BTN_PORTFOLIO), KeyboardButton(BTN_BUY), KeyboardButton(BTN_SELL), KeyboardButton(BTN_THEME)],
            [KeyboardButton(BTN_IMPORT), KeyboardButton(BTN_EXPORT), KeyboardButton(BTN_MAP), KeyboardButton(BTN_HELP)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

# ---- Nội dung hướng dẫn cho từng nút ----
HINT_BUY = (
    "➕ *MUA token*\n"
    "Cú pháp: `/cp_add SYMBOL SỐ_LƯỢNG GIÁ_USD [ghi_chú]`\n\n"
    "Ví dụ:\n"
    "`/cp_add BTC 0.02 60000 mua thử`\n"
    "`/cp_add ETH 1.5 3000`"
)

HINT_SELL = (
    "➖ *BÁN token*\n"
    "Cú pháp: `/cp_sell SYMBOL SỐ_LƯỢNG GIÁ_USD [ghi_chú]`\n\n"
    "Ví dụ:\n"
    "`/cp_sell BTC 0.01 62000 chốt lời`\n"
    "`/cp_sell ETH 0.5 3200`"
)

HINT_MAP = (
    "🔗 *MAP TOKEN với CoinGecko ID*\n"
    "Dùng khi bot không nhận ra token của bạn.\n"
    "Cú pháp: `/cp_map SYMBOL CG_ID`\n\n"
    "Ví dụ:\n"
    "`/cp_map ATOM cosmos`\n"
    "`/cp_map TON the-open-network`\n\n"
    "Tra CG\\_ID tại: https://www.coingecko.com"
)

HINT_IMPORT = (
    "⬇️ *NHẬP danh mục từ file*\n\n"
    "Bước 1: Bot sẽ gửi file mẫu CSV ngay bây giờ.\n"
    "Bước 2: Điền dữ liệu vào file mẫu theo đúng cột.\n"
    "Bước 3: Gửi file CSV hoặc Excel vào chat.\n"
    "Bước 4: *REPLY* vào file vừa gửi, gõ lệnh `/cp_import`\n\n"
    "⚠️ Không dùng caption — bot sẽ không nhận lệnh trong caption."
)

HINT_EXPORT = (
    "⬆️ *XUẤT danh mục ra file*\n\n"
    "Bot sẽ gửi toàn bộ lịch sử giao dịch của bạn dưới dạng file CSV.\n"
    "File này có thể dùng để backup hoặc nhập lại sau."
)

HINT_ALL = (
    "📖 *HƯỚNG DẪN NHANH*\n\n"
    "*1. Xem danh mục*\n"
    "→ Bấm nút 📋 Danh mục\n\n"
    "*2. Thêm giao dịch mua*\n"
    "→ `/cp_add SYMBOL SỐ_LƯỢNG GIÁ`\n"
    "VD: `/cp_add BTC 0.1 60000`\n\n"
    "*3. Thêm giao dịch bán*\n"
    "→ `/cp_sell SYMBOL SỐ_LƯỢNG GIÁ`\n"
    "VD: `/cp_sell ETH 0.5 3200`\n\n"
    "*4. Map token thủ công*\n"
    "→ `/cp_map SYMBOL CG_ID`\n"
    "VD: `/cp_map ATOM cosmos`\n\n"
    "*5. Nhập từ file CSV/Excel*\n"
    "→ Bấm ⬇️ Nhập CSV/Excel → làm theo hướng dẫn\n\n"
    "*6. Xuất file backup*\n"
    "→ Bấm ⬆️ Xuất CSV/Excel\n\n"
    "Gõ /start bất kỳ lúc nào để hiện lại bàn phím menu."
)

# ---- Handlers cho Reply Keyboard ----

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Chào mừng! Chọn chức năng từ bàn phím bên dưới.\nGõ /help hoặc bấm ❓ Hướng dẫn để xem cách dùng.",
        reply_markup=main_menu_keyboard()
    )

async def handle_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận text từ Reply Keyboard và xử lý."""
    if await check_rate(update):
        return
    text = (update.message.text or "").strip()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if text == BTN_PORTFOLIO:
        try:
            await send_portfolio_images(chat_id, user_id, context)
        except Exception as e:
            await update.message.reply_text(f"Chưa có dữ liệu. Dùng ➕ Mua để thêm.\nLỗi: {e}")

    elif text == BTN_THEME:
        current = db_get_theme(user_id)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"{'✅ ' if k == current else ''}{v['name']}",
                callback_data=f"SET_THEME:{k}"
            ) for k, v in THEMES.items()]
        ])
        await update.message.reply_text("🎨 Chọn theme biểu đồ:", reply_markup=kb)

    elif text == BTN_BUY:
        await update.message.reply_text(HINT_BUY, parse_mode="Markdown")

    elif text == BTN_SELL:
        await update.message.reply_text(HINT_SELL, parse_mode="Markdown")

    elif text == BTN_MAP:
        await update.message.reply_text(HINT_MAP, parse_mode="Markdown")

    elif text == BTN_IMPORT:
        # Gửi file mẫu + hướng dẫn
        tmp_fd, tmp = tempfile.mkstemp(prefix="crypto_import_template_", suffix=".csv")
        os.close(tmp_fd)
        with open(tmp, "w", newline="", encoding="utf-8") as tf:
            tw = csv.writer(tf)
            tw.writerow(["symbol", "cg_id", "side", "qty", "price_usd", "fee_usd", "note", "created_at"])
            tw.writerow(["ATOM", "cosmos", "BUY", "1", "10.0", "0", "", "2025-01-01 12:00:00"])
            tw.writerow(["BTC", "bitcoin", "BUY", "0.01", "50000", "2.5", "spot on binance", "2025-02-01 20:30:00"])
        try:
            with open(tmp, "rb") as f:
                await update.message.reply_document(f, filename="crypto_import_template.csv",
                                                    caption="📄 File mẫu — điền dữ liệu vào rồi gửi lại.")
        finally:
            try:
                os.remove(tmp)
            except Exception:
                pass
        await update.message.reply_text(HINT_IMPORT, parse_mode="Markdown")

    elif text == BTN_EXPORT:
        await update.message.reply_text(HINT_EXPORT, parse_mode="Markdown")
        # Thực hiện xuất luôn
        rows = db_crypto_all_trades(user_id)
        if not rows:
            await update.message.reply_text("Chưa có giao dịch để xuất.")
            return
        headers = ["symbol", "cg_id", "side", "qty", "price_usd", "fee_usd", "note", "created_at"]
        fd, path = tempfile.mkstemp(prefix="portfolio_", suffix=".csv")
        os.close(fd)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(headers)
            for r in rows:
                w.writerow(r)
        try:
            with open(path, "rb") as f:
                await update.message.reply_document(f, filename="crypto_portfolio.csv",
                                                    caption="✅ Danh mục đã xuất.")
        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    elif text == BTN_HELP:
        await update.message.reply_text(HINT_ALL, parse_mode="Markdown")

def _build_positions_and_prices(user_id: int):
    positions = db_crypto_positions(user_id)
    ids = [p["cg_id"] or cg_guess_id_from_symbol(p["symbol"]) for p in positions if (p["cg_id"] or cg_guess_id_from_symbol(p["symbol"]))]
    prices = cg_simple_price_usd(ids)
    return positions, prices

# ===================== Portfolio actions =====================

def format_portfolio_text(user_id: int) -> str:
    # Trả về tóm tắt danh mục dạng Markdown
    try:
        positions, prices = _build_positions_and_prices(user_id)
    except Exception:
        positions, prices = [], {}
    if not positions:
        return "Danh mục trống. Dùng /cp_add để thêm giao dịch."
    lines = ["*📋 Danh mục hiện tại*"]
    total_invested = 0.0
    total_value = 0.0
    row_lines = []
    for p in positions:
        sym = p.get("symbol","?")
        qty = float(p.get("qty") or 0.0)
        invested = float(p.get("invested_usd") or 0.0)
        cg_id = p.get("cg_id") or cg_guess_id_from_symbol(sym)
        price = float(prices.get(cg_id, 0.0))
        value = qty * price
        pnl = value - invested
        pnl_pct = (pnl / invested * 100.0) if abs(invested) > 1e-9 else 0.0
        total_invested += invested
        total_value += value
        row_lines.append(f"- {sym}: {qty:g} × ${price:,.2f} = ${value:,.2f}  (vốn: ${invested:,.2f}, PnL: {pnl:+,.2f} | {pnl_pct:+.2f}%)")
    tot_pnl = total_value - total_invested
    tot_pct = (tot_pnl / total_invested * 100.0) if abs(total_invested) > 1e-9 else 0.0
    lines += row_lines[:25]
    if len(row_lines) > 25:
        lines.append(f"... và {len(row_lines)-25} mã nữa")
    lines.append("")
    lines.append(f"*Tổng*: vốn ${total_invested:,.2f} → giá trị ${total_value:,.2f} | *PnL*: {tot_pnl:+,.2f} ({tot_pct:+.2f}%)")
    return "\n".join(lines)


async def send_portfolio_images(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    positions, prices = _build_positions_and_prices(user_id)
    if not positions:
        await context.bot.send_message(chat_id, "Danh mục trống. Dùng /cp_add để thêm giao dịch.")
        return
    theme = db_get_theme(user_id)
    donut = table = None
    try:
        donut = await asyncio.to_thread(gen_portfolio_donut_image, positions, prices, theme)
        table = await asyncio.to_thread(gen_portfolio_table_image, positions, prices, theme)
        with open(donut, "rb") as f1:
            await context.bot.send_photo(chat_id, f1)
        with open(table, "rb") as f2:
            await context.bot.send_photo(chat_id, f2, caption="📋 Danh mục (donut + bảng)")
        # Gửi biểu đồ phân bổ lên channel nếu là owner
        if user_id == OWNER_USER_ID:
            try:
                with open(donut, "rb") as fc:
                    timestamp = _dt.datetime.now().strftime("%d/%m/%Y %H:%M")
                    await context.bot.send_photo(
                        CHANNEL_CHAT_ID, fc,
                        caption=f"📊 Phân bổ danh mục — {timestamp}"
                    )
            except Exception as ce:
                await context.bot.send_message(chat_id, f"⚠️ Không gửi được lên channel: {ce!r}")
    except Exception as e:
        await context.bot.send_message(chat_id, f"⚠️ Lỗi khi tạo/gửi ảnh danh mục: {e!r}")
    finally:
        for fp in (donut, table):
            try:
                if fp and os.path.exists(fp):
                    os.remove(fp)
            except Exception:
                pass

async def cp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_rate(update): return
    await send_portfolio_images(update.effective_chat.id, update.effective_user.id, context)

# ===================== Import/Export =====================

def _parse_trades_from_excel(bio) -> list[dict]:
    """
    Read Excel (xlsx/xlsm) from a BytesIO and return list of row dicts.
    Accepts BOTH:
      A) Import template headers: Date, Exchange, Symbol, Pair, Side, Quantity, Price, Fee, FeeCurrency, Note, CreatedAt
      B) Export headers: symbol, cg_id, side, qty, price_usd, fee_usd, note, created_at
    Sheet: prefers 'Trades', otherwise first sheet.
    """
    if load_workbook is None:
        raise RuntimeError("Excel import requires openpyxl. Please install: pip install openpyxl")
    bio.seek(0)
    wb = load_workbook(filename=bio, read_only=True, data_only=True)
    ws = wb["Trades"] if "Trades" in wb.sheetnames else wb.active

    # Read header row
    header_cells = next(ws.iter_rows(min_row=1, max_row=1, values_only=False))
    headers = []
    for c in header_cells:
        val = c.value
        if isinstance(val, str):
            headers.append(val.strip())
        else:
            headers.append(val if val is not None else "")
    # Build a lowercase index map
    norm = {str(h).strip().lower(): i for i, h in enumerate(headers) if str(h).strip()}

    def get_val(row_vals, *names):
        for name in names:
            k = name.lower()
            if k in norm and norm[k] < len(row_vals):
                return row_vals[norm[k]]
        return None

    rows: list[dict] = []

    # Iterate rows
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r is None or all((v is None or (isinstance(v, str) and v.strip() == "")) for v in r):
            continue

        # Map flexible headers to canonical keys expected by cp_import_cmd
        date_val = get_val(r, "date", "created_at")  # use created_at if no date
        exchange = get_val(r, "exchange")
        symbol = get_val(r, "symbol", "asset", "token")
        pair = get_val(r, "pair")
        side = get_val(r, "side", "action")
        quantity = get_val(r, "quantity", "qty", "amount")
        price = get_val(r, "price", "price_usd")
        fee = get_val(r, "fee", "fee_usd")
        fee_currency = get_val(r, "feecurrency", "fee_currency", "fee cur", "fee currency")
        note = get_val(r, "note", "memo", "comment")
        created_at = get_val(r, "created_at")  # may duplicate date_val

        # If the export format is used, set sensible defaults
        if fee_currency in (None, "") and get_val(r, "fee_usd") is not None:
            fee_currency = "USD"

        # Build canonical dict
        row = {
            "date": date_val,
            "exchange": exchange,
            "symbol": symbol,
            "pair": pair,
            "side": side,
            "quantity": quantity,
            "price": price,
            "fee": fee,
            "fee_currency": fee_currency,
            "note": note,
            "created_at": created_at,
        }
        rows.append(row)

    # If we ended up with zero rows, provide a helpful error
    if not rows:
        have = list(norm.keys())
        raise ValueError(f"No data rows found. Detected headers: {have}. "
                         f"Expected either import template or export columns.")
    return rows

def _normalize_datetime_str(val) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    # Try pandas-like parser via datetime if it's a float/excel serial date we can't handle directly
    # Handle Excel datetime objects (openpyxl may give datetime)
    try:
        # If already datetime
        if hasattr(val, "year") and hasattr(val, "month") and hasattr(val, "day"):
            return val.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    # Try common formats
    fmts = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y"]
    for f in fmts:
        try:
            return _dt.datetime.strptime(s, f).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
    # Fallback: try fromisoformat
    try:
        return _dt.datetime.fromisoformat(s).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    raise ValueError(f"Invalid datetime: {s}")

async def cp_import_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_rate(update): return
    user = update.effective_user
    doc = None
    if update.message and update.message.document:
        doc = update.message.document
    if not doc and update.message and update.message.reply_to_message and update.message.reply_to_message.document:
        doc = update.message.reply_to_message.document
    if not doc:
        await update.message.reply_text(
            "Hãy gửi *file CSV hoặc Excel (xlsx/xlsm)* rồi reply `/cp_import` vào file đã gửi.",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text("📥 Đang xử lý file, vui lòng chờ...")

    fobj = await context.bot.get_file(doc.file_id)
    bio = io.BytesIO(); await fobj.download_to_memory(out=bio); bio.seek(0)

    filename = (doc.file_name or "").lower()
    mime = (doc.mime_type or "").lower()

    ok = fail = 0

    try:
        if filename.endswith((".xlsx",".xlsm")) or "spreadsheetml" in mime:
            # Excel path
            rows = _parse_trades_from_excel(bio)
            for row in rows:
                try:
                    symbol = (row.get("symbol") or "").strip().upper()
                    side = (row.get("side") or "").strip().upper()
                    qty = float(row.get("quantity") or 0)
                    price = float(row.get("price") or 0)
                    fee = float(row.get("fee") or 0) if str(row.get("fee") or "").strip() != "" else 0.0
                    note = (row.get("note") or "").strip()
                    at_raw = row.get("created_at")
                    at_norm = None
                    if at_raw not in (None, ""):
                        try:
                            at_norm = _normalize_datetime_str(at_raw)
                            created_at = _dt.datetime.fromisoformat(at_norm)
                        except Exception:
                            created_at = None
                    else:
                        created_at = None
                    cg_id = db_crypto_get_map(symbol) or cg_guess_id_from_symbol(symbol)
                    if cg_id:
                        db_crypto_upsert_map(symbol, cg_id)
                    if not symbol or side not in ("BUY","SELL") or qty<=0 or price<=0:
                        fail += 1; continue
                    db_crypto_add_trade(user.id, symbol, side, qty, price, note=note, cg_id=cg_id, fee_usd=fee, created_at=created_at)
                    ok += 1
                except Exception:
                    fail += 1
        else:
            # CSV hoặc Excel path (UTF-8)
            reader = csv.DictReader(io.TextIOWrapper(bio, encoding="utf-8"))
            for row in reader:
                try:
                    symbol = (row.get("symbol") or row.get("Symbol") or "").strip().upper()
                    side = (row.get("side") or row.get("Side") or "").strip().upper()
                    qty = float(row.get("qty") or row.get("quantity") or row.get("Quantity") or 0)
                    price = float(row.get("price") or row.get("price_usd") or row.get("Price") or 0)
                    fee = float(row.get("fee") or row.get("Fee") or 0) if str(row.get("fee") or row.get("Fee") or "").strip() != "" else 0.0
                    note = (row.get("note") or row.get("Note") or "").strip()
                    cg_id = (row.get("cg_id") or row.get("CG_ID") or row.get("cgid") or "").strip() or None
                    at_raw = (row.get("created_at") or row.get("CreatedAt") or "").strip()
                    if not symbol or side not in ("BUY","SELL") or qty<=0 or price<=0:
                        fail += 1; continue
                    created_at = None
                    if at_raw:
                        try:
                            created_at = _dt.datetime.fromisoformat(at_raw)
                        except Exception:
                            created_at = None
                    if not cg_id:
                        cg_id = db_crypto_get_map(symbol) or cg_guess_id_from_symbol(symbol)
                    if cg_id:
                        db_crypto_upsert_map(symbol, cg_id)
                    db_crypto_add_trade(user.id, symbol, side, qty, price, note=note, cg_id=cg_id, fee_usd=fee, created_at=created_at)
                    ok += 1
                except Exception:
                    fail += 1
    except RuntimeError as e:
        await update.message.reply_text(f"❌ {e}")
        return

    await update.message.reply_text(f"✅ Đã nhập {ok} giao dịch, lỗi {fail}. Dùng /cp để xem danh mục.")

# ===================== Commands =====================

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HINT_ALL, parse_mode="Markdown", reply_markup=main_menu_keyboard())

def _parse_price(s: str) -> Optional[float]:
    """Chuyển chuỗi giá: '70k' -> 70000, '1.5m' -> 1500000, '87' -> 87"""
    s = s.lower().replace(',', '').strip()
    try:
        if s.endswith('k'):   return float(s[:-1]) * 1_000
        if s.endswith('m'):   return float(s[:-1]) * 1_000_000
        if s.endswith('b'):   return float(s[:-1]) * 1_000_000_000
        return float(s)
    except Exception:
        return None

def _parse_qty(s: str) -> Optional[float]:
    """Chuyển số lượng thuần: '10', '0.5', '1.5k'"""
    return _parse_price(s)  # dùng cùng logic

def _get_held_qty(user_id: int, symbol: str) -> float:
    """Lấy số lượng đang nắm giữ của user cho symbol."""
    conn = db_conn(); cur = conn.cursor()
    cur.execute("""
        SELECT SUM(CASE WHEN side='BUY' THEN qty ELSE -qty END)
        FROM crypto_trades WHERE user_id=? AND symbol=?
    """, (user_id, symbol.upper()))
    row = cur.fetchone(); conn.close()
    return float(row[0] or 0.0) if row and row[0] is not None else 0.0

def _parse_natural_trade(text: str, user_id: int = 0):
    """
    Parser lệnh tự nhiên. Trả về (side, symbol, qty, price, note) hoặc None.

    Hỗ trợ:
      mua BTC 0.01 giá 70k
      mua BTC 0.01 70000
      bán SOL 10 giá 87
      bán SOL tất cả giá 100
      bán SOL hết giá 100
      bán SOL 50% giá 0.01
      bán SOL 50pct giá 0.01
      mua ETH 2 price 3000
      buy BTC 0.1 60000
      sell SOL all 100
      sell BABY 30% 0.02
    """
    import re
    text = text.strip()

    # Xác định side
    side = None
    for kw in ['bán', 'ban', 'sell']:
        if text.lower().startswith(kw):
            side = 'SELL'
            text = text[len(kw):].strip()
            break
    if side is None:
        for kw in ['mua', 'buy']:
            if text.lower().startswith(kw):
                side = 'BUY'
                text = text[len(kw):].strip()
                break
    if side is None:
        return None

    # Lấy symbol (token đầu tiên)
    parts = text.split()
    if not parts:
        return None
    symbol = parts[0].upper()
    text   = ' '.join(parts[1:]).strip()

    # Xóa từ khóa nhiễu: "giá", "price", "gia", "@"
    text = re.sub(r'\b(gia|giá|price|@)\b', ' ', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'\s+', ' ', text)

    parts = text.split()
    if len(parts) < 2:
        return None

    # Phần qty có thể là: số, %, "tất cả", "hết", "all"
    qty_raw   = parts[0].lower()
    price_raw = parts[1]
    note      = ' '.join(parts[2:]).strip() if len(parts) > 2 else ''

    # Xử lý qty
    qty = None
    if qty_raw in ('tất cả', 'tat ca', 'hết', 'het', 'all', 'toàn bộ', 'toan bo'):
        if side == 'SELL' and user_id:
            qty = _get_held_qty(user_id, symbol)
        else:
            return None
    elif re.fullmatch(r'[\d.,]+\s*%', qty_raw) or re.fullmatch(r'[\d.,]+pct', qty_raw):
        pct_val = float(re.sub(r'[%pct]', '', qty_raw).replace(',', ''))
        if side == 'SELL' and user_id:
            held = _get_held_qty(user_id, symbol)
            qty  = held * pct_val / 100
        else:
            return None
    else:
        qty = _parse_qty(qty_raw)

    if qty is None or qty <= 0:
        return None

    price = _parse_price(price_raw)
    if price is None or price <= 0:
        return None

    return side, symbol, qty, price, note


def _parse_trade_args(args: List[str]):
    """Parser cũ giữ lại cho /cp_add /cp_sell dạng command."""
    if len(args) < 3:
        return None
    symbol = args[0].upper()
    try:
        qty   = float(args[1])
        price = float(args[2])
    except Exception:
        return None
    note = " ".join(args[3:]).strip() if len(args) > 3 else ""
    return symbol, qty, price, note


async def _execute_trade(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         side: str, symbol: str, qty: float, price: float, note: str):
    """Thực thi lệnh mua/bán và reply kết quả."""
    user_id = update.effective_user.id
    if side == 'SELL':
        held = _get_held_qty(user_id, symbol)
        if qty > held + 1e-9:
            await update.message.reply_text(
                f"⚠️ Bạn chỉ đang giữ {held:g} {symbol}, không thể bán {qty:g}.")
            return
    cg_id = db_crypto_get_map(symbol) or cg_guess_id_from_symbol(symbol)
    if cg_id:
        db_crypto_upsert_map(symbol, cg_id)
    db_crypto_add_trade(user_id, symbol, side, qty, price, note=note, cg_id=cg_id)
    action = "MUA" if side == 'BUY' else "BAN"
    total  = qty * price
    msg    = f"✅ {action} {symbol}: {qty:g} @ ${price:,.4g} = ${total:,.2f} USD"
    if note:
        msg += f"\nGhi chu: {note}"
    await update.message.reply_text(msg)


async def cp_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_rate(update): return
    ensure_migrated()
    parsed = _parse_trade_args(context.args)
    if not parsed:
        await update.message.reply_text(
            "Cú pháp: /cp_add SYMBOL SL GIA [ghi_chu]\n"
            "Ví dụ: /cp_add BTC 0.01 70000\n"
            "Hoặc nhắn nhanh: mua BTC 0.01 giá 70k")
        return
    symbol, qty, price, note = parsed
    if qty <= 0 or price <= 0:
        await update.message.reply_text("Số lượng & giá phải > 0")
        return
    await _execute_trade(update, context, 'BUY', symbol, qty, price, note)


async def cp_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_rate(update): return
    ensure_migrated()
    parsed = _parse_trade_args(context.args)
    if not parsed:
        await update.message.reply_text(
            "Cú pháp: /cp_sell SYMBOL SL GIA [ghi_chu]\n"
            "Ví dụ: /cp_sell SOL 10 87\n"
            "Hoặc nhắn nhanh: bán SOL tất cả giá 100")
        return
    symbol, qty, price, note = parsed
    if qty <= 0 or price <= 0:
        await update.message.reply_text("Số lượng & giá phải > 0")
        return
    await _execute_trade(update, context, 'SELL', symbol, qty, price, note)


async def handle_natural_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận lệnh giao dịch tự nhiên từ text thường (không phải nút menu)."""
    if await check_rate(update): return
    ensure_migrated()
    text    = (update.message.text or "").strip()
    user_id = update.effective_user.id
    parsed  = _parse_natural_trade(text, user_id)
    if not parsed:
        return  # không phải lệnh giao dịch, bỏ qua
    side, symbol, qty, price, note = parsed
    await _execute_trade(update, context, side, symbol, qty, price, note)


async def cp_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Map symbol thủ công với CoinGecko ID: /cp_map SYMBOL CG_ID"""
    if await check_rate(update): return
    ensure_migrated()
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Cú pháp: /cp_map SYMBOL CG_ID")
        return
    symbol, cg_id = args[0].upper(), args[1]
    db_crypto_upsert_map(symbol, cg_id)
    await update.message.reply_text(f"✅ Đã map {symbol} -> {cg_id}")

# ===================== Error Handler =====================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        err = "".join(traceback.format_exception(None, context.error, context.error.__traceback__))
    except Exception:
        err = str(context.error)
    print("===== ERROR ====="); print("Update:", update); print(err)
    try:
        chat_id = update.effective_chat.id if update and hasattr(update, "effective_chat") else None
        if chat_id:
            await context.bot.send_message(chat_id, "⚠️ Có lỗi xảy ra. Hãy thử lại.")
    except Exception:
        pass


async def theme_select_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    theme_key = q.data.split(":")[1]
    if theme_key not in THEMES:
        await q.edit_message_text("❌ Theme không hợp lệ.")
        return
    db_set_theme(q.from_user.id, theme_key)
    theme_name = THEMES[theme_key]["name"]
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{'✅ ' if k == theme_key else ''}{v['name']}",
            callback_data=f"SET_THEME:{k}"
        ) for k, v in THEMES.items()]
    ])
    await q.edit_message_text(f"✅ Đã chọn theme: {theme_name}\nBấm 📋 Danh mục để xem kết quả.", reply_markup=kb)

# ===================== App =====================

def build_app() -> Application:
    run_migrations()

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("cp", cp))
    app.add_handler(CommandHandler("cp_add", cp_add))
    app.add_handler(CommandHandler("cp_sell", cp_sell))
    app.add_handler(CommandHandler("cp_map", cp_map))
    app.add_handler(CommandHandler("cp_import", cp_import_cmd))

    # Reply Keyboard buttons
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(
            rf"^({BTN_PORTFOLIO}|{BTN_BUY}|{BTN_SELL}|{BTN_THEME}|{BTN_MAP}|{BTN_IMPORT}|{BTN_EXPORT}|{BTN_HELP})$"
        ),
        handle_menu_text
    ))

    # Lệnh giao dịch tự nhiên: "mua BTC 0.01 giá 70k", "bán SOL tất cả giá 100"...
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(
            r'(?i)^(mua|bán|ban|buy|sell)\s+\w+'
        ),
        handle_natural_trade
    ))

    # Theme selection callback
    app.add_handler(CallbackQueryHandler(theme_select_cb, pattern=r"^SET_THEME:"))

    app.add_error_handler(error_handler)
    return app


if __name__ == "__main__":
    app = build_app()
    print("Bot crypto đang chạy...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.run_polling(allowed_updates=Update.ALL_TYPES)
