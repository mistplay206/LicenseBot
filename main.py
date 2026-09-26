import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from dotenv import load_dotenv
import database

# خواندن اطلاعات از فایل .env
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
try:
    ADMIN_ID = int(os.getenv('ADMIN_ID'))
except:
    ADMIN_ID = 0

CHANNEL_ID = os.getenv('CHANNEL_ID')

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

# راه‌اندازی دیتابیس
database.init_db()

def check_membership(user_id):
    if not CHANNEL_ID or CHANNEL_ID == "@YourChannelID": 
        return True
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

# ================= ساختار منوها =================

def show_main_menu(chat_id):
    """نمایش کیبورد اصلی (برای همه)"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    # تغییر نام دکمه به اسم اختصاصی محصول شما
    markup.row(KeyboardButton('🛒 خرید لایسنس یک ماهه'), KeyboardButton('🛍 خریدهای من'))
    
    if chat_id == ADMIN_ID:
        markup.row(KeyboardButton('⚙️ تنظیمات'))
        bot.send_message(chat_id, "فروشگاه لایسنس 🛒\n\n👨‍💻 برای ورود به پنل مدیریت روی دکمه تنظیمات کلیک کنید:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "به فروشگاه لایسنس خوش آمدید 🛒", reply_markup=markup)

def show_admin_menu(chat_id):
    """نمایش کیبورد اختصاصی پنل مدیریت"""
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

# ================= دکمه لغو، ورود به پنل و بازگشت =================

@bot.message_handler(func=lambda message: message.text == '❌ لغو')
def cancel_action(message):
    if user_states.get(message.chat.id):
        user_states[message.chat.id] = None
    bot.send_message(message.chat.id, "عملیات لغو شد. 🔙", reply_markup=ReplyKeyboardRemove())
    
    if message.chat.id == ADMIN_ID:
        show_admin_menu(message.chat.id)
    else:
        show_main_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == '⚙️ تنظیمات' and message.chat.id == ADMIN_ID)
def enter_admin_panel(message):
    show_admin_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == '🔙 بازگشت' and message.chat.id == ADMIN_ID)
def back_to_main(message):
    show_main_menu(message.chat.id)

# ================= استارت و جوین اجباری =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    database.add_user(message.chat.id)
    if not check_membership(message.chat.id) and message.chat.id != ADMIN_ID:
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

# ================= بخش تنظیمات مدیریت =================

@bot.message_handler(func=lambda message: message.text == '💳 تنظیمات پرداخت' and message.chat.id == ADMIN_ID)
def payment_settings(message):
    current_price = database.get_setting('price')
    current_card = database.get_setting('card_number')
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("تغییر قیمت 💰", callback_data="change_price"))
    markup.add(InlineKeyboardButton("تغییر شماره کارت 💳", callback_data="change_card"))
    
    bot.send_message(message.chat.id, f"⚙️ **تنظیمات فعلی پرداخت:**\n\n💰 قیمت: `{current_price}`\n💳 کارت: `{current_card}`", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['change_price', 'change_card'])
def handle_setting_change(call):
    if call.from_user.id != ADMIN_ID: return
    if call.data == 'change_price':
        bot.send_message(call.message.chat.id, "💰 لطفاً قیمت جدید را وارد کنید (مثلا: ۱۵۰,۰۰۰ تومان):", reply_markup=get_cancel_markup())
        user_states[ADMIN_ID] = 'waiting_for_price'
    elif call.data == 'change_card':
        bot.send_message(call.message.chat.id, "💳 لطفاً شماره کارت جدید را وارد کنید:", reply_markup=get_cancel_markup())
        user_states[ADMIN_ID] = 'waiting_for_card'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) in ['waiting_for_price', 'waiting_for_card'] and message.chat.id == ADMIN_ID)
def save_new_settings(message):
    state = user_states[ADMIN_ID]
    if state == 'waiting_for_price':
        database.update_setting('price', message.text)
        bot.send_message(message.chat.id, f"✅ قیمت با موفقیت به `{message.text}` تغییر یافت.", parse_mode='Markdown')
    elif state == 'waiting_for_card':
        database.update_setting('card_number', message.text)
        bot.send_message(message.chat.id, f"✅ شماره کارت با موفقیت به `{message.text}` تغییر یافت.", parse_mode='Markdown')
    user_states[ADMIN_ID] = None
    show_admin_menu(message.chat.id)

# ================= مشاهده لایسنس‌ها =================

@bot.message_handler(func=lambda message: message.text == '👀 مشاهده لایسنس‌ها' and message.chat.id == ADMIN_ID)
def choose_license_type_to_view(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ موجود (فروخته نشده)", callback_data="view_available"))
    markup.add(InlineKeyboardButton("🛒 فروخته شده", callback_data="view_sold"))
    bot.send_message(message.chat.id, "انتخاب کنید کدام لیست را می‌خواهید ببینید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['view_available', 'view_sold'])
def handle_view_licenses(call):
    if call.from_user.id != ADMIN_ID:
        return
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

# ================= سایر بخش‌های ادمین =================

@bot.message_handler(func=lambda message: message.text == '👥 آمار کاربران' and message.chat.id == ADMIN_ID)
def check_users(message):
    users_count = len(database.get_all_users())
    bot.send_message(message.chat.id, f"👥 تعداد کل کاربران ربات: `{users_count}` نفر", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '📦 موجودی انبار' and message.chat.id == ADMIN_ID)
def check_stock(message):
    count = database.get_available_count()
    sold_count = database.get_total_sold_count()
    bot.send_message(message.chat.id, f"📊 **وضعیت انبار:**\n\n✅ آماده فروش: `{count}` عدد\n🛒 کل فروش‌ها: `{sold_count}` عدد", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '➕ افزودن لایسنس' and message.chat.id == ADMIN_ID)
def request_new_licenses(message):
    bot.send_message(message.chat.id, "📥 لطفاً کدهای لایسنس جدید را زیر هم در یک پیام بفرستید.\n\n📄 **همچنین می‌توانید یک فایل متنی (.txt) حاوی کدها را اینجا ارسال کنید:**", reply_markup=get_cancel_markup())
    user_states[ADMIN_ID] = 'waiting_for_new_licenses'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'waiting_for_new_licenses' and message.chat.id == ADMIN_ID, content_types=['text', 'document'])
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
                bot.send_message(message.chat.id, f"❌ خطا در خواندن فایل. لطفاً مطمئن شوید فایل متنی استاندارد است.\n{e}")
                return
        else:
            bot.send_message(message.chat.id, "⚠️ لطفاً فقط فایل متنی با پسوند txt. ارسال کنید.")
            return

    codes = [code.strip() for code in codes if code.strip()]
    if not codes:
        bot.send_message(message.chat.id, "⚠️ هیچ کدی یافت نشد! عملیات لغو شد.")
        user_states[ADMIN_ID] = None
        show_admin_menu(message.chat.id)
        return

    total_sent = len(codes)
    added = database.add_licenses(codes)
    duplicated = total_sent - added
    
    user_states[ADMIN_ID] = None
    
    report_msg = f"📦 **گزارش افزودن لایسنس:**\n\n"
    report_msg += f"📥 کل کدهای دریافتی: `{total_sent}` عدد\n"
    report_msg += f"✅ با موفقیت ذخیره شد: `{added}` عدد\n"
    if duplicated > 0:
        report_msg += f"⚠️ تکراری (رد شد): `{duplicated}` عدد\n"
    
    bot.send_message(message.chat.id, report_msg, parse_mode='Markdown')
    show_admin_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == '📢 پیام همگانی' and message.chat.id == ADMIN_ID)
def request_broadcast(message):
    bot.send_message(message.chat.id, "پیام خود را بفرستید (متن، عکس و...):", reply_markup=get_cancel_markup())
    user_states[ADMIN_ID] = 'waiting_for_broadcast'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'waiting_for_broadcast' and message.chat.id == ADMIN_ID, content_types=['text', 'photo', 'video', 'document', 'voice'])
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
    user_states[ADMIN_ID] = None
    bot.send_message(message.chat.id, f"✅ پیام شما با موفقیت به {success} نفر ارسال شد.")
    show_admin_menu(message.chat.id)

# ================= بخش مشتری =================

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

# تغییر در نام دکمه در این خط انجام شده است
@bot.message_handler(func=lambda message: message.text == '🛒 خرید لایسنس یک ماهه')
def request_payment(message):
    if not check_membership(message.chat.id) and message.chat.id != ADMIN_ID:
        send_welcome(message)
        return
        
    if database.get_available_count() == 0:
        bot.send_message(message.chat.id, "❌ متاسفانه در حال حاضر موجودی به اتمام رسیده است.")
        return
    
    price = database.get_setting('price')
    card = database.get_setting('card_number')
    
    # اضافه شدن اسم محصول به فاکتور
    msg = f"🛍 **محصول:** لایسنس یک ماهه\n" \
          f"💳 **مبلغ قابل پرداخت:** {price}\n\n" \
          f"لطفاً مبلغ را به شماره کارت زیر واریز کنید:\n`{card}`\n\n" \
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
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode='Markdown')

# ================= بخش تایید رسید توسط ادمین =================

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def handle_admin_decision(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "شما دسترسی ندارید!")
        return
        
    action, user_id_str = call.data.split('_')
    user_id = int(user_id_str)
    
    if action == 'approve':
        try:
            license_code = database.sell_license(user_id) 
            if license_code:
                # نام محصول در پیام تحویل به مشتری هم نوشته شد
                bot.send_message(user_id, f"✅ پرداخت شما تایید شد!\n\n🛍 **محصول:** لایسنس یک ماهه\n🔑 **کد لایسنس شما:**\n`{license_code}`", parse_mode='Markdown')
                bot.edit_message_caption(caption=f"✅ تایید شد.\n(کاربر: `{user_id}`)\nکد تحویل داده شده: `{license_code}`", chat_id=ADMIN_ID, message_id=call.message.message_id, parse_mode='Markdown')
            else:
                bot.answer_callback_query(call.id, "⚠️ خطا: موجودی انبار تمام شده است!", show_alert=True)
                bot.send_message(ADMIN_ID, f"⚠️ انبار خالی است! لایسنس جدید اضافه کنید.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ خطای دیتابیس!\nارور: {e}")
            
    elif action == 'reject':
        bot.send_message(user_id, "❌ کاربر گرامی، رسید ارسالی شما توسط مدیریت تایید نشد.")
        bot.edit_message_caption(caption=f"❌ رسید رد شد.\n(کاربر: `{user_id}`)", chat_id=ADMIN_ID, message_id=call.message.message_id, parse_mode='Markdown')

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()