import telebot
import requests
import time
import threading
import random
import re
import os
import json

# --- بيانات البوت ---
BOT_TOKEN   = '7655504363:AAEBZmKP7NzaxIvtXQejVj82cRyp5Y52B_A'
OWNER_ID    = 6488083580
ALERT_ADMINS = {198027774}  # أدمنية صلاحية التنبيه فقط
CHANNEL     = 'https://t.me/hawk0000000'

# --- القائمة البيضاء ---
WHITELIST_LINKS = [
    't.me/hawk0000000',
    'youtube.com',
    'youtu.be',
    'tiktok.com',
    'instagram.com',
    'waze.com',
    'facebook.com',
    'fb.com',
    'fb.watch'
]

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE      = "users_db.txt"
VIDEOS_FILE  = "videos_db.json"
BUTTONS_FILE = "buttons_db.json"
GROUPS_FILE  = "groups_db.txt"

pending_admin   = {}
pending_video   = {}
pending_mention = {}
glitch_sessions = {}

# ═══════════════════════════════════════
# 📋 حفظ المجموعات تلقائياً
# ═══════════════════════════════════════

DEFAULT_GROUPS = set()

def load_groups():
    groups = set(DEFAULT_GROUPS)
    if os.path.exists(GROUPS_FILE):
        for line in open(GROUPS_FILE, "r"):
            line = line.strip()
            if line:
                try: groups.add(int(line))
                except: pass
    return groups

def save_group(chat_id):
    groups = load_groups()
    if chat_id not in groups:
        with open(GROUPS_FILE, "a") as f:
            f.write(f"{chat_id}\n")

active_groups = load_groups()

# ═══════════════════════════════════════
# 📸 الصورة الإعلانية
# ═══════════════════════════════════════

DAILY_PHOTO_URL = "https://a.top4top.io/p_3732sxkcf0.png"

BUTTON_KEYS = {
    "uber_pay":      "💳 طريقة تسديد Uber",
    "uber_withdraw": "💰 طريقة سحب مستحقات Uber",
    "uber_careem":   "🔗 ربط كريم في Uber",
    "uber_master":   "💳 ربط الماستر بتطبيق Uber",
    "uber_cancel":   "🔄 تعويض إلغاء الرحلة",
    "uber_block":    "🚫 منع الرحلات الجديدة",
    "uber_support":  "🆘 دعم Uber داخل التطبيق",
    "baly_pay":      "💳 طريقة تسديد Baly",
    "oper_pay":      "💳 طريقة تسديد Oper",
}

# ═══════════════════════════════════════
# دوال قاعدة البيانات
# ═══════════════════════════════════════

def load_users():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return {line.strip(): True for line in f.readlines()}
    return {}

def save_user(user_id):
    with open(DB_FILE, "a") as f:
        f.write(f"{user_id}\n")

def load_videos():
    if os.path.exists(VIDEOS_FILE):
        with open(VIDEOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_videos(videos):
    with open(VIDEOS_FILE, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

def load_buttons():
    if os.path.exists(BUTTONS_FILE):
        with open(BUTTONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "main": [
            {"key": "menu_uber", "label": "🚖 حول Uber", "type": "submenu"},
            {"key": "baly_main", "label": "🟢 حول Baly", "type": "video"},
            {"key": "oper_main", "label": "🟡 حول Oper", "type": "video"},
        ],
        "uber": [
            {"key": "uber_pay",      "label": "💳 طريقة تسديد Uber",        "type": "video"},
            {"key": "uber_withdraw", "label": "💰 طريقة سحب مستحقات Uber",  "type": "video"},
            {"key": "uber_careem",   "label": "🔗 ربط كريم في Uber",         "type": "video"},
            {"key": "uber_master",   "label": "💳 ربط الماستر بتطبيق Uber", "type": "video"},
            {"key": "uber_cancel",   "label": "🔄 تعويض إلغاء الرحلة",      "type": "video"},
            {"key": "uber_block",    "label": "🚫 منع الرحلات الجديدة",     "type": "video"},
            {"key": "uber_support",  "label": "🆘 دعم Uber داخل التطبيق",   "type": "video"},
        ]
    }

def save_buttons(b):
    with open(BUTTONS_FILE, "w", encoding="utf-8") as f:
        json.dump(b, f, ensure_ascii=False, indent=2)

replied_users = load_users()
videos_db     = load_videos()

# ═══════════════════════════════════════
# 👥 أعضاء سبق الرد عليهم
# ═══════════════════════════════════════
PRE_REPLIED = [
    5633215088, 6488083580, 7609125208, 6795035237, 8539562017,
    864870558,  7327508475, 7536362781, 1070865939, 6830552073,
    7988621867, 6094437294, 198027774,  5088986424, 757238742,
    761060518,  680759139,  1040677599, 7157045929, 7357049023,
    275721187,  7617151152, 8376116643, 930017311,  6356596693,
    7025637869, 1479414048, 6265596285, 1166572718, 7567727943,
    1570199594, 57105596,   1384300828, 5986061100, 103118589,
    6009034600, 660820270,  5987653099, 1025838371, 6251602984,
    473037594,  8449403353, 241025620,  5980813009, 2096246385,
    639419761,  8166538747, 206463756,  5020366676, 283084206,
    5322110987, 7446662158, 5645221568, 8196301549, 6594976602,
    643244393,  5178534518, 1116833219, 1215608520, 7725269843,
]

for uid in PRE_REPLIED:
    uid_str = str(uid)
    if uid_str not in replied_users:
        replied_users[uid_str] = True
        save_user(uid_str)

# ═══════════════════════════════════════
# 🎬 الفيديوهات الثابتة
# ═══════════════════════════════════════
FIXED_VIDEOS = {
    "oper_pay":      "BAACAgIAAxkBAAIDGGmbIPGGhh4Q2OkKCjDHP20p9iweAAKHlwACv-DYSG4MDukpCf0tOgQ",
    "baly_pay":      "BAACAgIAAxkBAAIDGmmbIRJixuRz2Q8bfgJ9BIDW57_0AAKJlwACv-DYSA-mro42hfb3OgQ",
    "uber_withdraw": "BAACAgIAAxkBAAIChGmawtpFjG-Y-os3JJia_fcLtxXZAAI_kgACv-DYSDiXe_Ej73KjOgQ",
    "uber_careem":   "BAACAgIAAxkBAAIC5mmbBndewCwKXr_or9mitgjKlSpDAAL6lQACv-DYSLfZGzJ-cvWpOgQ",
    "uber_master":   "BAACAgIAAxkBAAIC3GmbATBbMwd9OaRMDd0J05FNlnpjAALkhwACZV_RS5rI8WmK3zJ1OgQ",
    "uber_support":  "BAACAgIAAxkBAAIC1mmbAAFWjjXaphG0vnstNi3CnfWcTQACgpUAAqtp6EtWakIboxiqbjoE",
    "uber_block":    "BAACAgIAAxkBAAIC02mbAAE4iYfKQk6pwa6aZX8q3tf3FwAC95wAAhQ7aEimz619q9l_eDoE",
    "uber_cancel":   "BAACAgIAAxkBAAICjGmaw7FSiQvkdv99yPoujWKfSirWAAJWnQACFDtoSLXKf446_9NnOgQ",
    "uber_pay":      "BAACAgIAAxkBAAID5mmlkRH-iaBVRCS_kW-R7MSCU_9RAAITjwAC5XsQSVw4Yd0kWt23OgQ",
}

for key, file_id in FIXED_VIDEOS.items():
    videos_db[key] = file_id
save_videos(videos_db)

# ═══════════════════════════════════════
# دوال مساعدة
# ═══════════════════════════════════════

def is_admin(chat_id, user_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in admins)
    except:
        return False

def is_emoji_only(text):
    if not text:
        return False
    clean_text = re.sub(r'[^\w\s,.]', '', text).strip()
    return len(clean_text) == 0

def contains_url(text):
    if not text:
        return False
    url_pattern = re.compile(
        r'(https?://\S+|www\.\S+|t\.me/\S+|@\S+\.\S+)',
        re.IGNORECASE
    )
    return bool(url_pattern.search(text))

ADULT_KEYWORDS = [
    'porn', 'xxx', 'sex', 'nude', 'naked', 'onlyfans',
    'xvideos', 'xnxx', 'pornhub', 'redtube', 'youporn', 'brazzers',
    'اباحي', 'إباحي', 'سكس', 'عاري', 'عارية',
    'بورن', 'شرموطة', 'عاهرة', 'دعارة',
    'فيديو ساخن', 'صور ساخنة', 'بنات خاص', 'cam girls'
]

def is_adult_content(text):
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in ADULT_KEYWORDS)

def is_suspicious_url(text):
    if not text:
        return False
    url_pattern = re.compile(r'(https?://\S+|www\.\S+)', re.IGNORECASE)
    if not url_pattern.search(text):
        return False
    return not any(link in text.lower() for link in WHITELIST_LINKS)

def delete_message_after(chat_id, message_id, delay_seconds):
    time.sleep(delay_seconds)
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

def send_delayed_voice(chat_id, message_id):
    time.sleep(5)
    try:
        voices = [
            'CQACAgIAAxkBAAID62mobbzOQ1o4S4KrKF-xw3vNOSoyAALTkwACB05JSaaWNgXn9gqbOgQ',
            'CQACAgIAAxkBAAIEIWmodiU9smBOQ4lZG7hc5yU785pvAAJVlAACB05JSbPIhdoDGKQlOgQ'
        ]
        chosen_voice = random.choice(voices)
        bot_info = bot.get_me()
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            "🤖 AI الصقور — اضغط للتحدث",
            url=f"https://t.me/{bot_info.username}?start=hi"
        ))
        bot.send_voice(
            chat_id, chosen_voice,
            caption=CHANNEL,
            reply_to_message_id=message_id,
            reply_markup=markup
        )
    except:
        pass

# ═══════════════════════════════════════
# قوائم الأزرار
# ═══════════════════════════════════════

def get_main_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🚖 حول Uber", callback_data="menu_uber"),
        telebot.types.InlineKeyboardButton("🟢 حول Baly", callback_data="menu_baly"),
        telebot.types.InlineKeyboardButton("🟡 حول Oper", callback_data="menu_oper"),
        telebot.types.InlineKeyboardButton("💳 ماستر كارد", callback_data="menu_mastercard"),
    )
    return markup

def get_uber_menu():
    buttons_db = load_buttons()
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for btn in buttons_db.get('uber', []):
        markup.add(telebot.types.InlineKeyboardButton(btn['label'], callback_data=f"btn_{btn['key']}"))
    markup.add(telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="menu_back"))
    return markup

def get_baly_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("💳 تسديد Baly", callback_data="btn_baly_pay"),
        telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="menu_back"),
    )
    return markup

def get_oper_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("💳 تسديد Oper", callback_data="btn_oper_pay"),
        telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="menu_back"),
    )
    return markup

def get_mastercard_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🔧 حل مشكلة الماستر كارد", callback_data="mc_fix"),
        telebot.types.InlineKeyboardButton("💳 الحصول على الماستر", callback_data="mc_get"),
        telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="menu_back"),
    )
    return markup

def get_assign_buttons():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for key, label in BUTTON_KEYS.items():
        markup.add(telebot.types.InlineKeyboardButton(label, callback_data=f"assign_{key}"))
    markup.add(telebot.types.InlineKeyboardButton("❌ إلغاء", callback_data="assign_cancel"))
    return markup

def get_admin_panel():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("📋 إدارة أزرار القائمة الرئيسية", callback_data="adm_list_main"),
        telebot.types.InlineKeyboardButton("🚖 إدارة أزرار Uber",             callback_data="adm_list_uber"),
        telebot.types.InlineKeyboardButton("🎬 تغيير فيديو زر",               callback_data="adm_change_video"),
        telebot.types.InlineKeyboardButton("📢 إرسال تنبيه للمجموعات",        callback_data="adm_alert"),
        telebot.types.InlineKeyboardButton("📍 تجمع",                          callback_data="adm_gather"),
    )
    return markup

def get_gather_groups_menu():
    groups = load_groups()
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for gid in groups:
        try:
            chat = bot.get_chat(gid)
            name = chat.title or str(gid)
        except:
            name = str(gid)
        markup.add(telebot.types.InlineKeyboardButton(
            f"👥 {name}", callback_data=f"gather_group_{gid}"
        ))
    markup.add(telebot.types.InlineKeyboardButton("📢 إرسال للكل", callback_data="gather_group_all"))
    markup.add(telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_back"))
    return markup

def get_groups_menu():
    groups = load_groups()
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for gid in groups:
        try:
            chat = bot.get_chat(gid)
            name = chat.title or str(gid)
        except:
            name = str(gid)
        markup.add(telebot.types.InlineKeyboardButton(
            f"👥 {name}", callback_data=f"alert_group_{gid}"
        ))
    markup.add(telebot.types.InlineKeyboardButton(
        "📢 إرسال للكل", callback_data="alert_group_all"
    ))
    markup.add(telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_back"))
    return markup

def get_manage_menu(section):
    buttons_db = load_buttons()
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for btn in buttons_db.get(section, []):
        markup.add(telebot.types.InlineKeyboardButton(
            f"✏️ {btn['label']}", callback_data=f"adm_edit_{section}_{btn['key']}"
        ))
    markup.add(
        telebot.types.InlineKeyboardButton("➕ إضافة زر جديد", callback_data=f"adm_add_{section}"),
        telebot.types.InlineKeyboardButton("🔙 رجوع",          callback_data="adm_back"),
    )
    return markup

def get_edit_btn_menu(section, key):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("✏️ تغيير الاسم",   callback_data=f"adm_rename_{section}_{key}"),
        telebot.types.InlineKeyboardButton("🎬 تغيير الفيديو", callback_data=f"adm_vid_{section}_{key}"),
        telebot.types.InlineKeyboardButton("🗑 حذف الزر",      callback_data=f"adm_del_{section}_{key}"),
        telebot.types.InlineKeyboardButton("🔙 رجوع",          callback_data=f"adm_list_{section}"),
    )
    return markup

# ═══════════════════════════════════════
# معالج الأزرار (Callbacks)
# ═══════════════════════════════════════

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    data    = call.data

    if data.startswith('glitch_fixed_'):
        try:
            bot.send_photo(chat_id, FIXED_PHOTO)
            bot.answer_callback_query(call.id)
            try: bot.delete_message(chat_id, call.message.message_id)
            except: pass
        except Exception as e:
            print(f"glitch_fixed error: {e}")
        return

    if data == "menu_uber":
        try: bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_uber_menu())
        except: pass
        bot.answer_callback_query(call.id)
        return

    if data == "menu_baly":
        try: bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_baly_menu())
        except: pass
        bot.answer_callback_query(call.id)
        return

    if data == "menu_oper":
        try: bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_oper_menu())
        except: pass
        bot.answer_callback_query(call.id)
        return

    if data == "menu_mastercard":
        try: bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_mastercard_menu())
        except: pass
        bot.answer_callback_query(call.id)
        return

    if data == "mc_fix":
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        try:
            bot.send_video(
                chat_id,
                "https://a.top4top.io/m_37642ygkt0.mp4",
                caption="🔧 حل مشكلة الماستر كارد\n\n📢 " + CHANNEL
            )
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ خطأ في إرسال الفيديو: {e}")
        bot.answer_callback_query(call.id)
        return

    if data == "mc_get":
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        try:
            bot.send_video(
                chat_id,
                "https://i.top4top.io/m_37646npju0.mp4",
                caption="💳 الحصول على الماستر\n\n📢 " + CHANNEL
            )
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ خطأ في إرسال الفيديو: {e}")
        bot.answer_callback_query(call.id)
        return

    if data == "menu_back":
        try: bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_main_menu())
        except: pass
        bot.answer_callback_query(call.id)
        return

    if data.startswith("btn_"):
        key = data[4:]
        if key in videos_db:
            try:
                if user_id in pending_mention:
                    info = pending_mention.pop(user_id)
                    bot.send_video(info['chat_id'], videos_db[key], caption=CHANNEL,
                                   reply_to_message_id=info['target_message_id'])
                else:
                    bot.send_video(chat_id, videos_db[key], caption=CHANNEL)
                bot.delete_message(chat_id, call.message.message_id)
            except:
                bot.answer_callback_query(call.id, "⚠️ حدث خطأ في إرسال الفيديو", show_alert=True)
                return
        else:
            label = BUTTON_KEYS.get(key, key)
            bot.answer_callback_query(call.id, f"⚠️ لا يوجد فيديو لـ: {label}", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        return

    if data.startswith("assign_"):
        key = data[7:]
        if key == "cancel":
            pending_video.pop(user_id, None)
            try: bot.delete_message(chat_id, call.message.message_id)
            except: pass
            bot.answer_callback_query(call.id)
            return
        if user_id in pending_video:
            file_id = pending_video.pop(user_id)
            videos_db[key] = file_id
            save_videos(videos_db)
            label = BUTTON_KEYS.get(key, key)
            try: bot.edit_message_text(f"✅ تم حفظ الفيديو!\nالزر: {label}", chat_id, call.message.message_id)
            except: pass
            bot.answer_callback_query(call.id, "✅ تم الحفظ!")
        else:
            bot.answer_callback_query(call.id, "⚠️ انتهت الجلسة، أرسل الفيديو مجدداً", show_alert=True)
        return

    if data == "adm_back":
        try: bot.edit_message_text('⚙️ لوحة الإدارة:', chat_id, call.message.message_id, reply_markup=get_admin_panel())
        except: pass
        bot.answer_callback_query(call.id)
        return

    if data.startswith("adm_list_"):
        section = data[9:]
        try: bot.edit_message_text(f'📋 قائمة {section}:', chat_id, call.message.message_id, reply_markup=get_manage_menu(section))
        except: pass
        bot.answer_callback_query(call.id)
        return

    if data.startswith("adm_edit_"):
        parts   = data[9:].split("_", 1)
        section = parts[0]
        key     = parts[1] if len(parts) > 1 else ""
        try: bot.edit_message_text('✏️ تعديل الزر:', chat_id, call.message.message_id, reply_markup=get_edit_btn_menu(section, key))
        except: pass
        bot.answer_callback_query(call.id)
        return

    if data.startswith("adm_rename_"):
        parts   = data[11:].split("_", 1)
        section = parts[0]
        key     = parts[1] if len(parts) > 1 else ""
        pending_admin[user_id] = {'action': 'rename', 'section': section, 'key': key}
        bot.send_message(chat_id, "✏️ أرسل الاسم الجديد للزر:")
        bot.answer_callback_query(call.id)
        return

    if data.startswith("adm_vid_"):
        parts   = data[8:].split("_", 1)
        section = parts[0]
        key     = parts[1] if len(parts) > 1 else ""
        pending_admin[user_id] = {'action': 'set_video', 'section': section, 'key': key}
        bot.send_message(chat_id, "🎬 أرسل الفيديو الجديد:")
        bot.answer_callback_query(call.id)
        return

    if data.startswith("adm_del_"):
        parts   = data[8:].split("_", 1)
        section = parts[0]
        key     = parts[1] if len(parts) > 1 else ""
        buttons_db = load_buttons()
        buttons_db[section] = [b for b in buttons_db.get(section, []) if b['key'] != key]
        save_buttons(buttons_db)
        videos_db.pop(key, None)
        save_videos(videos_db)
        try: bot.edit_message_text('🗑 تم الحذف.', chat_id, call.message.message_id, reply_markup=get_manage_menu(section))
        except: pass
        bot.answer_callback_query(call.id, "✅ تم الحذف")
        return

    if data.startswith("adm_add_"):
        section = data[8:]
        pending_admin[user_id] = {'action': 'add_btn', 'section': section}
        bot.send_message(chat_id, "➕ أرسل اسم الزر الجديد:")
        bot.answer_callback_query(call.id)
        return

    if data == "adm_gather":
        if user_id != OWNER_ID and user_id not in ALERT_ADMINS:
            bot.answer_callback_query(call.id, "🚫 غير مصرح", show_alert=True)
            return
        pending_admin[user_id] = {'action': 'gather_photo'}
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        bot.send_message(chat_id, "🖼 أرسل صورة التجمع:")
        bot.answer_callback_query(call.id)
        return

    if data == "adm_alert":
        if user_id != OWNER_ID and user_id not in ALERT_ADMINS:
            bot.answer_callback_query(call.id, "🚫 غير مصرح", show_alert=True)
            return
        try: bot.edit_message_text("📢 اختر المجموعة التي تريد إرسال التنبيه إليها:", chat_id, call.message.message_id, reply_markup=get_groups_menu())
        except: pass
        bot.answer_callback_query(call.id)
        return

    if data.startswith("gather_group_"):
        if user_id != OWNER_ID and user_id not in ALERT_ADMINS:
            bot.answer_callback_query(call.id, "🚫 غير مصرح", show_alert=True)
            return
        target  = data[13:]
        file_id = pending_admin.get(user_id, {}).get('gather_file_id')
        if not file_id:
            bot.answer_callback_query(call.id, "⚠️ انتهت الجلسة، أرسل الصورة مجدداً", show_alert=True)
            return
        pending_admin[user_id] = {'action': 'gather_location', 'target': target, 'gather_file_id': file_id}
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        bot.send_message(chat_id, "📍 أرسل الموقع الآن\nأو اكتب <b>تخطي</b> لإرسال الصورة بدون موقع:", parse_mode="HTML")
        bot.answer_callback_query(call.id)
        return

    if data.startswith("alert_group_"):
        if user_id != OWNER_ID and user_id not in ALERT_ADMINS:
            bot.answer_callback_query(call.id, "🚫 غير مصرح", show_alert=True)
            return
        target = data[12:]
        pending_admin[user_id] = {'action': 'send_alert', 'target': target}
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        bot.send_message(chat_id, "🖼 أرسل الصورة الآن وسيتم إرسالها كتنبيه:")
        bot.answer_callback_query(call.id)
        return

    bot.answer_callback_query(call.id)


# ═══════════════════════════════════════
# ⭐ /start في الخاص
# ═══════════════════════════════════════

@bot.message_handler(commands=['start'], func=lambda m: m.chat.type == 'private')
def start_command(message):
    user_id    = message.from_user.id
    first_name = message.from_user.first_name or "أخي"

    if user_id == OWNER_ID:
        bot.send_message(message.chat.id, '⚙️ لوحة الإدارة - اختر ما تريد تعديله:',
                         reply_markup=get_admin_panel())
        return

    if user_id in ALERT_ADMINS:
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(telebot.types.InlineKeyboardButton("📢 إرسال تنبيه للمجموعات", callback_data="adm_alert"))
        markup.add(telebot.types.InlineKeyboardButton("📍 تجمع", callback_data="adm_gather"))
        bot.send_message(message.chat.id, '📢 لوحة التنبيهات:', reply_markup=markup)
        return

    welcome = (
        f"🦅 ياهلا ومرحبا بيك حياك الله {first_name}!\n\n"
        f"أنا صقر العراق، مساعدك 🤖\n"
        f"اضغط على الأزرار أدناه لمشاهدة الفيديوهات التعليمية\n"
        f"عن Uber أو Baly أو Oper ⚡\n\n"
        f"📢 قناتنا: https://t.me/hawk0000000\n"
        f"👥 مجموعتنا: https://t.me/FalconsofIraq\n\n"
        f"تحية طيبة لكم 🌹\n"
        f"إدارة كباتن صقور العراق 🦅"
    )
    bot.send_message(message.chat.id, welcome,
                     reply_markup=get_main_menu(),
                     disable_web_page_preview=True)


# ═══════════════════════════════════════
# أوامر الأدمن في الخاص
# ═══════════════════════════════════════

@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.text and m.text.strip().lower() == 'admin')
def admin_text_command(message):
    if message.from_user.id != OWNER_ID:
        return
    bot.send_message(message.chat.id, '⚙️ لوحة الإدارة - اختر ما تريد تعديله:',
                     reply_markup=get_admin_panel())

@bot.message_handler(commands=['myid'], func=lambda m: m.chat.type == 'private')
def myid_command(message):
    bot.reply_to(message, f'🆔 ID الخاص بك: {message.from_user.id}')

@bot.message_handler(commands=['admin'], func=lambda m: m.chat.type == 'private')
def admin_command(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, '🚫 غير مصرح لك باستخدام هذا الأمر.')
        return
    bot.send_message(message.chat.id, '⚙️ لوحة الإدارة - اختر ما تريد تعديله:',
                     reply_markup=get_admin_panel())


# ═══════════════════════════════════════
# معالج إدخال الأدمن (pending_admin)
# ═══════════════════════════════════════

@bot.message_handler(content_types=['text', 'video', 'photo'],
                     func=lambda m: m.chat.type == 'private' and m.from_user.id in pending_admin and (
                         (m.content_type == 'photo' and pending_admin.get(m.from_user.id, {}).get('action') in ['gather_photo', 'send_alert']) or
                         m.content_type in ['text', 'video']
                     ))
def handle_admin_input(message):
    user_id = message.from_user.id
    state   = pending_admin.pop(user_id)
    action  = state['action']

    if action == 'rename' and message.content_type == 'text':
        section    = state['section']
        key        = state['key']
        new_label  = message.text.strip()
        buttons_db = load_buttons()
        for btn in buttons_db.get(section, []):
            if btn['key'] == key:
                btn['label'] = new_label
                break
        save_buttons(buttons_db)
        bot.reply_to(message, f"✅ تم تغيير اسم الزر إلى: {new_label}")
        return

    if action == 'set_video' and message.content_type == 'video':
        key = state['key']
        videos_db[key] = message.video.file_id
        save_videos(videos_db)
        bot.reply_to(message, "✅ تم حفظ الفيديو للزر بنجاح!")
        return

    if action == 'add_btn' and message.content_type == 'text':
        section   = state['section']
        new_label = message.text.strip()
        new_key   = f"custom_{int(time.time())}"
        pending_admin[user_id] = {'action': 'add_btn_video', 'section': section,
                                  'key': new_key, 'label': new_label}
        bot.reply_to(message, f"✅ الاسم: {new_label}\n🎬 الآن أرسل الفيديو لهذا الزر:")
        return

    if action == 'add_btn_video' and message.content_type == 'video':
        section    = state['section']
        key        = state['key']
        label      = state['label']
        buttons_db = load_buttons()
        if section not in buttons_db:
            buttons_db[section] = []
        buttons_db[section].append({'key': key, 'label': label, 'type': 'video'})
        save_buttons(buttons_db)
        videos_db[key] = message.video.file_id
        save_videos(videos_db)
        bot.reply_to(message, f"✅ تم إضافة الزر: {label}\nسيظهر فوراً! 🎉")
        return

    if action == 'gather_photo' and message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        pending_admin[user_id] = {'action': 'gather_photo_done', 'gather_file_id': file_id}
        bot.reply_to(message, "✅ تم استلام الصورة!\nاختر المجموعة:", reply_markup=get_gather_groups_menu())
        return

    if action == 'gather_location' and message.content_type == 'text':
        target  = state['target']
        file_id = state['gather_file_id']
        caption = None if message.text.strip() == 'تخطي' else message.text.strip()
        groups  = load_groups()
        send_to = list(groups) if target == 'all' else [int(target)]
        success = 0
        for gid in send_to:
            try:
                bot.send_photo(gid, file_id, caption=caption)
                success += 1
            except:
                pass
        bot.reply_to(message, f"✅ تم إرسال التجمع إلى {success} مجموعة!")
        return

    if action == 'send_alert' and message.content_type == 'photo':
        target  = state['target']
        file_id = message.photo[-1].file_id
        groups  = load_groups()
        send_to = list(groups) if target == 'all' else [int(target)]
        success = 0
        for gid in send_to:
            try:
                bot.send_photo(gid, file_id, caption="https://t.me/FalconsofIraq")
                success += 1
            except:
                pass
        bot.reply_to(message, f"✅ تم إرسال التنبيه إلى {success} مجموعة!")
        return

    bot.reply_to(message, "⚠️ نوع غير صحيح، حاول مجدداً من /admin")


# ═══════════════════════════════════════
# خاص: استقبال فيديو من الأونر للحفظ
# ═══════════════════════════════════════

@bot.message_handler(content_types=['video'],
                     func=lambda m: m.chat.type == 'private' and m.from_user.id == OWNER_ID)
def handle_private_video(message):
    if message.from_user.id in pending_admin:
        return
    pending_video[message.from_user.id] = message.video.file_id
    bot.reply_to(message, "📹 تم استلام الفيديو!\nاختر الزر الذي تريد ربطه بهذا الفيديو:",
                 reply_markup=get_assign_buttons())


# ═══════════════════════════════════════
# خاص: رسائل الأعضاء العاديين → القائمة فقط
# ═══════════════════════════════════════

@bot.message_handler(content_types=['text'],
                     func=lambda m: m.chat.type == 'private' and m.from_user.id != OWNER_ID
                                    and m.from_user.id not in ALERT_ADMINS)
def handle_private_message(message):
    bot.send_message(
        message.chat.id,
        "👇 اختر ما تريد معرفته:",
        reply_markup=get_main_menu()
    )


# ═══════════════════════════════════════
# معالج رسائل المجموعة
# ═══════════════════════════════════════

@bot.message_handler(content_types=['sticker', 'animation', 'video_note', 'voice'])
def ignore_media(message):
    return

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video'])
def handle_hero_logic(message):
    chat_id     = message.chat.id
    user_id     = message.from_user.id
    text        = message.text or message.caption or ""
    words       = text.split()
    word_count  = len(words)
    user_id_str = str(user_id)
    is_group    = message.chat.type in ['group', 'supergroup']

    if is_group:
        save_group(chat_id)

    # ⭐ نقطة — عرض القائمة
    if is_group and text.strip() == '.':
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        if message.reply_to_message:
            target         = message.reply_to_message.from_user
            target_mention = f"@{target.username}" if target.username else target.first_name
            pending_mention[user_id] = {
                'chat_id':           chat_id,
                'target_id':         target.id,
                'target_message_id': message.reply_to_message.message_id,
                'target_mention':    target_mention
            }
            bot.send_message(chat_id, "📋 اختر فيديو:", reply_markup=get_main_menu())
        else:
            bot.send_message(chat_id, "📋 اختر ما تريد معرفته:", reply_markup=get_main_menu())
        return

    # ⭐ أمر # — نظام الخلل الفني (للأدمن فقط)
    if is_group and text.strip() == '#' and message.reply_to_message and is_admin(chat_id, user_id):
        target_msg_id = message.reply_to_message.message_id
        session_key   = f"{chat_id}_{target_msg_id}"
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        target_user = message.reply_to_message.from_user
        target_name = target_user.first_name or ""
        if target_user.last_name:
            target_name += f" {target_user.last_name}"
        target_text = message.reply_to_message.text or message.reply_to_message.caption or ""
        threading.Thread(
            target=send_glitch_cycle,
            args=(chat_id, target_user.id, target_msg_id, session_key, 1, target_name, target_text)
        ).start()
        return

    # ⭐ رقم 1 — إرسال الصورة الإعلانية (للأدمن فقط)
    if is_group and text.strip() == '1' and is_admin(chat_id, user_id):
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        try:
            bot_info = bot.get_me()
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(
                "💬 مراسلة",
                url=f"https://t.me/{bot_info.username}?start=hi"
            ))
            bot.send_photo(chat_id, DAILY_PHOTO_URL, reply_markup=markup)
        except:
            pass
        return

    # كلمة admin من الأونر
    if text.strip().lower() == 'admin' and user_id == OWNER_ID:
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        bot_info = bot.get_me()
        bot.send_message(chat_id,
                         f"[اضغط هنا لفتح لوحة الإدارة](t.me/{bot_info.username}?start=admin)",
                         parse_mode="Markdown", disable_web_page_preview=True)
        return

    # ⭐ أمر تقيد
    if is_group and text.strip() == 'تقيد' and message.reply_to_message and is_admin(chat_id, user_id):
        target_id = message.reply_to_message.from_user.id
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        try:
            bot.restrict_chat_member(chat_id, target_id,
                telebot.types.ChatPermissions(
                    can_send_messages=False, can_send_media_messages=False,
                    can_send_other_messages=False, can_add_web_page_previews=False))
        except: pass
        return

    # ⭐ أمر فتح
    if is_group and text.strip() == 'فتح' and message.reply_to_message and is_admin(chat_id, user_id):
        target_id = message.reply_to_message.from_user.id
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        try:
            bot.restrict_chat_member(chat_id, target_id,
                telebot.types.ChatPermissions(
                    can_send_messages=True, can_send_media_messages=True,
                    can_send_other_messages=True, can_add_web_page_previews=True))
        except: pass
        return

    # حصانة القناة والروابط البيضاء
    text_has_whitelist = any(link in text.lower() for link in WHITELIST_LINKS)
    entity_urls = []
    all_entities = (message.entities or []) + (message.caption_entities or [])
    for ent in all_entities:
        if ent.type == 'url' and ent.url:
            entity_urls.append(ent.url.lower())
        elif ent.type == 'text_link' and ent.url:
            entity_urls.append(ent.url.lower())
    entity_has_whitelist = any(
        any(link in url for link in WHITELIST_LINKS)
        for url in entity_urls
    )
    if (message.forward_from_chat and message.forward_from_chat.username == 'hawk0000000') or \
       text_has_whitelist or entity_has_whitelist:
        return

    _all_ents = (message.entities or []) + (message.caption_entities or [])
    if any(e.type == 'text_mention' for e in _all_ents):
        return

    # منطق التاك @
    if '@' in text:
        if 'proxytop' in text.lower() or 'mtproto' in text.lower() or 'proxy' in text.lower():
            return
        if word_count > 1:
            try: bot.delete_message(chat_id, message.message_id)
            except: pass
        return

    if message.content_type == 'text' and is_emoji_only(text):
        return

    # حذف المحتوى المحول من قنوات أخرى
    _fwd_chat = message.forward_from_chat
    _fwd_origin = getattr(message, 'forward_origin', None)
    _is_channel_fwd = (
        (_fwd_chat and _fwd_chat.type == 'channel' and _fwd_chat.username != 'hawk0000000') or
        (_fwd_origin and getattr(_fwd_origin, 'type', None) == 'channel' and
         getattr(getattr(_fwd_origin, 'chat', None), 'username', None) != 'hawk0000000')
    )
    if _is_channel_fwd:
        if not is_admin(chat_id, user_id):
            if text.strip():
                threading.Thread(target=delete_message_after, args=(chat_id, message.message_id, 600)).start()
            return
        else:
            return

    if is_admin(chat_id, user_id):
        return

    # 🚫 محتوى إباحي → حذف + تقييد فوري
    if is_adult_content(text):
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        try:
            bot.restrict_chat_member(chat_id, user_id,
                telebot.types.ChatPermissions(
                    can_send_messages=False, can_send_media_messages=False,
                    can_send_other_messages=False, can_add_web_page_previews=False))
        except: pass
        return

    # 🚫 رابط مشبوه → حذف فوري
    if is_suspicious_url(text):
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        bot_username = bot.get_me().username
        WHITELISTED_BOTS = [bot_username.lower(), 'iiqqsk_bot']
        bot_mentioned = any(f'@{b}' in text.lower() or f't.me/{b}' in text.lower() for b in WHITELISTED_BOTS)
        if re.search(r'_bot', text, re.IGNORECASE) and not bot_mentioned:
            try:
                bot.restrict_chat_member(chat_id, user_id,
                    telebot.types.ChatPermissions(
                        can_send_messages=False, can_send_media_messages=False,
                        can_send_other_messages=False, can_add_web_page_previews=False))
            except: pass
        return

    # 🚫 بوت سبام → حذف + تقييد فوري
    bot_username = bot.get_me().username
    WHITELISTED_BOTS2 = [bot_username.lower(), 'iiqqsk_bot']
    bot_mentioned2 = any(f'@{b}' in text.lower() or f't.me/{b}' in text.lower() for b in WHITELISTED_BOTS2)
    is_bot_spam = re.search(r'@\w+_bot', text, re.IGNORECASE) or re.search(r't\.me/\w+_bot', text, re.IGNORECASE)
    if is_bot_spam and not bot_mentioned2:
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        try:
            bot.restrict_chat_member(chat_id, user_id,
                telebot.types.ChatPermissions(
                    can_send_messages=False, can_send_media_messages=False,
                    can_send_other_messages=False, can_add_web_page_previews=False))
        except: pass
        return

    # صور وفيديوهات
    if message.content_type in ['photo', 'video']:
        if word_count > 10:
            try: bot.delete_message(chat_id, message.message_id)
            except: pass
            return
        if 4 <= word_count <= 10:
            threading.Thread(target=delete_message_after, args=(chat_id, message.message_id, 300)).start()
            return
        if 2 <= word_count <= 3:
            threading.Thread(target=delete_message_after, args=(chat_id, message.message_id, 900)).start()
            return
        return

    # نصوص
    if message.content_type == 'text':
        if re.fullmatch(r'[\d\s\+\-\.،,]+', text.strip()):
            return
        if word_count >= 6:
            try: bot.delete_message(chat_id, message.message_id)
            except: pass
            return
        if user_id_str in replied_users:
            try: bot.delete_message(chat_id, message.message_id)
            except: pass
            return
        replied_users[user_id_str] = True
        save_user(user_id_str)
        threading.Thread(target=send_delayed_voice, args=(chat_id, message.message_id)).start()
        delay = 21600 if word_count <= 2 else 900
        threading.Thread(target=delete_message_after, args=(chat_id, message.message_id, delay)).start()


# ═══════════════════════════════════════
# 🔧 نظام الخلل الفني (#)
# ═══════════════════════════════════════

GLITCH_PHOTO = "https://a.top4top.io/p_3746yndx10.jpg"
FIXED_PHOTO  = "https://b.top4top.io/p_37460fvh20.jpg"

def send_glitch_cycle(chat_id, target_user_id, target_msg_id, session_key, count, target_name="", target_text=""):
    try:
        is_last = (count >= 2)
        markup  = None
        if is_last:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(
                "✅ هل تم التصليح؟",
                callback_data=f"glitch_fixed_{session_key}"
            ))
        bot.send_photo(chat_id, GLITCH_PHOTO, reply_markup=markup)
        try:
            bot.forward_message(chat_id, chat_id, target_msg_id)
        except:
            pass
        if not is_last:
            time.sleep(300)
            send_glitch_cycle(chat_id, target_user_id, target_msg_id, session_key, count + 1, target_name, target_text)
    except Exception as e:
        print(f"glitch error: {e}")

@bot.message_handler(
    func=lambda m: m.chat.type in ['group', 'supergroup'] and
                   m.text and m.text.strip() == '#' and
                   m.reply_to_message is not None,
    content_types=['text']
)
def handle_glitch_command(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    chat_id       = message.chat.id
    target_msg_id = message.reply_to_message.message_id
    target_user   = message.reply_to_message.from_user
    session_key   = f"{chat_id}_{target_msg_id}"
    try: bot.delete_message(chat_id, message.message_id)
    except: pass
    threading.Thread(
        target=send_glitch_cycle,
        args=(chat_id, target_user.id, target_msg_id, session_key, 1)
    ).start()

@bot.callback_query_handler(func=lambda call: call.data.startswith('glitch_fixed_'))
def handle_glitch_fixed(call):
    try:
        bot.send_photo(call.message.chat.id, FIXED_PHOTO)
        bot.answer_callback_query(call.id)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
    except Exception as e:
        print(f"glitch_fixed error: {e}")


# ═══════════════════════════════════════
# تشغيل البوت
# ═══════════════════════════════════════

def resolve_default_groups():
    usernames = ['FalconsofIraq']
    for username in usernames:
        try:
            chat = bot.get_chat(f'@{username}')
            save_group(chat.id)
            print(f"✅ تم تسجيل مجموعة: {chat.title} ({chat.id})")
        except Exception as e:
            print(f"⚠️ تعذر جلب {username}: {e}")

if __name__ == "__main__":
    print("✅ البوت يعمل...")
    resolve_default_groups()
    while True:
        try:
            bot.delete_webhook(drop_pending_updates=True)
            bot.infinity_polling(timeout=20, interval=2)
        except Exception as e:
            print(f"⚠️ خطأ: {e}")
            time.sleep(10)

