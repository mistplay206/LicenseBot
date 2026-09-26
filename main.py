import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from dotenv import load_dotenv
import database

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
admin_env = str(os.getenv('ADMIN_ID', ''))
ADMIN_IDS = [int(x.strip()) for x in admin_env.split(',') if x.strip().isdigit()]
CHANNEL_ID = os.getenv('CHANNEL_ID')

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

database.init_db()

def check_membership(user_id):
    if not CHANNEL_ID or CHANNEL_ID == "@YourChannelID": 
        return True
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

def show_main_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton('🛒 خرید لایسنس یک ماهه'), KeyboardButton('🛍 خریدهای من'))
    
    if chat_id in ADMIN_IDS:
        markup.row(KeyboardButton('⚙️ تنظیمات'))
        bot.send_message(chat_id, "فروشگاه لایسنس 🛒\n\n👨‍💻 برای ورود به پنل مدیریت روی دکمه تنظیمات کلیک کنید:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "به فروشگاه لایسنس خوش آمدید 🛒", reply_markup=markup)

def show_admin_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton('➕ افزودن لایسنس'), KeyboardButton('📦 موجودی انبار'))
    markup.row(KeyboardButton('👀 مشاهده لایسنس‌ها'), KeyboardButton('📢 پیام همگانی'))
    markup.row(KeyboardButton('👥 آمار کاربران'), KeyboardButton('💳 تنظیمات پرداخت'))
    markup.row(KeyboardButton('🔙 بازگشت'))
    bot.send_message(chat_id, "👨‍💻 به پنل مدیریت خوش آمدید. یک گزینه را انتخاب کنید:", reply_markup=markup)

def get_cancel_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('❌ لغو'))
    return markup

@bot.message_handler(func=lambda message: message.text == '❌ لغو')
def cancel_action(message):
    if user_states.get(message.chat.id):
        user_states[message.chat.id] = None
    bot.send_message(message.chat.id, "عملیات لغو شد. 🔙", reply_markup=ReplyKeyboardRemove())
    
    if message.chat.id in ADMIN_IDS:
        show_admin_menu(message.chat.id)
    else:
        show_main_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == '⚙️ تنظیمات' and message.chat.id in ADMIN_IDS)
def enter_admin_panel(message):
    show_admin_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == '🔙 بازگشت' and message.chat.id in ADMIN_IDS)
def back_to_main(message):
    show_main_menu(message.chat.id)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    database.add_user(message.chat.id)
    if not check_membership(message.chat.id) and message.chat.id not in ADMIN_IDS:
        markup = InlineKeyboardMarkup()
        channel_url = f"https://t.me/{CHANNEL_ID.replace('@', '')}"
        markup.add(InlineKeyboardButton("📢 عضویت در کانال", url=channel_url))
        markup.add(InlineKeyboardButton("✅ عضو شدم", callback_data="check_join"))
        bot.send_message(message.chat.id, "🛑 برای استفاده از ربات، ابتدا باید در کانال ما عضو شوید:", reply_markup=markup)
        return
    show_main_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == 'check_join')
def verify_join(call):
    if check_membership(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_main_menu(call.from_user.id)
    else:
        bot.answer_callback_query(call.id, "❌ شما هنوز در کانال عضو نشده‌اید!", show_alert=True)

@bot.message_handler(func=lambda message: message.text == '💳 تنظیمات پرداخت' and message.chat.id in ADMIN_IDS)
def payment_settings(message):
    current_price = database.get_setting('price')
    current_card = database.get_setting('card_number')
    current_name = database.get_setting('card_name')
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("تغییر قیمت 💰", callback_data="change_price"))
    markup.add(InlineKeyboardButton("تغییر شماره کارت 💳", callback_data="change_card"))
    markup.add(InlineKeyboardButton("تغییر صاحب کارت 👤", callback_data="change_card_name"))
    
    bot.send_message(message.chat.id, f"⚙️ **تنظیمات فعلی پرداخت:**\n\n💰 قیمت: `{current_price}`\n💳 کارت: `{current_card}`\n👤 به نام: `{current_name}`", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['change_price', 'change_card', 'change_card_name'])
def handle_setting_change(call):
    if call.from_user.id not in ADMIN_IDS: return
    if call.data == 'change_price':
        bot.send_message(call.message.chat.id, "💰 لطفاً قیمت جدید را وارد کنید (مثلا: ۱۵۰,۰۰۰ تومان):", reply_markup=get_cancel_markup())
        user_states[call.message.chat.id] = 'waiting_for_price'
    elif call.data == 'change_card':
        bot.send_message(call.message.chat.id, "💳 لطفاً شماره کارت جدید را وارد کنید:", reply_markup=get_cancel_markup())
        user_states[call.message.chat.id] = 'waiting_for_card'
    elif call.data == 'change_card_name':
        bot.send_message(call.message.chat.id, "👤 لطفاً نام و نام خانوادگی صاحب کارت را وارد کنید:", reply_markup=get_cancel_markup())
        user_states[call.message.chat.id] = 'waiting_for_card_name'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) in ['waiting_for_price', 'waiting_for_card', 'waiting_for_card_name'] and message.chat.id in ADMIN_IDS)
def save_new_settings(message):
    state = user_states[message.chat.id]
    if state == 'waiting_for_price':
        database.update_setting('price', message.text)
        bot.send_message(message.chat.id, f"✅ قیمت با موفقیت به `{message.text}` تغییر یافت.", parse_mode='Markdown')
    elif state == 'waiting_for_card':
        database.update_setting('card_number', message.text)
        bot.send_message(message.chat.id, f"✅ شماره کارت با موفقیت به `{message.text}` تغییر یافت.", parse_mode='Markdown')
    elif state == 'waiting_for_card_name':
        database.update_setting('card_name', message.text)
        bot.send_message(message.chat.id, f"✅ نام صاحب کارت با موفقیت به `{message.text}` تغییر یافت.", parse_mode='Markdown')
    user_states[message.chat.id] = None
    show_admin_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == '👀 مشاهده لایسنس‌ها' and message.chat.id in ADMIN_IDS)
def choose_license_type_to_view(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ موجود (فروخته نشده)", callback_data="view_available"))
    markup.add(InlineKeyboardButton("🛒 فروخته شده", callback_data="view_sold"))
    bot.send_message(message.chat.id, "انتخاب کنید کدام لیست را می‌خواهید ببینید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['view_available', 'view_sold'])
def handle_view_licenses(call):
    if call.from_user.id not in ADMIN_IDS: return
    bot.delete_message(call.message.chat.id, call.message.message_id) 
    
    if call.data == 'view_available':
        codes = database.get_all_available_licenses()
        if not codes:
            bot.send_message(call.message.chat.id, "📦 انبار شما کاملاً خالی است!")
            return
        if len(codes) <= 50:
            text = f"👀 **لیست {len(codes)} لایسنس موجود:**\n\n"
            for i, code in enumerate(codes, 1):
                text += f"{i}. `{code}`\n"
            bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
        else:
            bot.send_message(call.message.chat.id, "⏳ در حال ساخت فایل خروجی...")
            file_content = "\n".join(codes)
            with open("available_licenses_export.txt", "w", encoding="utf-8") as f:
                f.write(file_content)
            with open("available_licenses_export.txt", "rb") as f:
                bot.send_document(call.message.chat.id, f, caption=f"📦 فایل حاوی {len(codes)} لایسنس موجود در انبار")
            os.remove("available_licenses_export.txt")

    elif call.data == 'view_sold':
        sold_data = database.get_all_sold_licenses()
        if not sold_data:
            bot.send_message(call.message.chat.id, "🛒 هنوز هیچ لایسنسی فروخته نشده است!")
            return
        if len(sold_data) <= 50:
            text = f"🛒 **لیست {len(sold_data)} لایسنس فروخته شده:**\n\n"
            for i, item in enumerate(sold_data, 1):
                code, buyer, date = item
                text += f"{i}. `{code}`\n👤 خریدار: `{buyer}` | 🕒 {date}\n\n"
            bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
        else:
            bot.send_message(call.message.chat.id, "⏳ در حال ساخت فایل خروجی...")
            file_content = "لیست لایسنس‌های فروخته شده:\n\n"
            for i, item in enumerate(sold_data, 1):
                code, buyer, date = item
                file_content += f"{i}. Code: {code} | Buyer: {buyer} | Date: {date}\n"
            with open("sold_licenses_export.txt", "w", encoding="utf-8") as f:
                f.write(file_content)
            with open("sold_licenses_export.txt", "rb") as f:
                bot.send_document(call.message.chat.id, f, caption=f"🛒 فایل حاوی {len(sold_data)} لایسنس فروخته شده")
            os.remove("sold_licenses_export.txt")

@bot.message_handler(func=lambda message: message.text == '👥 آمار کاربران' and message.chat.id in ADMIN_IDS)
def check_users(message):
    users_count = len(database.get_all_users())
    bot.send_message(message.chat.id, f"👥 تعداد کل کاربران ربات: `{users_count}` نفر", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '📦 موجودی انبار' and message.chat.id in ADMIN_IDS)
def check_stock(message):
    count = database.get_available_count()
    sold_count = database.get_total_sold_count()
    bot.send_message(message.chat.id, f"📊 **وضعیت انبار:**\n\n✅ آماده فروش: `{count}` عدد\n🛒 کل فروش‌ها: `{sold_count}` عدد", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '➕ افزودن لایسنس' and message.chat.id in ADMIN_IDS)
def request_new_licenses(message):
    bot.send_message(message.chat.id, "📥 لطفاً کدهای لایسنس جدید را زیر هم در یک پیام بفرستید.\n\n📄 **همچنین می‌توانید یک فایل متنی (.txt) حاوی کدها را اینجا ارسال کنید:**", reply_markup=get_cancel_markup())
    user_states[message.chat.id] = 'waiting_for_new_licenses'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'waiting_for_new_licenses' and message.chat.id in ADMIN_IDS, content_types=['text', 'document'])
def save_new_licenses(message):
    codes = []
    if message.content_type == 'text':
        codes = message.text.split('\n')
    elif message.content_type == 'document':
        if message.document.file_name.endswith('.txt') or message.document.mime_type == 'text/plain':
            bot.send_message(message.chat.id, "⏳ در حال دانلود و خواندن فایل...")
            try:
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                file_content = downloaded_file.decode('utf-8')
                codes = file_content.split('\n')
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ خطا در خواندن فایل.\n{e}")
                return
        else:
            bot.send_message(message.chat.id, "⚠️ لطفاً فقط فایل متنی با پسوند txt. ارسال کنید.")
            return

    codes = [code.strip() for code in codes if code.strip()]
    if not codes:
        bot.send_message(message.chat.id, "⚠️ هیچ کدی یافت نشد! عملیات لغو شد.")
        user_states[message.chat.id] = None
        show_admin_menu(message.chat.id)
        return

    total_sent = len(codes)
    added = database.add_licenses(codes)
    duplicated = total_sent - added
    
    user_states[message.chat.id] = None
    
    report_msg = f"📦 **گزارش افزودن لایسنس:**\n\n"
    report_msg += f"📥 کل کدهای دریافتی: `{total_sent}` عدد\n"
    report_msg += f"✅ با موفقیت ذخیره شد: `{added}` عدد\n"
    if duplicated > 0:
        report_msg += f"⚠️ تکراری (رد شد): `{duplicated}` عدد\n"
    
    bot.send_message(message.chat.id, report_msg, parse_mode='Markdown')
    show_admin_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == '📢 پیام همگانی' and message.chat.id in ADMIN_IDS)
def request_broadcast(message):
    bot.send_message(message.chat.id, "پیام خود را بفرستید (متن، عکس و...):", reply_markup=get_cancel_markup())
    user_states[message.chat.id] = 'waiting_for_broadcast'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'waiting_for_broadcast' and message.chat.id in ADMIN_IDS, content_types=['text', 'photo', 'video', 'document', 'voice'])
def send_broadcast(message):
    users = database.get_all_users()
    success = 0
    bot.send_message(message.chat.id, "⏳ در حال ارسال پیام...")
    for user_id in users:
        try:
            bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            success += 1
        except:
            pass 
    user_states[message.chat.id] = None
    bot.send_message(message.chat.id, f"✅ پیام شما با موفقیت به {success} نفر ارسال شد.")
    show_admin_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == '🛍 خریدهای من')
def my_purchases(message):
    purchases = database.get_user_purchases(message.chat.id)
    if not purchases:
        bot.send_message(message.chat.id, "شما هنوز هیچ خریدی از ما نداشته‌اید. 🛒")
        return
    text = "🛍 **لیست خریدهای شما:**\n\n"
    for idx, p in enumerate(purchases, 1):
        text += f"{idx}. کد: `{p[0]}`\n🕒 تاریخ: {p[1]}\n\n"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '🛒 خرید لایسنس یک ماهه')
def request_payment(message):
    if not check_membership(message.chat.id) and message.chat.id not in ADMIN_IDS:
        send_welcome(message)
        return
        
    if database.get_available_count() == 0:
        bot.send_message(message.chat.id, "❌ متاسفانه در حال حاضر موجودی به اتمام رسیده است.")
        return
    
    price = database.get_setting('price')
    card = database.get_setting('card_number')
    card_name = database.get_setting('card_name')
    
    msg = f"🛍 **محصول:** لایسنس یک ماهه\n" \
          f"💳 **مبلغ قابل پرداخت:** {price}\n\n" \
          f"لطفاً مبلغ را به شماره کارت زیر واریز کنید:\n`{card}`\n👤 **به نام:** {card_name}\n\n" \
          f"📸 **سپس عکس رسید واریزی خود را ارسال کنید.**"
          
    bot.send_message(message.chat.id, msg, parse_mode='Markdown', reply_markup=get_cancel_markup())
    user_states[message.chat.id] = 'waiting_for_receipt'

@bot.message_handler(content_types=['photo', 'text'])
def handle_receipt(message):
    if user_states.get(message.chat.id) == 'waiting_for_receipt':
        
        if message.content_type != 'photo':
            bot.send_message(message.chat.id, "⚠️ لطفاً فقط عکس رسید را ارسال کنید. (یا از دکمه لغو استفاده کنید)")
            return

        user_states[message.chat.id] = None 
        bot.send_message(message.chat.id, "✅ رسید شما دریافت شد و برای مدیریت ارسال گردید. لطفاً منتظر تایید باشید. ⏳", reply_markup=ReplyKeyboardRemove())
        show_main_menu(message.chat.id)
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ تایید و ارسال", callback_data=f"approve_{message.chat.id}"),
            InlineKeyboardButton("❌ رد رسید", callback_data=f"reject_{message.chat.id}")
        )
        username = f"@{message.from_user.username}" if message.from_user.username else "ندارد"
        caption = f"🧾 رسید جدید (لایسنس یک ماهه)\nآیدی: `{message.chat.id}`\nیوزرنیم: {username}"
        
        for admin_id in ADMIN_IDS:
            try:
                bot.send_photo(admin_id, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode='Markdown')
            except:
                pass

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def handle_admin_decision(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "شما دسترسی ندارید!")
        return
        
    action, user_id_str = call.data.split('_')
    user_id = int(user_id_str)
    
    if action == 'approve':
        try:
            license_code = database.sell_license(user_id) 
            if license_code:
                bot.send_message(user_id, f"✅ پرداخت شما تایید شد!\n\n🛍 **محصول:** لایسنس یک ماهه\n🔑 **کد لایسنس شما:**\n`{license_code}`", parse_mode='Markdown')
                bot.edit_message_caption(caption=f"✅ تایید شد.\n(کاربر: `{user_id}`)\nکد تحویل داده شده: `{license_code}`\n👤 بررسی توسط ادمین: `{call.from_user.id}`", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown')
            else:
                bot.answer_callback_query(call.id, "⚠️ خطا: موجودی انبار تمام شده است!", show_alert=True)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ خطای دیتابیس!\nارور: {e}")
            
    elif action == 'reject':
        bot.send_message(user_id, "❌ کاربر گرامی، رسید ارسالی شما توسط مدیریت تایید نشد.")
        bot.edit_message_caption(caption=f"❌ رسید رد شد.\n(کاربر: `{user_id}`)\n👤 بررسی توسط ادمین: `{call.from_user.id}`", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown')

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()