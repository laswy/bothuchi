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
