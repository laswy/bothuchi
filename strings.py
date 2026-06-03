# -*- coding: utf-8 -*-
"""
Bothuchi — bilingual string resources.
To add a new language: add an entry to SUPPORTED_LANGS, CURRENCY, and STRINGS.
Amount templates use {amount}/{spent}/{budget} as pre-formatted strings
(via fmt_amount() in main.py) so the currency symbol is handled automatically.
"""

SUPPORTED_LANGS = ('en', 'vi')

CURRENCY = {
    'en': {'symbol': '$',  'position': 'prefix', 'decimals': 2, 'name': 'USD'},
    'vi': {'symbol': 'đ',  'position': 'suffix', 'decimals': 0, 'name': 'VND'},
}

STRINGS: dict[str, dict[str, str]] = {
    'en': {
        # ── Buttons ──────────────────────────────────────────────
        'btn_crypto':       '📈 Crypto',
        'btn_finance':      '💰 Finance',
        'btn_back':         '🏠 Home',
        'btn_portfolio':    '📊 Portfolio',
        'btn_buy':          '➕ Buy',
        'btn_sell':         '➖ Sell',
        'btn_map':          '🔗 Map Token',
        'btn_cimport':      '⬇️ Import',
        'btn_cexport':      '⬆️ Export',
        'btn_fadd':         '💵 Add',
        'btn_fdel':         '🗑️ Delete',
        'btn_budget':       '🎯 Budget',
        'btn_recurring':    '🔁 Recurring',
        'btn_fimport':      '⬇️ Import File',
        'btn_fexport':      '⬆️ Export File',
        'btn_chart':        '📈 Chart',
        'btn_report':       '📋 Report',
        'btn_settings':     '⚙️ Settings',
        # ── Settings ──────────────────────────────────────────────
        'settings_title':       '⚙️ *Settings*',
        'settings_btn_lang':    '🌐 Language',
        'settings_btn_currency':'💱 Currency',
        'settings_btn_dashboard':'🌐 Dashboard',
        # ── Menus ─────────────────────────────────────────────────
        'menu_crypto':      '📈 *Crypto*:',
        'menu_finance':     '💰 *Finance*:',
        'menu_home':        'Main menu:',
        # ── Start / Help / Dashboard ──────────────────────────────
        'start_msg':        (
            '👋 Welcome! Crypto portfolio + Personal finance bot.\n\n'
            '🪪 Your Telegram ID: `{uid}`\n'
            '🌐 HTML Dashboard: `http://localhost:{port}?user_id={uid}`\n\n'
            'Use the keyboard below or /help for guide.'
        ),
        'help_title':       '📖 *QUICK GUIDE*',
        'help_crypto':      (
            '*📈 CRYPTO*\n'
            '• 📊 Portfolio — holdings + P&L\n'
            '• ➕ Buy / ➖ Sell — manual entry\n'
            '• 📈 Chart — price history & allocation\n'
            '• 📋 Report — period summary\n'
            '• 🔗 Map Token — set CoinGecko ID\n'
            '• ⬇️ Import / ⬆️ Export — CSV & Excel\n'
            '• Quick: `buy BTC 0.01 price 70k`\n'
            '• `/cp_add SYMBOL QTY PRICE [note]`\n'
            '• `/cp_sell SYMBOL QTY PRICE [note]`'
        ),
        'help_finance':     (
            '*💰 FINANCE*\n'
            '• 💵 Add — income or expense\n'
            '• 🗑️ Delete — remove transaction\n'
            '• 🎯 Budget — set limits & alerts\n'
            '• 🔁 Recurring — auto monthly entries\n'
            '• 📋 Report / 📈 Chart\n'
            '• ⬇️ Import File / ⬆️ Export File\n'
            '• Quick: `$20 breakfast`, `+$500 salary`'
        ),
        'help_dashboard':   (
            '*🌐 HTML Dashboard*\n'
            '• Filter by date, category, keyword\n'
            '• Add / edit / delete without reload\n'
            '• Import / Export CSV & Excel\n'
            '• 💾 Backup & restore database\n'
            '• Use /dashboard to get link'
        ),
        'help_id':          '🪪 Your ID: `{uid}`',
        'dashboard_title':  '🌐 *HTML Dashboard*',
        'dashboard_id':     '🪪 Telegram ID: `{uid}`',
        'dashboard_link':   '🔗 Link: `{link}`',
        'dashboard_no_secret': '\n⚠️ DASHBOARD\\_SECRET not set — add to .env',
        'dashboard_secret': '\n🔑 Token: `{secret}`',
        'dashboard_features': (
            'Features:\n'
            '• 📊 Portfolio & finance overview\n'
            '• 🔍 Filter by date, category, keyword\n'
            '• ✏️ Add / edit / delete transactions\n'
            '• 📥 Import / 📤 Export CSV & Excel\n'
            '• 💾 Backup & restore database'
        ),
        # ── Language ──────────────────────────────────────────────
        'lang_choose':      '🌐 Choose language / Chọn ngôn ngữ:',
        'lang_set_en':      '✅ Language set to English.',
        'lang_set_vi':      '✅ Đã chuyển sang Tiếng Việt.',
        # ── Currency ──────────────────────────────────────────────
        'currency_choose':  '💱 Choose your preferred currency:',
        'currency_set_vnd': '✅ Currency set to VND (đ).',
        'currency_set_usd': '✅ Currency set to USD ($).',
        # ── Rate limit ────────────────────────────────────────────
        'rate_limit':       '⏳ Too many requests. Wait {sec}s and try again.',
        # ── Crypto messages ───────────────────────────────────────
        'cp_buy_help':      '➕ *BUY*: `/cp_add SYMBOL QTY PRICE [note]`\nEx: `/cp_add BTC 0.01 70000`\nOr type: `buy BTC 0.01 price 70k`',
        'cp_sell_help':     '➖ *SELL*: `/cp_sell SYMBOL QTY PRICE [note]`\nEx: `/cp_sell SOL 10 87`\nOr type: `sell SOL all price 100`',
        'cp_map_help':      '🔗 *MAP TOKEN*: `/cp_map SYMBOL CG_ID`\nEx: `/cp_map ATOM cosmos`',
        'cp_no_export':     'No trades to export.',
        'cp_no_data':       'No data yet.\nError: {e}',
        'cp_add_usage':     'Usage: /cp_add SYMBOL QTY PRICE [note]\nEx: /cp_add BTC 0.01 70000',
        'cp_sell_usage':    'Usage: /cp_sell SYMBOL QTY PRICE [note]\nEx: /cp_sell SOL 10 87',
        'cp_map_usage':     'Usage: /cp_map SYMBOL CG_ID',
        'cp_invalid_num':   'Invalid quantity or price.',
        'cp_positive':      'Quantity and price must be > 0.',
        'cp_oversell':      '⚠️ You only hold {held:g} {symbol}, cannot sell {qty:g}.',
        'cp_mapped':        '✅ Mapped {symbol} → {cg_id}',
        'cp_import_hint':   'Send a CSV or Excel file then reply `/cp_import`.',
        'cp_processing':    '📥 Processing file...',
        'cp_imported':      '✅ Imported {ok} trades, {fail} errors.',
        # ── Finance messages ──────────────────────────────────────
        'fin_add_type':         'What type of transaction?',
        'fin_enter_amount':     'Enter amount (e.g. $20, 5k, 1.5m):',
        'fin_invalid_amount':   'Invalid. Try again (e.g. $20, 5k, 1.5m):',
        'fin_amount_gt0':       'Amount must be > 0:',
        'fin_confirm_large':    'Confirm {type} {amount}? (large amount)',
        'fin_enter_note':       'Enter a note:',
        'fin_choose_source':    'Choose income source:',
        'fin_choose_cat':       'Choose expense category:',
        'fin_choose_date':      'Transaction date?',
        'fin_invalid_date':     '{e} Enter date again:',
        'fin_saved':            'Transaction recorded.',
        'fin_budget_over':      '🚨 *OVER BUDGET* {cat}: {spent}/{budget}',
        'fin_budget_near':      '⚠️ *NEAR BUDGET* {cat}: {spent}/{budget} (≥90%)',
        # ── Budget ────────────────────────────────────────────────
        'budget_title':         '🎯 *Budget*:',
        'budget_set_btn':       '🎯 Set budget',
        'budget_view_btn':      '📋 View budgets',
        'budget_set_hint':      '📝 Use:\n`/budget <Category> <Amount>`\nEx: `/budget Food 300`',
        'budget_empty':         'No budgets set. Use /budget to add one.',
        'budget_list_title':    '🎯 *Current Budgets:*',
        'budget_usage':         'Usage: /budget <Category> <Amount>\nEx: /budget Food 500',
        'budget_saved':         '✅ Budget *{cat}*: `{amount}` /month',
        'budget_invalid':       'Invalid amount. Try: /budget Food 500',
        'budget_del_usage':     'Usage: /budget_del <Category>',
        'budget_deleted':       '🗑️ Deleted budget *{cat}*',
        'budget_none':          'No budgets set.',
        # ── Recurring ─────────────────────────────────────────────
        'recur_title':          '🔁 *Recurring transactions* ({n}):',
        'recur_empty':          '🔁 *Recurring transactions*\nNone yet. Tap ➕ to add.',
        'recur_add_type':       '💰 Income',
        'recur_add_expense':    '💸 Expense',
        'recur_add_amount':     '💵 Enter amount (e.g. $20, 5k):',
        'recur_invalid_amt':    '⚠️ Invalid amount. Try again (e.g. $250):',
        'recur_pick_income':    '📌 Choose income source:',
        'recur_pick_cat':       '📌 Choose expense category:',
        'recur_pick_day':       '📅 Which day of the month? Enter number (1–28):',
        'recur_invalid_day':    '⚠️ Enter a number from 1 to 28:',
        'recur_pick_freq':      'How often?',
        'recur_monthly':        '🔁 Monthly',
        'recur_yearly':         '📅 Once a year',
        'recur_add_month':      'Which month?',
        'recur_saved':          '✅ Recurring entry saved.',
        'recur_updated_amt':    '✅ Updated amount → `{amount}`',
        'recur_updated_note':   '✅ Updated note → *{note}*',
        'recur_pick_day2':      'Day {day} — frequency?',
        'recur_freq_monthly':   'monthly',
        'recur_freq_yearly':    'yr/M{month}',
        # ── Export / Import ───────────────────────────────────────
        'export_choose':        'Export format?',
        'import_only_csv':      '⚠️ Only .csv or .xlsx supported. Try again.',
        'import_processing':    '⏳ Processing file...',
        'import_done':          '✅ Imported {ok} rows, {fail} errors.',
        'no_import_file':       'No file to import.',
        # ── Finance add flow ──────────────────────────────────────
        'fin_btn_income_today':  'Income (Today)',
        'fin_btn_expense_today': 'Expense (Today)',
        'fin_btn_supplement':    'Past transaction',
        'fin_btn_cancel':        '❌ Cancel',
        'fin_btn_income':        'Income',
        'fin_btn_expense':       'Expense',
        'fin_supp_title':        'Income or Expense?',
        'fin_enter_income_amt':  'Enter income amount (e.g. $20, 5k):',
        'fin_enter_expense_amt': 'Enter expense amount (e.g. $20, 5k):',
        'fin_btn_yes':           '✅ Correct',
        'fin_btn_retype':        '❌ Enter again',
        'fin_confirmed_note':    '✅ Confirmed. Enter note:',
        'fin_retype_amount':     'Enter amount again:',
        'fin_enter_income_note': 'Enter a note for this income:',
        'fin_enter_expense_note':'Enter a note for this expense:',
        'fin_btn_today':         'Today',
        'fin_btn_other_date':    'Other date',
        'fin_enter_date':        'Enter date (e.g. 25/06/2024 or 15/1):',
        'fin_saved_income':      '✅ Income: {amount} — {source} ({note}) on {date}',
        'fin_saved_expense':     '✅ Expense: {amount} — {note} ({category}) on {date}',
        # ── Delete flow ───────────────────────────────────────────
        'del_crypto_q':          '🗑️ Delete Crypto data?',
        'del_finance_q':         'What would you like to do?',
        'del_btn_del_trade':     'Delete transaction',
        'del_btn_del_crypto':    'Delete Crypto trade',
        'del_btn_reset_all':     'Reset all finance',
        'del_btn_reset_crypto':  'Reset all Crypto',
        'del_no_crypto':         'No Crypto trades to delete.',
        'del_no_finance':        'No transactions to delete.',
        'del_recent_crypto':     '5 recent Crypto trades:\n\n',
        'del_recent_finance':    '5 recent transactions:\n\n',
        'del_income_label':      'Income',
        'del_expense_label':     'Expense',
        'del_confirm_reset_all': 'Delete ALL finance data? Cannot undo.',
        'del_confirm_reset_crypto': 'Delete ALL Crypto trades? Cannot undo.',
        'del_final_all':         'Final confirm: DELETE all data? Cannot recover.',
        'del_final_crypto':      'Final confirm: DELETE all Crypto? Cannot recover.',
        'del_item_q':            'Delete transaction {label}?',
        'del_btn_confirm_del':   '✅ Confirm DELETE',
        'del_btn_sure':          '✅ Yes, sure',
        'del_btn_cancel':        '❌ Cancel',
        'del_btn_del_all':       '🔥 DELETE ALL',
        'del_btn_del_all_crypto':'🔥 DELETE ALL CRYPTO',
        'del_done':              '✅ Transaction deleted.',
        'del_done_crypto':       '✅ Crypto trade deleted.',
        'del_done_all':          '✅ All finance data deleted.',
        'del_done_all_crypto':   '✅ All Crypto data deleted.',
        'del_cancelled':         'Cancelled.',
        # ── Report flow ───────────────────────────────────────────
        'report_choose_period':  '📊 *CHOOSE REPORT PERIOD*\nSelect time range:',
        'report_loading':        '⏳ Generating report...',
        'report_overview':       '💼 *OVERVIEW*\n',
        'report_income_line':    '┃ 📈 Income: `{amount}`\n',
        'report_expense_line':   '┃ 📉 Expense: `{amount}`\n',
        'report_balance_line':   '┃ 💰 Balance: `{amount}`\n\n',
        'report_income_detail':  '💵 *INCOME DETAIL*\n',
        'report_expense_detail': '💸 *EXPENSE DETAIL*\n',
        'report_no_income':      '⚠️ *No income this period*\n\n',
        'report_no_expense':     '✅ *No expenses this period*\n\n',
        'report_budget_title':   '⚠️ *BUDGET*\n',
        'report_budget_over_lbl':'🚨 OVER',
        'report_budget_near_lbl':'⚠️ NEAR',
        'report_eval_positive':  '📊 *EVALUATION*: Positive! 🎉',
        'report_eval_balanced':  '📊 *EVALUATION*: Balanced ⚖️',
        'report_eval_negative':  '📊 *EVALUATION*: Review spending ⚠️',
        'report_done':           '✅ Report complete.',
        # ── Chart flow ────────────────────────────────────────────
        'chart_choose_period':   '📊 View chart for which period?',
        'chart_loading':         '⏳ Generating chart {period}...',
        'chart_no_data':         'No data in {period}.',
        'chart_done':            '✅ Chart complete.',
        'pick_month':            '📆 Choose month:',
        'pick_year':             '🗓️ Choose year:',
        # ── Period picker buttons ─────────────────────────────────
        'period_btn_week':       '📅 This week',
        'period_btn_month':      '📆 Choose month',
        'period_btn_year':       '🗓️ Choose year',
        'period_btn_all':        '⏰ All time',
        'period_btn_cancel':     '❌ Cancel',
        'period_btn_back':       '↩️ Back',
        'period_week_suffix':    'this week ({start} - {end})',
        'period_month_suffix':   'this month ({date})',
        'period_year_suffix':    'this year ({year})',
        'period_all_suffix':     'all time',
        'period_m_suffix':       'month {m}/{y}',
        'period_y_suffix':       'year {y}',
        # ── Chart image labels ────────────────────────────────────
        'chart_expense_dist':    'Expense Distribution',
        'chart_income_label':    'Income',
        'chart_expense_label':   'Expense',
        'chart_incexp_title':    'Income vs Expense',
        'chart_total_income':    'Total income',
        'chart_total_expense':   'Total expense',
        'chart_balance':         'Balance',
        'chart_heatmap_day':     'Daily Spending Heatmap',
        'chart_heatmap_month':   'Monthly Spending Heatmap',
        # ── Export / Import (extended) ────────────────────────────
        'export_no_data':        '⚠️ No data to export.',
        'export_btn_csv':        'Export CSV',
        'export_btn_excel':      'Export Excel',
        'export_no_data2':       '⚠️ No data.',
        'export_loading':        '⏳ Preparing file...',
        'export_done':           '✅ Export complete.',
        'import_hint':           (
            '📥 *IMPORT FINANCE DATA*\n\n'
            'File needs 5 columns:\n`Type` | `Amount` | `Note` | `Category/Source` | `Date`\n\n'
            'Example:\n`expense | 50000 | Lunch | Food | 2024-07-28`\n\n'
            'Send a .csv or .xlsx file now.'
        ),
        'import_done_full':      '✅ Imported {total}:\n- {income} income\n- {expense} expense\n- {fail} skipped',
        'import_file_err':       '❌ File error: {e}',
        # ── Budget list ───────────────────────────────────────────
        'budget_list_title_full':'📋 *THIS MONTH\'S BUDGET*',
        'budget_status_over':    '🚨 OVER',
        'budget_status_near':    '⚠️ NEAR',
        'budget_status_ok':      '✅ OK',
        # ── Recurring (extended) ─────────────────────────────────
        'recur_back':            '◀️ Back',
        'recur_btn_del':         '✅ Delete',
        'recur_not_found':       'Not found.',
        'recur_del_q':           'Delete recurring:\n*{label}* — `{amount}` on day {day} {freq}?',
        # ── NLP auto-transaction ──────────────────────────────────
        'nlp_income_saved':      '✅ *Income*: `{amount}`\n• Source: *{cat}*\n• Note: _{note}_\n• Date: {date}',
        'nlp_expense_saved':     '✅ *Expense*: `{amount}`\n• Category: *{cat}*\n• Note: _{note}_\n• Date: {date}',
        # ── Error handler ─────────────────────────────────────────
        'error_generic':         '⚠️ An error occurred. Please try again.',
        # ── Delete ────────────────────────────────────────────────
        'delete_title':         '🗑️ *Delete*',
        # ── General ───────────────────────────────────────────────
        'cancel':               '❌ Cancel',
        'close':                '❌ Close',
        'no_data':              'No data.',
        'not_understood':       'Command not recognized. Use the menu buttons below:',
        'theme_changed':        '✅ Theme: {name}. Open Portfolio to see result.',
    },

    'vi': {
        # ── Buttons ──────────────────────────────────────────────
        'btn_crypto':       '📈 Crypto',
        'btn_finance':      '💰 Thu Chi',
        'btn_back':         '🔙 Trang Chủ',
        'btn_portfolio':    '📊 Danh Mục',
        'btn_buy':          '➕ Mua',
        'btn_sell':         '➖ Bán',
        'btn_map':          '🔗 Map Token',
        'btn_cimport':      '⬇️ Nhập',
        'btn_cexport':      '⬆️ Xuất',
        'btn_fadd':         '💵 Thêm',
        'btn_fdel':         '🗑️ Xóa',
        'btn_budget':       '🎯 Ngân Sách',
        'btn_recurring':    '🔁 Định Kỳ',
        'btn_fimport':      '⬇️ Nhập File',
        'btn_fexport':      '⬆️ Xuất File',
        'btn_chart':        '📈 Biểu Đồ',
        'btn_report':       '📋 Báo Cáo',
        'btn_settings':     '⚙️ Cài Đặt',
        # ── Settings ──────────────────────────────────────────────
        'settings_title':       '⚙️ *Cài Đặt*',
        'settings_btn_lang':    '🌐 Ngôn Ngữ',
        'settings_btn_currency':'💱 Tiền Tệ',
        'settings_btn_dashboard':'🌐 Dashboard',
        # ── Menus ─────────────────────────────────────────────────
        'menu_crypto':      '📈 *Crypto*:',
        'menu_finance':     '💰 *Thu Chi*:',
        'menu_home':        'Menu chính:',
        # ── Start / Help / Dashboard ──────────────────────────────
        'start_msg':        (
            '👋 Chào mừng! Bot quản lý *Crypto* + *Thu Chi* tài chính.\n\n'
            '🪪 Telegram ID của bạn: `{uid}`\n'
            '🌐 HTML Dashboard: `http://localhost:{port}?user_id={uid}`\n\n'
            'Dùng bàn phím bên dưới hoặc /help để xem hướng dẫn.'
        ),
        'help_title':       '📖 *HƯỚNG DẪN NHANH*',
        'help_crypto':      (
            '*📈 CRYPTO*\n'
            '• 📊 Danh Mục — portfolio + lợi nhuận\n'
            '• ➕ Mua / ➖ Bán — nhập lệnh thủ công\n'
            '• 📈 Biểu Đồ — giá lịch sử & cơ cấu\n'
            '• 📋 Báo Cáo — tóm tắt theo kỳ\n'
            '• 🔗 Map Token — gắn CoinGecko ID\n'
            '• ⬇️ Nhập / ⬆️ Xuất — CSV & Excel\n'
            '• Lệnh nhanh: `mua BTC 0.01 giá 70k`\n'
            '• `/cp_add SYMBOL SL GIA [note]`\n'
            '• `/cp_sell SYMBOL SL GIA [note]`'
        ),
        'help_finance':     (
            '*💰 THU CHI*\n'
            '• 💵 Thêm — thu nhập hoặc chi tiêu\n'
            '• 🗑️ Xóa — xóa giao dịch\n'
            '• 🎯 Ngân Sách — đặt hạn mức & cảnh báo\n'
            '• 🔁 Định Kỳ — thu/chi tự động hàng tháng\n'
            '• 📋 Báo Cáo / 📈 Biểu Đồ\n'
            '• ⬇️ Nhập File / ⬆️ Xuất File\n'
            '• Lệnh nhanh: `20k ăn sáng`, `+500k lương`'
        ),
        'help_dashboard':   (
            '*🌐 HTML Dashboard*\n'
            '• Lọc thu chi theo ngày, danh mục, từ khoá\n'
            '• Thêm / sửa / xóa không cần reload\n'
            '• Import / Export CSV & Excel\n'
            '• 💾 Backup & restore database\n'
            '• Dùng /dashboard để lấy link'
        ),
        'help_id':          '🪪 ID của bạn: `{uid}`',
        'dashboard_title':  '🌐 *HTML Dashboard*',
        'dashboard_id':     '🪪 Telegram ID: `{uid}`',
        'dashboard_link':   '🔗 Link: `{link}`',
        'dashboard_no_secret': '\n⚠️ Chưa đặt DASHBOARD\\_SECRET — nên thêm vào .env',
        'dashboard_secret': '\n🔑 Token: `{secret}`',
        'dashboard_features': (
            'Tính năng:\n'
            '• 📊 Xem portfolio crypto & thu chi\n'
            '• 🔍 Lọc theo ngày, danh mục, từ khoá\n'
            '• ✏️ Thêm / sửa / xóa giao dịch\n'
            '• 📥 Import / 📤 Export CSV & Excel\n'
            '• 💾 Backup & restore database'
        ),
        # ── Language ──────────────────────────────────────────────
        'lang_choose':      '🌐 Choose language / Chọn ngôn ngữ:',
        'lang_set_en':      '✅ Language set to English.',
        'lang_set_vi':      '✅ Đã chuyển sang Tiếng Việt.',
        # ── Currency ──────────────────────────────────────────────
        'currency_choose':  '💱 Chọn đơn vị tiền tệ bạn muốn:',
        'currency_set_vnd': '✅ Đã chuyển sang VND (đ).',
        'currency_set_usd': '✅ Đã chuyển sang USD ($).',
        # ── Rate limit ────────────────────────────────────────────
        'rate_limit':       '⏳ Gửi lệnh quá nhanh. Chờ {sec}s rồi thử lại.',
        # ── Crypto messages ───────────────────────────────────────
        'cp_buy_help':      '➕ *MUA*: `/cp_add SYMBOL SL GIA [note]`\nVD: `/cp_add BTC 0.01 70000`\nHoặc gõ: `mua BTC 0.01 giá 70k`',
        'cp_sell_help':     '➖ *BÁN*: `/cp_sell SYMBOL SL GIA [note]`\nVD: `/cp_sell SOL 10 87`\nHoặc gõ: `bán SOL tất cả giá 100`',
        'cp_map_help':      '🔗 *MAP TOKEN*: `/cp_map SYMBOL CG_ID`\nVD: `/cp_map ATOM cosmos`',
        'cp_no_export':     'Chưa có giao dịch để xuất.',
        'cp_no_data':       'Chưa có dữ liệu.\nLỗi: {e}',
        'cp_add_usage':     'Cú pháp: /cp_add SYMBOL SL GIA [note]\nVD: /cp_add BTC 0.01 70000',
        'cp_sell_usage':    'Cú pháp: /cp_sell SYMBOL SL GIA [note]\nVD: /cp_sell SOL 10 87',
        'cp_map_usage':     'Cú pháp: /cp_map SYMBOL CG_ID',
        'cp_invalid_num':   'Số lượng & giá không hợp lệ.',
        'cp_positive':      'Số lượng & giá phải > 0.',
        'cp_oversell':      '⚠️ Bạn chỉ đang giữ {held:g} {symbol}, không thể bán {qty:g}.',
        'cp_mapped':        '✅ Đã map {symbol} → {cg_id}',
        'cp_import_hint':   'Gửi file CSV hoặc Excel rồi reply `/cp_import`.',
        'cp_processing':    '📥 Đang xử lý file...',
        'cp_imported':      '✅ Đã nhập {ok} giao dịch, lỗi {fail}.',
        # ── Finance messages ──────────────────────────────────────
        'fin_add_type':         'Bạn muốn thêm loại giao dịch nào?',
        'fin_enter_amount':     'Nhập số tiền (VD: 20k, 5tr, 200000):',
        'fin_invalid_amount':   'Không hợp lệ. Thử lại (VD: 5tr, 200k):',
        'fin_amount_gt0':       'Số tiền phải > 0:',
        'fin_confirm_large':    'Chắc chắn {type} {amount}? (số lớn)',
        'fin_enter_note':       'Nhập ghi chú:',
        'fin_choose_source':    'Chọn nguồn thu nhập:',
        'fin_choose_cat':       'Chọn danh mục chi tiêu:',
        'fin_choose_date':      'Giao dịch vào ngày nào?',
        'fin_invalid_date':     '{e} Nhập lại ngày:',
        'fin_saved':            'Giao dịch đã ghi nhận.',
        'fin_budget_over':      '🚨 *VƯỢT NGÂN SÁCH* {cat}: {spent}/{budget}',
        'fin_budget_near':      '⚠️ *GẦN HẾT NGÂN SÁCH* {cat}: {spent}/{budget} (≥90%)',
        # ── Budget ────────────────────────────────────────────────
        'budget_title':         '🎯 *Ngân Sách*:',
        'budget_set_btn':       '🎯 Đặt ngân sách',
        'budget_view_btn':      '📋 Xem ngân sách',
        'budget_set_hint':      '📝 Dùng lệnh:\n`/ngansach <Danh mục> <Số tiền>`\nVD: `/ngansach Ăn uống 3000000`',
        'budget_empty':         'Chưa đặt ngân sách nào. Dùng /ngansach để đặt.',
        'budget_list_title':    '🎯 *Ngân Sách Hiện Tại:*',
        'budget_usage':         'Cú pháp: /ngansach <Danh mục> <Số tiền>\nVD: /ngansach Ăn uống 3tr',
        'budget_saved':         '✅ Đặt ngân sách *{cat}*: `{amount}`/tháng',
        'budget_invalid':       'Số tiền không hợp lệ. Thử: /ngansach Ăn uống 3tr',
        'budget_del_usage':     'Cú pháp: /xoa_ngansach <Danh mục>',
        'budget_deleted':       '🗑️ Đã xóa ngân sách *{cat}*',
        'budget_none':          'Chưa đặt ngân sách nào.',
        # ── Recurring ─────────────────────────────────────────────
        'recur_title':          '🔁 *Giao dịch định kỳ* ({n} khoản):',
        'recur_empty':          '🔁 *Giao dịch định kỳ*\nChưa có khoản nào. Nhấn ➕ để thêm.',
        'recur_add_type':       '💰 Thu nhập',
        'recur_add_expense':    '💸 Chi tiêu',
        'recur_add_amount':     '💵 Nhập số tiền (VD: 5tr, 200k):',
        'recur_invalid_amt':    '⚠️ Số tiền không hợp lệ. Nhập lại (VD: 250k):',
        'recur_pick_income':    '📌 Chọn nguồn thu nhập:',
        'recur_pick_cat':       '📌 Chọn danh mục chi tiêu:',
        'recur_pick_day':       '📅 Ngày mấy trong tháng sẽ tự ghi? Nhập số (1–28):',
        'recur_invalid_day':    '⚠️ Nhập số từ 1 đến 28:',
        'recur_pick_freq':      'Lặp lại như thế nào?',
        'recur_monthly':        '🔁 Hàng tháng',
        'recur_yearly':         '📅 1 lần/năm',
        'recur_add_month':      'Tháng mấy?',
        'recur_saved':          '✅ Đã lưu giao dịch định kỳ.',
        'recur_updated_amt':    '✅ Đã cập nhật số tiền → `{amount}`',
        'recur_updated_note':   '✅ Đã cập nhật ghi chú → *{note}*',
        'recur_pick_day2':      'Ngày {day} — tần suất?',
        'recur_freq_monthly':   'hàng tháng',
        'recur_freq_yearly':    'năm/T{month}',
        # ── Export / Import ───────────────────────────────────────
        'export_choose':        'Xuất dữ liệu ra định dạng nào?',
        'import_only_csv':      '⚠️ Chỉ hỗ trợ .csv hoặc .xlsx. Thử lại.',
        'import_processing':    '⏳ Đang xử lý file...',
        'import_done':          '✅ Đã nhập {ok} dòng, lỗi {fail}.',
        'no_import_file':       'Không có file để nhập.',
        # ── Finance add flow ──────────────────────────────────────
        'fin_btn_income_today':  'Thu nhập (Hôm nay)',
        'fin_btn_expense_today': 'Chi tiêu (Hôm nay)',
        'fin_btn_supplement':    'Bổ sung giao dịch',
        'fin_btn_cancel':        '❌ Hủy bỏ',
        'fin_btn_income':        'Thu nhập',
        'fin_btn_expense':       'Chi tiêu',
        'fin_supp_title':        'Bổ sung Thu nhập hay Chi tiêu?',
        'fin_enter_income_amt':  'Nhập số tiền thu nhập (VD: 5tr, 200k):',
        'fin_enter_expense_amt': 'Nhập số tiền chi tiêu (VD: 5tr, 100k):',
        'fin_btn_yes':           '✅ Đúng vậy',
        'fin_btn_retype':        '❌ Nhập lại',
        'fin_confirmed_note':    'Đã xác nhận. Nhập ghi chú:',
        'fin_retype_amount':     'Nhập lại số tiền:',
        'fin_enter_income_note': 'Nhập ghi chú cho khoản thu:',
        'fin_enter_expense_note':'Nhập ghi chú cho khoản chi:',
        'fin_btn_today':         'Hôm nay',
        'fin_btn_other_date':    'Ngày khác',
        'fin_enter_date':        'Nhập ngày (VD: 25/06/2024 hoặc 15/1):',
        'fin_saved_income':      '✅ Thu nhập: {amount} — {source} ({note}) ngày {date}',
        'fin_saved_expense':     '✅ Chi tiêu: {amount} — {note} ({category}) ngày {date}',
        # ── Delete flow ───────────────────────────────────────────
        'del_crypto_q':          '🗑️ Xóa dữ liệu Crypto?',
        'del_finance_q':         'Bạn muốn làm gì?',
        'del_btn_del_trade':     'Xóa giao dịch',
        'del_btn_del_crypto':    'Xóa giao dịch Crypto',
        'del_btn_reset_all':     'Đặt lại toàn bộ',
        'del_btn_reset_crypto':  'Đặt lại toàn bộ Crypto',
        'del_no_crypto':         'Chưa có giao dịch Crypto để xóa.',
        'del_no_finance':        'Chưa có giao dịch để xóa.',
        'del_recent_crypto':     '5 giao dịch Crypto gần nhất:\n\n',
        'del_recent_finance':    '5 giao dịch gần nhất:\n\n',
        'del_income_label':      'Thu nhập',
        'del_expense_label':     'Chi tiêu',
        'del_confirm_reset_all': 'Xóa TẤT CẢ dữ liệu tài chính? Không thể hoàn tác.',
        'del_confirm_reset_crypto': 'Xóa TẤT CẢ giao dịch Crypto? Không thể hoàn tác.',
        'del_final_all':         'Xác nhận cuối: XÓA toàn bộ dữ liệu? Không thể khôi phục.',
        'del_final_crypto':      'Xác nhận cuối: XÓA toàn bộ Crypto? Không thể khôi phục.',
        'del_item_q':            'Xóa giao dịch {label}?',
        'del_btn_confirm_del':   '✅ Xác nhận XÓA',
        'del_btn_sure':          '✅ Có, chắc chắn',
        'del_btn_cancel':        '❌ Hủy bỏ',
        'del_btn_del_all':       '🔥 XÓA TẤT CẢ',
        'del_btn_del_all_crypto':'🔥 XÓA TẤT CẢ CRYPTO',
        'del_done':              '✅ Đã xóa giao dịch.',
        'del_done_crypto':       '✅ Đã xóa giao dịch Crypto.',
        'del_done_all':          '✅ Đã xóa toàn bộ dữ liệu tài chính.',
        'del_done_all_crypto':   '✅ Đã xóa toàn bộ dữ liệu Crypto.',
        'del_cancelled':         'Đã hủy.',
        # ── Report flow ───────────────────────────────────────────
        'report_choose_period':  '📊 *CHỌN KỲ BÁO CÁO*\nChọn khoảng thời gian:',
        'report_loading':        '⏳ Đang tạo báo cáo...',
        'report_overview':       '💼 *TỔNG QUAN*\n',
        'report_income_line':    '┃ 📈 Thu nhập: `{amount}`\n',
        'report_expense_line':   '┃ 📉 Chi tiêu: `{amount}`\n',
        'report_balance_line':   '┃ 💰 Số dư: `{amount}`\n\n',
        'report_income_detail':  '💵 *CHI TIẾT THU NHẬP*\n',
        'report_expense_detail': '💸 *CHI TIẾT CHI TIÊU*\n',
        'report_no_income':      '⚠️ *Chưa có thu nhập trong kỳ*\n\n',
        'report_no_expense':     '✅ *Không có chi tiêu trong kỳ*\n\n',
        'report_budget_title':   '⚠️ *NGÂN SÁCH*\n',
        'report_budget_over_lbl':'🚨 VƯỢT',
        'report_budget_near_lbl':'⚠️ GẦN',
        'report_eval_positive':  '📊 *ĐÁNH GIÁ*: Tích cực! 🎉',
        'report_eval_balanced':  '📊 *ĐÁNH GIÁ*: Cân bằng ⚖️',
        'report_eval_negative':  '📊 *ĐÁNH GIÁ*: Cần cân nhắc ⚠️',
        'report_done':           '✅ Báo cáo hoàn tất.',
        # ── Chart flow ────────────────────────────────────────────
        'chart_choose_period':   '📊 Xem biểu đồ theo kỳ nào?',
        'chart_loading':         '⏳ Đang tạo biểu đồ {period}...',
        'chart_no_data':         'Không có dữ liệu trong {period}.',
        'chart_done':            '✅ Biểu đồ hoàn tất.',
        'pick_month':            '📆 Chọn tháng:',
        'pick_year':             '🗓️ Chọn năm:',
        # ── Period picker buttons ─────────────────────────────────
        'period_btn_week':       '📅 Tuần này',
        'period_btn_month':      '📆 Chọn tháng',
        'period_btn_year':       '🗓️ Chọn năm',
        'period_btn_all':        '⏰ Toàn bộ',
        'period_btn_cancel':     '❌ Hủy bỏ',
        'period_btn_back':       '↩️ Quay lại',
        'period_week_suffix':    'tuần này ({start} - {end})',
        'period_month_suffix':   'tháng này ({date})',
        'period_year_suffix':    'năm nay ({year})',
        'period_all_suffix':     'tất cả thời gian',
        'period_m_suffix':       'tháng {m}/{y}',
        'period_y_suffix':       'năm {y}',
        # ── Chart image labels ────────────────────────────────────
        'chart_expense_dist':    'Phân bổ Chi tiêu',
        'chart_income_label':    'Thu nhập',
        'chart_expense_label':   'Chi tiêu',
        'chart_incexp_title':    'Thu Chi',
        'chart_total_income':    'Tổng thu',
        'chart_total_expense':   'Tổng chi',
        'chart_balance':         'Cân đối',
        'chart_heatmap_day':     'Heatmap Chi Tiêu Theo Ngày',
        'chart_heatmap_month':   'Heatmap Chi Tiêu Theo Tháng',
        # ── Export / Import (extended) ────────────────────────────
        'export_no_data':        '⚠️ Chưa có dữ liệu để xuất.',
        'export_btn_csv':        'Xuất ra CSV',
        'export_btn_excel':      'Xuất ra Excel',
        'export_no_data2':       '⚠️ Không có dữ liệu.',
        'export_loading':        '⏳ Đang chuẩn bị file...',
        'export_done':           '✅ Xuất file hoàn tất.',
        'import_hint':           (
            '📥 *NHẬP DỮ LIỆU TÀI CHÍNH*\n\n'
            'File cần có 5 cột:\n`Loại` | `Số tiền` | `Ghi chú` | `Danh mục/Nguồn` | `Ngày`\n\n'
            'Ví dụ:\n`Chi tiêu | 50000 | Ăn trưa | Ăn uống | 2024-07-28`\n\n'
            'Gửi file .csv hoặc .xlsx ngay bây giờ.'
        ),
        'import_done_full':      '✅ Nhập thành công {total}:\n- {income} thu nhập\n- {expense} chi tiêu\n- {fail} lỗi bỏ qua',
        'import_file_err':       '❌ Lỗi xử lý file: {e}',
        # ── Budget list ───────────────────────────────────────────
        'budget_list_title_full':'📋 *NGÂN SÁCH THÁNG NÀY*',
        'budget_status_over':    '🚨 VƯỢT',
        'budget_status_near':    '⚠️ GẦN',
        'budget_status_ok':      '✅ OK',
        # ── Recurring (extended) ─────────────────────────────────
        'recur_back':            '◀️ Quay lại',
        'recur_btn_del':         '✅ Xóa',
        'recur_not_found':       'Không tìm thấy.',
        'recur_del_q':           'Xóa khoản định kỳ:\n*{label}* — `{amount}` Ngày {day} {freq}?',
        # ── NLP auto-transaction ──────────────────────────────────
        'nlp_income_saved':      '✅ *Thu nhập*: `{amount}`\n• Nguồn: *{cat}*\n• Ghi chú: _{note}_\n• Ngày: {date}',
        'nlp_expense_saved':     '✅ *Chi tiêu*: `{amount}`\n• Danh mục: *{cat}*\n• Ghi chú: _{note}_\n• Ngày: {date}',
        # ── Error handler ─────────────────────────────────────────
        'error_generic':         '⚠️ Có lỗi xảy ra. Hãy thử lại.',
        # ── Delete ────────────────────────────────────────────────
        'delete_title':         '🗑️ *Xóa*',
        # ── General ───────────────────────────────────────────────
        'cancel':               '❌ Hủy',
        'close':                '❌ Đóng',
        'no_data':              'Chưa có dữ liệu.',
        'not_understood':       'Không nhận diện được lệnh. Dùng các nút menu bên dưới:',
        'theme_changed':        '✅ Theme: {name}. Bấm 📋 Danh mục để thấy kết quả.',
    },
}
