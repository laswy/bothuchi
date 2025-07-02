import logging
import sqlite3
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import io # Để xử lý ảnh và file trong bộ nhớ
import os # Để xóa file tạm nếu cần

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# --- HÀM MÃ HÓA TÊN NGƯỜI DÙNG ---
def mask_user_name(full_name: str) -> str:
    """Ẩn tên người dùng, chỉ hiển thị 3 ký tự cuối."""
    full_name = full_name.strip()
    if len(full_name) <= 3:
        return '****' + full_name
    return '****' + full_name[-3:]

# --- CẤU HÌNH ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Kênh Telegram để đăng thông báo giao dịch mới.
CHANNEL_ID = "@congthuchi" 

# Trạng thái cho ConversationHandler
CHOOSING_INCOME_AMOUNT, CHOOSING_INCOME_NOTE, CHOOSING_INCOME_DATE, CHOOSING_INCOME_SOURCE, CONFIRM_INCOME_AMOUNT = range(5)
CHOOSING_EXPENSE_AMOUNT, CHOOSING_EXPENSE_NOTE, CHOOSING_EXPENSE_DATE, CHOOSING_EXPENSE_CATEGORY, CONFIRM_EXPENSE_AMOUNT = range(5, 10)
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

DB_PATH = "expenses.db"
LARGE_AMOUNT_THRESHOLD = 100_000_000

# --- CÁC HÀM XỬ LÝ LOGIC (Không thay đổi) ---

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            note TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            source TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def parse_amount(text: str) -> float:
    text = text.lower().replace(" ", "").replace(",", "")
    if "tr" in text:
        text = text.replace("tr", "")
        if "k" in text:
            parts = text.split("k")
            million = float(parts[0]) * 1_000_000
            thousand = float(parts[1]) * 1_000 if parts[1] else 0
            return million + thousand
        else:
            return float(text) * 1_000_000
    elif "k" in text:
        return float(text.replace("k", "")) * 1_000
    else:
        return float(text)

def parse_date(date_str: str) -> datetime.datetime:
    today = datetime.date.today()
    try:
        return datetime.datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        try:
            return datetime.datetime.strptime(f"{date_str}/{today.year}", "%d/%m/%Y")
        except ValueError:
            raise ValueError("Định dạng ngày không hợp lệ. Vui lòng nhập DD/MM/YYYY hoặc DD/MM.")

def db_add_income(user_id: int, amount: float, source: str, note: str, created_at: datetime.datetime = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if created_at is None:
        created_at = datetime.datetime.now()
    cursor.execute("INSERT INTO incomes (user_id, amount, source, note, created_at) VALUES (?, ?, ?, ?, ?)",
                   (user_id, amount, source, note, created_at.isoformat()))
    conn.commit()
    conn.close()

def db_add_expense(user_id: int, amount: float, note: str, category: str, created_at: datetime.datetime = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if created_at is None:
        created_at = datetime.datetime.now()
    cursor.execute("INSERT INTO expenses (user_id, amount, note, category, created_at) VALUES (?, ?, ?, ?, ?)",
                   (user_id, amount, note, category, created_at.isoformat()))
    conn.commit()
    conn.close()

def db_list_expenses_grouped(user_id: int, start_date=None, end_date=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT category, SUM(amount) FROM expenses WHERE user_id = ?"
    params = [user_id]
    if start_date and end_date:
        end_date_inclusive = end_date + datetime.timedelta(days=1)
        query += " AND created_at >= ? AND created_at < ?"
        params.extend([start_date.isoformat(), end_date_inclusive.isoformat()])
    query += " GROUP BY category ORDER BY SUM(amount) DESC"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return rows

def db_list_incomes_grouped(user_id: int, start_date=None, end_date=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT source, SUM(amount) FROM incomes WHERE user_id = ?"
    params = [user_id]
    if start_date and end_date:
        end_date_inclusive = end_date + datetime.timedelta(days=1)
        query += " AND created_at >= ? AND created_at < ?"
        params.extend([start_date.isoformat(), end_date_inclusive.isoformat()])
    query += " GROUP BY source ORDER BY SUM(amount) DESC"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return rows

def db_get_monthly_report(user_id, start_date=None, end_date=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    expense_query = "SELECT strftime('%Y-%m', created_at) as month, SUM(amount) FROM expenses WHERE user_id = ?"
    income_query = "SELECT strftime('%Y-%m', created_at) as month, SUM(amount) FROM incomes WHERE user_id = ?"
    params = [user_id]
    if start_date and end_date:
        end_date_inclusive = end_date + datetime.timedelta(days=1)
        expense_query += " AND created_at >= ? AND created_at < ?"
        income_query += " AND created_at >= ? AND created_at < ?"
        params.extend([start_date.isoformat(), end_date_inclusive.isoformat()])
    expense_query += " GROUP BY month ORDER BY month"
    income_query += " GROUP BY month ORDER BY month"
    cursor.execute(expense_query, tuple(params))
    expenses = cursor.fetchall()
    cursor.execute(income_query, tuple(params))
    incomes = cursor.fetchall()
    conn.close()
    return expenses, incomes

def db_get_combined_summary(user_id: int, start_date=None, end_date=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    income_query = "SELECT SUM(amount) FROM incomes WHERE user_id = ?"
    expense_query = "SELECT SUM(amount) FROM expenses WHERE user_id = ?"
    params = [user_id]
    if start_date and end_date:
        end_date_inclusive = end_date + datetime.timedelta(days=1)
        income_query += " AND created_at >= ? AND created_at < ?"
        expense_query += " AND created_at >= ? AND created_at < ?"
        params.extend([start_date.isoformat(), end_date_inclusive.isoformat()])
    cursor.execute(income_query, tuple(params))
    income = cursor.fetchone()[0] or 0
    cursor.execute(expense_query, tuple(params))
    expense = cursor.fetchone()[0] or 0
    conn.close()
    return income, expense, income - expense

def db_export_data(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 'Chi tiêu' as type, amount, note, category as label, created_at, id
        FROM expenses WHERE user_id = ?
        UNION ALL
        SELECT 'Thu nhập' as type, amount, note, source as label, created_at, id
        FROM incomes WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id, user_id))
    rows = cursor.fetchall()
    headers = ['Loại', 'Số tiền', 'Ghi chú', 'Danh mục/Nguồn', 'Ngày', 'ID_Giao_dich']
    conn.close()
    return pd.DataFrame(rows, columns=headers)

def db_get_last_n_transactions(user_id: int, limit: int = 5):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, 'expense' as type, amount, note, category, created_at FROM expenses WHERE user_id = ?
        UNION ALL
        SELECT id, 'income' as type, amount, note, source, created_at FROM incomes WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, user_id, limit))
    transactions = cursor.fetchall()
    conn.close()
    return transactions

def db_delete_transaction(transaction_id: int, transaction_type: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    table_name = "expenses" if transaction_type == 'expense' else "incomes"
    cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()

def db_reset_all_data(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM incomes WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_main_menu_keyboard():
    keyboard = [
        [KeyboardButton("➕ Thêm"), KeyboardButton("🗑️ Xóa"), KeyboardButton("📈 Báo Cáo")],
        [KeyboardButton("📊 Biểu Đồ"), KeyboardButton("📤 Xuất File")],
        [KeyboardButton("❓ Hướng Dẫn")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False, is_persistent=True)

# --- CÁC HÀM XỬ LÝ BOT ---

def anonymize_name(name: str) -> str:
    if not name:
        return "****"
    if len(name) < 2:
        return "*"
    masked_part = '*' * (len(name) - 1)
    last_char = name[-1]
    return f"{masked_part}{last_char}"

async def post_to_channel(context: ContextTypes.DEFAULT_TYPE, message: str):
    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='Markdown')
        logger.info(f"Đã đăng tin thành công lên kênh {CHANNEL_ID}")
    except Exception as e:
        logger.error(f"Lỗi không thể đăng tin lên kênh {CHANNEL_ID}: {e}. "
                     "Hãy chắc chắn rằng bot là Quản trị viên của kênh và có quyền đăng tin nhắn.")

async def send_or_update_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str = "Đây là menu chính của bạn:"):
    # This function is meant to ensure the main menu is always visible and in a consistent state.
    # It tries to edit if possible, otherwise sends a new message.
    if update.callback_query:
        try:
            # Try to edit the message the callback came from
            await update.callback_query.edit_message_text(message_text, reply_markup=get_main_menu_keyboard())
        except Exception:
            # If editing fails (e.g., message was deleted or too old), send a new message
            await update.callback_query.message.reply_text(message_text, reply_markup=get_main_menu_keyboard())
    elif update.message:
        await update.message.reply_text(message_text, reply_markup=get_main_menu_keyboard())


# Hàm chung để kết thúc hội thoại và dọn dẹp
async def end_current_conversation_and_reset(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str) -> int:
    # Xóa dữ liệu người dùng liên quan đến hội thoại hiện tại
    context.user_data.clear()
    
    # Gửi tin nhắn hủy bỏ/hoàn tất và hiển thị lại menu chính
    await send_or_update_main_menu(update, context, message_text)
    
    return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    init_db()
    return await end_current_conversation_and_reset(update, context, 
        f"Chào mừng bạn đến với Bot Quản lý Tài chính!\n\n"
        f"Sử dụng các nút bên dưới hoặc gõ các lệnh để tương tác.\n"
    )

async def show_main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await end_current_conversation_and_reset(update, context, "Đây là menu chính của bạn:")

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hàm hủy bỏ chung cho CommandHandler /cancel"""
    return await end_current_conversation_and_reset(update, context, 'Đã hủy bỏ thao tác.')

async def cancel_conversation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hàm hủy bỏ chung cho CallbackQueryHandler (nút ❌ Hủy bỏ)"""
    return await end_current_conversation_and_reset(update, context, 'Đã hủy bỏ thao tác.')


async def handle_add_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Ensure current conversation is ended cleanly before starting new one
    context.user_data.clear() # Clear any remnants from previous conversations
    keyboard = [
        [InlineKeyboardButton("Thu nhập (Hôm nay)", callback_data="add_type_income_today")],
        [InlineKeyboardButton("Chi tiêu (Hôm nay)", callback_data="add_type_expense_today")],
        [InlineKeyboardButton("Bổ sung giao dịch", callback_data="add_type_supplement")],
        [InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Bạn muốn thêm loại giao dịch nào?", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Bạn muốn thêm loại giao dịch nào?", reply_markup=reply_markup)
    return CHOOSING_ADD_TYPE

async def choose_add_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice == "add_type_income_today":
        context.user_data['transaction_type'] = "income"
        context.user_data['created_at'] = datetime.datetime.now()
        await query.edit_message_text("Nhập số tiền thu nhập (VD: 5tr, 200k):")
        return CHOOSING_INCOME_AMOUNT
    elif choice == "add_type_expense_today":
        context.user_data['transaction_type'] = "expense"
        context.user_data['created_at'] = datetime.datetime.now()
        await query.edit_message_text("Nhập số tiền chi tiêu (VD: 5tr2, 100k):")
        return CHOOSING_EXPENSE_AMOUNT
    elif choice == "add_type_supplement":
        keyboard = [
            [InlineKeyboardButton("Thu nhập", callback_data="supplement_type_income")],
            [InlineKeyboardButton("Chi tiêu", callback_data="supplement_type_expense")],
            [InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Bạn muốn bổ sung Thu nhập hay Chi tiêu?", reply_markup=reply_markup)
        return CHOOSING_SUPPLEMENT_TYPE
    return await cancel_conversation_callback(update, context)

async def choose_supplement_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    context.user_data.pop('created_at', None) # Clear any pre-existing date for supplement
    if choice == "supplement_type_income":
        context.user_data['transaction_type'] = "income"
        await query.edit_message_text("Nhập số tiền thu nhập (VD: 5tr, 200k):")
        return CHOOSING_INCOME_AMOUNT
    elif choice == "supplement_type_expense":
        context.user_data['transaction_type'] = "expense"
        await query.edit_message_text("Nhập số tiền chi tiêu (VD: 5tr2, 100k):")
        return CHOOSING_EXPENSE_AMOUNT
    return await cancel_conversation_callback(update, context)

async def get_income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount = parse_amount(update.message.text)
        if amount <= 0:
            await update.message.reply_text("Số tiền phải lớn hơn 0. Vui lòng nhập lại:")
            return CHOOSING_INCOME_AMOUNT
        if amount > LARGE_AMOUNT_THRESHOLD:
            context.user_data['amount_to_confirm'] = amount
            keyboard = [
                [InlineKeyboardButton("✅ Đúng vậy", callback_data="confirm_amount_yes")],
                [InlineKeyboardButton("❌ Nhập lại", callback_data="confirm_amount_no")],
                [InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Bạn chắc chắn muốn ghi nhận khoản thu nhập {amount:,.0f} đ chứ? Số tiền này khá lớn.",
                reply_markup=reply_markup
            )
            return CONFIRM_INCOME_AMOUNT
        else:
            context.user_data['amount'] = amount
            await update.message.reply_text("Tuyệt vời! Bây giờ, nhập ghi chú cho khoản thu này:")
            return CHOOSING_INCOME_NOTE
    except (ValueError, TypeError):
        await update.message.reply_text("Số tiền không hợp lệ. Vui lòng nhập lại (VD: 5tr, 200k):")
        return CHOOSING_INCOME_AMOUNT

async def confirm_income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "confirm_amount_yes":
        context.user_data['amount'] = context.user_data.pop('amount_to_confirm')
        await query.edit_message_text("Đã xác nhận. Bây giờ, nhập ghi chú cho khoản thu này:")
        return CHOOSING_INCOME_NOTE
    elif query.data == "confirm_amount_no":
        context.user_data.pop('amount_to_confirm', None)
        await query.edit_message_text("Vui lòng nhập lại số tiền thu nhập:")
        return CHOOSING_INCOME_AMOUNT
    return await cancel_conversation_callback(update, context)

async def get_income_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['note'] = update.message.text
    if 'created_at' in context.user_data: # If date was set (today)
        sources = ["Lương", "Thưởng", "Kinh doanh", "Được cho", "Thu hồi nợ", "Khác"]
        keyboard = [[InlineKeyboardButton(src, callback_data=f"income_source_{src}")] for src in sources]
        keyboard.append([InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Chọn nguồn thu nhập:", reply_markup=reply_markup)
        return CHOOSING_INCOME_SOURCE
    else: # Need to ask for date
        keyboard = [
            [InlineKeyboardButton("Hôm nay", callback_data="date_today_income")],
            [InlineKeyboardButton("Ngày khác", callback_data="date_other_income")],
            [InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Giao dịch này xảy ra vào khi nào?", reply_markup=reply_markup)
        return CHOOSING_INCOME_DATE

async def choose_income_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice == "date_today_income":
        context.user_data['created_at'] = datetime.datetime.now()
        sources = ["Lương", "Thưởng", "Kinh doanh", "Được cho", "Thu hồi nợ", "Khác"]
        keyboard = [[InlineKeyboardButton(src, callback_data=f"income_source_{src}")] for src in sources]
        keyboard.append([InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Chọn nguồn thu nhập:", reply_markup=reply_markup)
        return CHOOSING_INCOME_SOURCE
    elif choice == "date_other_income":
        await query.edit_message_text("Vui lòng nhập ngày của khoản thu nhập (VD: 25/06/2024 hoặc 15/1):")
        return CHOOSING_INCOME_DATE
    return await cancel_conversation_callback(update, context)

async def get_income_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['created_at'] = parse_date(update.message.text)
        sources = ["Lương", "Thưởng", "Kinh doanh", "Được cho", "Thu hồi nợ", "Khác"]
        keyboard = [[InlineKeyboardButton(src, callback_data=f"income_source_{src}")] for src in sources]
        keyboard.append([InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Chọn nguồn thu nhập:", reply_markup=reply_markup)
        return CHOOSING_INCOME_SOURCE
    except ValueError as e:
        await update.message.reply_text(f"{e} Vui lòng nhập lại ngày:")
        return CHOOSING_INCOME_DATE

async def get_income_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    source = query.data.replace("income_source_", "")
    user_id = query.from_user.id
    user_name = query.from_user.full_name
    amount = context.user_data.get('amount')
    note = context.user_data.get('note')
    created_at = context.user_data.get('created_at')

    db_add_income(user_id, amount, source, note, created_at)
    await query.edit_message_text(f"✅ Đã lưu thu nhập: {amount:,.0f} đ - {source} ({note}) vào ngày {created_at.strftime('%d/%m/%Y')}")
    
    anonymized_user_name = anonymize_name(user_name)
    post_message = (
        f"🔔 *Giao dịch mới được ghi nhận*\n\n"
        f"**Loại:** Thu nhập\n"
        f"**Số tiền:** `{amount:,.0f} đ`\n"
        f"**Nguồn:** {source}\n"
        f"**Ghi chú:** {note}\n"
        f"**Ngày:** {created_at.strftime('%d/%m/%Y')}\n\n"
        f"👤 *Người dùng:* `{anonymized_user_name}`"
    )
    await post_to_channel(context, post_message)
    return await end_current_conversation_and_reset(update, context, "Thu nhập đã được ghi nhận thành công.")

async def get_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount = parse_amount(update.message.text)
        if amount <= 0:
            await update.message.reply_text("Số tiền phải lớn hơn 0. Vui lòng nhập lại:")
            return CHOOSING_EXPENSE_AMOUNT
        if amount > LARGE_AMOUNT_THRESHOLD:
            context.user_data['amount_to_confirm'] = amount
            keyboard = [
                [InlineKeyboardButton("✅ Đúng vậy", callback_data="confirm_amount_yes")],
                [InlineKeyboardButton("❌ Nhập lại", callback_data="confirm_amount_no")],
                [InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Bạn chắc chắn muốn ghi nhận khoản chi tiêu {amount:,.0f} đ chứ? Số tiền này khá lớn.",
                reply_markup=reply_markup
            )
            return CONFIRM_EXPENSE_AMOUNT
        else:
            context.user_data['amount'] = amount
            await update.message.reply_text("Tuyệt vời! Bây giờ, nhập ghi chú cho khoản chi này:")
            return CHOOSING_EXPENSE_NOTE
    except (ValueError, TypeError):
        await update.message.reply_text("Số tiền không hợp lệ. Vui lòng nhập lại (VD: 5tr2, 100k):")
        return CHOOSING_EXPENSE_AMOUNT

async def confirm_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "confirm_amount_yes":
        context.user_data['amount'] = context.user_data.pop('amount_to_confirm')
        await query.edit_message_text("Đã xác nhận. Bây giờ, nhập ghi chú cho khoản chi này:")
        return CHOOSING_EXPENSE_NOTE
    elif query.data == "confirm_amount_no":
        context.user_data.pop('amount_to_confirm', None)
        await query.edit_message_text("Vui lòng nhập lại số tiền chi tiêu:")
        return CHOOSING_EXPENSE_AMOUNT
    return await cancel_conversation_callback(update, context)

async def get_expense_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['note'] = update.message.text
    if 'created_at' in context.user_data: # If date was set (today)
        categories = ["Ăn uống", "Di chuyển", "Mua sắm", "Hóa đơn", "Tiết kiệm", "Khác"]
        keyboard = [[InlineKeyboardButton(cat, callback_data=f"expense_category_{cat}")] for cat in categories]
        keyboard.append([InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Chọn danh mục chi tiêu:", reply_markup=reply_markup)
        return CHOOSING_EXPENSE_CATEGORY
    else: # Need to ask for date
        keyboard = [
            [InlineKeyboardButton("Hôm nay", callback_data="date_today_expense")],
            [InlineKeyboardButton("Ngày khác", callback_data="date_other_expense")],
            [InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Giao dịch này xảy ra vào khi nào?", reply_markup=reply_markup)
        return CHOOSING_EXPENSE_DATE

async def choose_expense_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice == "date_today_expense":
        context.user_data['created_at'] = datetime.datetime.now()
        categories = ["Ăn uống", "Di chuyển", "Mua sắm", "Hóa đơn", "Tiết kiệm", "Khác"]
        keyboard = [[InlineKeyboardButton(cat, callback_data=f"expense_category_{cat}")] for cat in categories]
        keyboard.append([InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Chọn danh mục chi tiêu:", reply_markup=reply_markup)
        return CHOOSING_EXPENSE_CATEGORY
    elif choice == "date_other_expense":
        await query.edit_message_text("Vui lòng nhập ngày của khoản chi tiêu (VD: 25/06/2024 hoặc 15/1):")
        return CHOOSING_EXPENSE_DATE
    return await cancel_conversation_callback(update, context)

async def get_expense_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['created_at'] = parse_date(update.message.text)
        categories = ["Ăn uống", "Di chuyển", "Mua sắm", "Hóa đơn", "Tiết kiệm", "Khác"]
        keyboard = [[InlineKeyboardButton(cat, callback_data=f"expense_category_{cat}")] for cat in categories]
        keyboard.append([InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Chọn danh mục chi tiêu:", reply_markup=reply_markup)
        return CHOOSING_EXPENSE_CATEGORY
    except ValueError as e:
        await update.message.reply_text(f"{e} Vui lòng nhập lại ngày:")
        return CHOOSING_EXPENSE_DATE

async def get_expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    category = query.data.replace("expense_category_", "")
    user_id = query.from_user.id
    user_name = query.from_user.full_name
    amount = context.user_data.get('amount')
    note = context.user_data.get('note')
    created_at = context.user_data.get('created_at')

    db_add_expense(user_id, amount, note, category, created_at)
    await query.edit_message_text(f"✅ Đã lưu chi tiêu: {amount:,.0f} đ - {note} ({category}) vào ngày {created_at.strftime('%d/%m/%Y')}")
    
    anonymized_user_name = anonymize_name(user_name)
    post_message = (
        f"🔔 *Giao dịch mới được ghi nhận*\n\n"
        f"**Loại:** Chi tiêu\n"
        f"**Số tiền:** `{amount:,.0f} đ`\n"
        f"**Danh mục:** {category}\n"
        f"**Ghi chú:** {note}\n"
        f"**Ngày:** {created_at.strftime('%d/%m/%Y')}\n\n"
        f"👤 *Người dùng:* `{anonymized_user_name}`"
    )
    await post_to_channel(context, post_message)
    return await end_current_conversation_and_reset(update, context, "Chi tiêu đã được ghi nhận thành công.")

async def handle_delete_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Ensure current conversation is ended cleanly before starting new one
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("Xóa giao dịch", callback_data="delete_action_individual")],
        [InlineKeyboardButton("Đặt lại dữ liệu", callback_data="delete_action_reset_all")],
        [InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Bạn muốn thực hiện thao tác nào?", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Bạn muốn thực hiện thao tác nào?", reply_markup=reply_markup)
    return DELETE_CHOOSING_ACTION

async def choose_delete_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice == "delete_action_individual":
        return await delete_start_individual(update, context)
    elif choice == "delete_action_reset_all":
        keyboard = [
            [InlineKeyboardButton("✅ Có, tôi chắc chắn", callback_data="reset_confirm_1_yes")],
            [InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Bạn có chắc chắn muốn xóa TẤT CẢ dữ liệu tài chính của mình không? "
            "Hành động này không thể hoàn tác.",
            reply_markup=reply_markup
        )
        return RESET_DATA_CONFIRM_STEP1
    return await cancel_conversation_callback(update, context)

async def delete_start_individual(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    transactions = db_get_last_n_transactions(user_id, limit=5)
    if not transactions:
        message_text = "Bạn chưa có giao dịch nào để xóa."
        return await end_current_conversation_and_reset(update, context, message_text)
        
    message_text = "Dưới đây là 5 giao dịch gần nhất của bạn:\n\n"
    keyboard = []
    for i, t in enumerate(transactions):
        trans_id, trans_type_str, amount, note, cat_or_src, created_at_str = t
        trans_type = "Chi tiêu" if trans_type_str == "expense" else "Thu nhập"
        created_at = datetime.datetime.fromisoformat(created_at_str)
        message_text += f"*{i+1}.* [{trans_type}] {amount:,.0f} đ - `{note}` ({cat_or_src}) - {created_at.strftime('%d/%m/%Y')}\n"
        keyboard.append([InlineKeyboardButton(f"Xóa mục {i+1}", callback_data=f"delete_id_{trans_id}_{trans_type_str}")])
    keyboard.append([InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
    return DELETE_INDIVIDUAL_LISTING

async def delete_choose_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split('_')
    trans_id = int(parts[2])
    trans_type = parts[3]
    context.user_data['id_to_delete'] = trans_id
    context.user_data['type_to_delete'] = trans_type
    keyboard = [[InlineKeyboardButton("✅ Xác nhận XÓA", callback_data="confirm_delete_yes")], [InlineKeyboardButton("❌ Hủy", callback_data="cancel_action")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Bạn có chắc chắn muốn xóa giao dịch ID {trans_id} ({'Thu nhập' if trans_type == 'income' else 'Chi tiêu'}) này không?", reply_markup=reply_markup)
    return DELETE_INDIVIDUAL_CONFIRM

async def delete_confirm_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "confirm_delete_yes":
        trans_id = context.user_data.get('id_to_delete')
        trans_type = context.user_data.get('type_to_delete')
        db_delete_transaction(trans_id, trans_type)
        return await end_current_conversation_and_reset(update, context, f"✅ Đã xóa thành công giao dịch ID {trans_id}.")
    else:
        return await end_current_conversation_and_reset(update, context, "Đã hủy bỏ thao tác xóa.")

async def reset_data_confirmation_1_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "reset_confirm_1_yes":
        keyboard = [
            [InlineKeyboardButton("🔥 Xóa TẤT CẢ dữ liệu 🔥", callback_data="reset_confirm_2_yes")],
            [InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Đây là bước xác nhận cuối cùng. Bạn có THỰC SỰ muốn xóa tất cả dữ liệu? "
            "Sau khi xóa, dữ liệu sẽ không thể khôi phục.",
            reply_markup=reply_markup
        )
        return RESET_DATA_CONFIRM_STEP2
    return await cancel_conversation_callback(update, context)

async def reset_data_confirmation_2_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "reset_confirm_2_yes":
        user_id = query.from_user.id
        db_reset_all_data(user_id)
        return await end_current_conversation_and_reset(update, context, "✅ Đã xóa toàn bộ dữ liệu tài chính của bạn thành công.")
    else:
        return await end_current_conversation_and_reset(update, context, "Đã hủy bỏ thao tác đặt lại dữ liệu.")

def get_period_dates(period_choice: str):
    today = datetime.datetime.now()
    start_date, end_date, title_suffix = None, None, ""
    if period_choice == "week":
        start_of_week = today - datetime.timedelta(days=today.weekday())
        start_date = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_of_week + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59)
        title_suffix = f"tuần này ({start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')})"
    elif period_choice == "month":
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = start_date.replace(day=28) + datetime.timedelta(days=4)  # Đảm bảo chuyển sang tháng sau
        end_date = (next_month - datetime.timedelta(days=next_month.day)).replace(hour=23, minute=59, second=59)
        title_suffix = f"tháng này ({today.strftime('%m/%Y')})"
    elif period_choice == "year":
        start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(month=12, day=31, hour=23, minute=59, second=59)
        title_suffix = f"năm nay ({today.year})"
    elif period_choice == "all":
        title_suffix = "tất cả thời gian"
    else:
        return None, None, None
    return start_date, end_date, title_suffix

async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Ensure current conversation is ended cleanly before starting new one
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("Theo tuần", callback_data="report_period_week")],
        [InlineKeyboardButton("Theo tháng", callback_data="report_period_month")],
        [InlineKeyboardButton("Theo năm", callback_data="report_period_year")],
        [InlineKeyboardButton("Toàn bộ thời gian", callback_data="report_period_all")],
        [InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Bạn muốn xem báo cáo theo kỳ nào?", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Bạn muốn xem báo cáo theo kỳ nào?", reply_markup=reply_markup)
    return CHOOSING_REPORT_PERIOD

async def generate_report_for_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_action":
        return await cancel_conversation_callback(update, context)

    period_choice = query.data.replace("report_period_", "")
    user_id = query.from_user.id
    
    message_to_delete = await query.edit_message_text("Đang tạo báo cáo, vui lòng chờ...")

    start_date, end_date, title_suffix = get_period_dates(period_choice)
    income, expense, balance = db_get_combined_summary(user_id, start_date, end_date)
    incomes_grouped = db_list_incomes_grouped(user_id, start_date, end_date)
    expenses_grouped = db_list_expenses_grouped(user_id, start_date, end_date)
    
    report_message = (
        f"===== BÁO CÁO TỔNG HỢP {title_suffix.upper()} =====\n"
        f"📈 Tổng thu nhập : `{income:,.0f} đ`\n"
        f"📉 Tổng chi tiêu : `{expense:,.0f} đ`\n"
        f"💰 Còn lại        : `{balance:,.0f} đ`\n\n"
    )
    if incomes_grouped:
        report_message += "📊 *Thu nhập theo nguồn:*\n"
        for source, total in incomes_grouped:
            report_message += f"- {source}: `{total:,.0f} đ`\n"
    else:
        report_message += "⚠️ Bạn chưa có khoản thu nhập nào trong kỳ này.\n"
    if expenses_grouped:
        report_message += "\n📊 *Chi tiêu theo danh mục:*\n"
        for category, total in expenses_grouped:
            report_message += f"- {category}: `{total:,.0f} đ`\n"
    else:
        report_message += "\n⚠️ Bạn chưa có khoản chi tiêu nào trong kỳ này.\n"
    
    await message_to_delete.delete() 
    
    await query.message.reply_text(report_message, parse_mode='Markdown')
    
    return await end_current_conversation_and_reset(update, context, "Báo cáo đã được tạo thành công.")


async def chart_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Ensure current conversation is ended cleanly before starting new one
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("Theo tuần", callback_data="chart_period_week")],
        [InlineKeyboardButton("Theo tháng", callback_data="chart_period_month")],
        [InlineKeyboardButton("Theo năm", callback_data="chart_period_year")],
        [InlineKeyboardButton("Toàn bộ thời gian", callback_data="chart_period_all")],
        [InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Bạn muốn xem biểu đồ theo kỳ nào?", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Bạn muốn xem biểu đồ theo kỳ nào?", reply_markup=reply_markup)
    return CHOOSING_CHART_PERIOD

async def generate_charts_for_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_action":
        return await cancel_conversation_callback(update, context)

    period_choice = query.data.replace("chart_period_", "")
    user_id = query.from_user.id
    start_date, end_date, title_suffix = get_period_dates(period_choice)
    
    message_to_delete = await query.edit_message_text(f"Đang tạo biểu đồ cho {title_suffix}, vui lòng chờ...")
    
    has_sent_chart = False

    expenses_data = db_list_expenses_grouped(user_id, start_date, end_date)
    if expenses_data:
        has_sent_chart = True
        labels, sizes = [r[0] for r in expenses_data], [r[1] for r in expenses_data]
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
        ax.axis("equal")
        plt.title(f"Phân bổ Chi tiêu ({title_suffix})")
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        await query.message.reply_photo(photo=buf, caption=f"Biểu đồ phân bổ chi tiêu cho {title_suffix}:")
        plt.close(fig)

    expenses, incomes = db_get_monthly_report(user_id, start_date, end_date)
    if expenses or incomes:
        has_sent_chart = True
        months_expenses = [e[0] for e in expenses]
        months_incomes = [i[0] for i in incomes]
        all_months = sorted(list(set(months_expenses + months_incomes)))
        
        exp_dict = {month: amount for month, amount in expenses}
        inc_dict = {month: amount for month, amount in incomes}
        
        exp_values = [exp_dict.get(m, 0) for m in all_months]
        inc_values = [inc_dict.get(m, 0) for m in all_months]

        x = range(len(all_months))
        fig, ax = plt.subplots(figsize=(10, 6))
        bar_width = 0.35
        ax.bar([i - bar_width/2 for i in x], inc_values, width=bar_width, label='Thu nhập')
        ax.bar([i + bar_width/2 for i in x], exp_values, width=bar_width, label='Chi tiêu')
        ax.set_xticks(x)
        ax.set_xticklabels(all_months, rotation=45, ha='right')
        ax.set_ylabel("Số tiền (VND)")
        ax.set_title(f"Tổng hợp Thu nhập & Chi tiêu ({title_suffix})")
        ax.legend()
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        await query.message.reply_photo(photo=buf, caption=f"Biểu đồ tổng hợp thu/chi cho {title_suffix}:")
        plt.close(fig)

    if not has_sent_chart:
        await message_to_delete.edit_text(f"⚠️ Không có dữ liệu để vẽ biểu đồ cho {title_suffix}.")
    else:
        await message_to_delete.delete() 
    
    return await end_current_conversation_and_reset(update, context, "Biểu đồ đã được tạo thành công.")

async def export_file_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Ensure current conversation is ended cleanly before starting new one
    context.user_data.clear()
    df = db_export_data(update.effective_user.id)
    if not df.empty:
        keyboard = [
            [InlineKeyboardButton("Xuất ra CSV", callback_data="export_csv")],
            [InlineKeyboardButton("Xuất ra Excel", callback_data="export_excel")],
            [InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text("Bạn muốn xuất dữ liệu ra định dạng nào?", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Bạn muốn xuất dữ liệu ra định dạng nào?", reply_markup=reply_markup)
        return EXPORT_CHOOSING_FORMAT
    else:
        return await end_current_conversation_and_reset(update, context, "⚠️ Bạn chưa có dữ liệu nào để xuất.")

async def handle_export_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_action":
        return await cancel_conversation_callback(update, context)
    
    df = db_export_data(query.from_user.id)
    if df.empty: # Should not happen if export_file_start worked, but good for safety
        return await end_current_conversation_and_reset(update, context, "⚠️ Không có dữ liệu để xuất file.")
    
    message_to_edit = await query.edit_message_text("Đang chuẩn bị file, vui lòng chờ...")
    file_name_prefix = f'finance_export_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    if query.data == "export_csv":
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig') 
        await query.message.reply_document(document=csv_buffer.getvalue().encode('utf-8-sig'), filename=f'{file_name_prefix}.csv', caption="📁 Dữ liệu của bạn.")
    elif query.data == "export_excel":
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
        await query.message.reply_document(document=excel_buffer.getvalue(), filename=f'{file_name_prefix}.xlsx', caption="📁 Dữ liệu của bạn.")
    
    await message_to_edit.delete()
    return await end_current_conversation_and_reset(update, context, "Dữ liệu đã được xuất thành công.")


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await end_current_conversation_and_reset(
        update, context,
        "**HƯỚNG DẪN SỬ DỤNG BOT**\n\n"
        "➡️ **➕ Thêm:** Ghi nhận thu nhập/chi tiêu.\n"
        "➡️ **🗑️ Xóa:** Xóa giao dịch hoặc đặt lại toàn bộ dữ liệu.\n"
        "➡️ **📈 Báo Cáo:** Xem báo cáo tổng hợp theo kỳ.\n"
        "➡️ **📊 Biểu Đồ:** Xem biểu đồ trực quan theo kỳ.\n"
        "➡️ **📤 Xuất File:** Xuất dữ liệu ra file CSV/Excel.\n"
        "➡️ **/cancel:** Hủy bỏ thao tác hiện tại."
    )


def main() -> None:
    application = Application.builder().token("7869451384:AAFqrNrYigWRIz1B_uEZAlmktbmHci0jS6A").build() # Thay YOUR_BOT_TOKEN bằng token thật

    add_finance_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("them", handle_add_button),
            MessageHandler(filters.Regex("^➕ Thêm$"), handle_add_button)
        ],
        states={
            CHOOSING_ADD_TYPE: [CallbackQueryHandler(choose_add_type_callback, pattern="^add_type_")],
            CHOOSING_SUPPLEMENT_TYPE: [CallbackQueryHandler(choose_supplement_type_callback, pattern="^supplement_type_")],
            CHOOSING_INCOME_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_income_amount)],
            CONFIRM_INCOME_AMOUNT: [CallbackQueryHandler(confirm_income_amount, pattern="^confirm_amount_")],
            CHOOSING_INCOME_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_income_note)],
            CHOOSING_INCOME_DATE: [CallbackQueryHandler(choose_income_date, pattern="^date_"), MessageHandler(filters.TEXT & ~filters.COMMAND, get_income_date_input)],
            CHOOSING_INCOME_SOURCE: [CallbackQueryHandler(get_income_source, pattern="^income_source_")],
            CHOOSING_EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_expense_amount)],
            CONFIRM_EXPENSE_AMOUNT: [CallbackQueryHandler(confirm_expense_amount, pattern="^confirm_amount_")],
            CHOOSING_EXPENSE_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_expense_note)],
            CHOOSING_EXPENSE_DATE: [CallbackQueryHandler(choose_expense_date, pattern="^date_"), MessageHandler(filters.TEXT & ~filters.COMMAND, get_expense_date_input)],
            CHOOSING_EXPENSE_CATEGORY: [CallbackQueryHandler(get_expense_category, pattern="^expense_category_")],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation), CallbackQueryHandler(cancel_conversation_callback, pattern="^cancel_action$")],
        # per_message=True is removed as it causes new convs for each message, not desired here.
        # per_user=True is default, ensuring one active conversation per user.
    )

    delete_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("xoa", handle_delete_button),
            MessageHandler(filters.Regex("^🗑️ Xóa$"), handle_delete_button)
        ],
        states={
            DELETE_CHOOSING_ACTION: [CallbackQueryHandler(choose_delete_action, pattern="^delete_action_")],
            DELETE_INDIVIDUAL_LISTING: [CallbackQueryHandler(delete_choose_item, pattern="^delete_id_")],
            DELETE_INDIVIDUAL_CONFIRM: [CallbackQueryHandler(delete_confirm_action, pattern="^confirm_delete_")],
            RESET_DATA_CONFIRM_STEP1: [CallbackQueryHandler(reset_data_confirmation_1_handler, pattern="^reset_confirm_1_")],
            RESET_DATA_CONFIRM_STEP2: [CallbackQueryHandler(reset_data_confirmation_2_handler, pattern="^reset_confirm_2_")],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation), CallbackQueryHandler(cancel_conversation_callback, pattern="^cancel_action$")],
    )

    report_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("baocao", report_start),
            MessageHandler(filters.Regex("^📈 Báo Cáo$"), report_start)
        ],
        states={CHOOSING_REPORT_PERIOD: [CallbackQueryHandler(generate_report_for_period, pattern="^report_period_|^cancel_action$")]},
        fallbacks=[CommandHandler("cancel", cancel_conversation), CallbackQueryHandler(cancel_conversation_callback, pattern="^cancel_action$")],
    )

    chart_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("bieudo", chart_start),
            MessageHandler(filters.Regex("^📊 Biểu Đồ$"), chart_start)
        ],
        states={CHOOSING_CHART_PERIOD: [CallbackQueryHandler(generate_charts_for_period, pattern="^chart_period_|^cancel_action$")]},
        fallbacks=[CommandHandler("cancel", cancel_conversation), CallbackQueryHandler(cancel_conversation_callback, pattern="^cancel_action$")],
    )

    export_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("xuatfile", export_file_start),
            MessageHandler(filters.Regex("^📤 Xuất File$"), export_file_start)
        ],
        states={
            EXPORT_CHOOSING_FORMAT: [CallbackQueryHandler(handle_export_choice, pattern="^export_|^cancel_action$")]
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation), CallbackQueryHandler(cancel_conversation_callback, pattern="^cancel_action$")],
    )

    application.add_handler(add_finance_conv_handler)
    application.add_handler(delete_conv_handler)
    application.add_handler(report_conv_handler)
    application.add_handler(chart_conv_handler)
    application.add_handler(export_conv_handler)

    # Global CommandHandlers and MessageHandlers should be added AFTER ConversationHandlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", show_main_menu_handler))
    application.add_handler(CommandHandler("huongdan", show_help))
    application.add_handler(MessageHandler(filters.Regex("^❓ Hướng Dẫn$"), show_help))
    
    # Global cancel handler: important to break out of any ConversationHandler
    application.add_handler(CommandHandler("cancel", cancel_conversation))
    
    # This catch-all MessageHandler should be the very last handler to ensure ConversationHandlers get priority.
    # It also ensures that if a user types random text not part of any conversation, they get the main menu.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, show_main_menu_handler))


    print("Bot đang chạy...")
    application.run_polling()

if __name__ == "__main__":
    init_db()
    # Cấu hình font cho matplotlib để hiển thị tiếng Việt
    plt.rcParams['font.family'] = 'DejaVu Sans' # Hoặc 'Arial Unicode MS' nếu có
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif'] # Thêm font hỗ trợ Unicode
    plt.rcParams['axes.unicode_minus'] = False # Giúp hiển thị dấu trừ đúng cách với font Unicode
    main()
