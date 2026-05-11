import telebot
import requests
import time
import threading
import random
import re
import os
import json
import subprocess
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Health-check server — مطلوب على Railway وإلا يقتل الـ container ──
class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK - Falcons Bot Running")
    def log_message(self, *a): pass

def _run_health_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), _HealthHandler).serve_forever()

threading.Thread(target=_run_health_server, daemon=True).start()

# ═══════════════════════════════════════
# 🔑 بيانات البوتين — تُقرأ من Railway Environment Variables
# ═══════════════════════════════════════

BOT_TOKEN        = os.environ.get('BOT_TOKEN',        '7655504363:AAEBZmKP7NzaxIvtXQejVj82cRyp5Y52B_A')
OWNER_ID         = int(os.environ.get('OWNER_ID',     '6488083580'))
ALERT_ADMINS     = {198027774}
CHANNEL          = 'https://t.me/hawk0000000'
GROUP_LINK       = "https://t.me/FalconsofIraq"

DOWNLOADER_TOKEN = os.environ.get('DOWNLOADER_TOKEN', '8266072398:AAHO8y2Vd-i-3h9MQbx_i2ui2mMl6X9RRcY')

# ═══════════════════════════════════════
# 🔞 Sightengine — كشف الصور الإباحية
# ═══════════════════════════════════════
SIGHTENGINE_USER   = os.environ.get('SIGHTENGINE_USER',   '2955790')
SIGHTENGINE_SECRET = os.environ.get('SIGHTENGINE_SECRET', 'WULHupUUetaSHwc7xRNTHY9dNsoKwc3K')

# ═══════════════════════════════════════
# 📋 القائمة البيضاء للروابط
# ═══════════════════════════════════════

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
    "uber_pay":         "💳 طريقة تسديد Uber",
    "uber_withdraw":    "💰 طريقة سحب مستحقات Uber",
    "uber_careem":      "🔗 ربط كريم في Uber",
    "uber_master":      "💳 ربط الماستر بتطبيق Uber",
    "uber_cancel":      "🔄 تعويض إلغاء الرحلة",
    "uber_block":       "🚫 منع الرحلات الجديدة",
    "uber_support":     "🆘 دعم Uber داخل التطبيق",
    "uber_appointment": "📅 حجز موعد اوبر",
    "uber_trips":       "📋 معرفة تفاصيل الرحلات",
    "baly_pay":         "💳 طريقة تسديد Baly",
    "oper_pay":         "💳 طريقة تسديد Oper",
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
            {"key": "menu_uber",   "label": "🚖 حول Uber",  "type": "submenu"},
            {"key": "baly_main",   "label": "🟢 حول Baly",  "type": "video"},
            {"key": "oper_main",   "label": "🟡 حول Oper",  "type": "video"},
        ],
        "uber": [
            {"key": "uber_pay",         "label": "💳 طريقة تسديد Uber",        "type": "video"},
            {"key": "uber_withdraw",    "label": "💰 طريقة سحب مستحقات Uber",  "type": "video"},
            {"key": "uber_careem",      "label": "🔗 ربط كريم في Uber",         "type": "video"},
            {"key": "uber_master",      "label": "💳 ربط الماستر بتطبيق Uber", "type": "video"},
            {"key": "uber_cancel",      "label": "🔄 تعويض إلغاء الرحلة",      "type": "video"},
            {"key": "uber_block",       "label": "🚫 منع الرحلات الجديدة",     "type": "video"},
            {"key": "uber_support",     "label": "🆘 دعم Uber داخل التطبيق",   "type": "video"},
            {"key": "uber_appointment", "label": "📅 حجز موعد اوبر",           "type": "video"},
            {"key": "uber_trips",       "label": "📋 معرفة تفاصيل الرحلات",    "type": "video"},
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
    "oper_pay":         "BAACAgIAAxkBAAIDGGmbIPGGhh4Q2OkKCjDHP20p9iweAAKHlwACv-DYSG4MDukpCf0tOgQ",
    "baly_pay":         "BAACAgIAAxkBAAIDGmmbIRJixuRz2Q8bfgJ9BIDW57_0AAKJlwACv-DYSA-mro42hfb3OgQ",
    "uber_withdraw":    "BAACAgIAAxkBAAIChGmawtpFjG-Y-os3JJia_fcLtxXZAAI_kgACv-DYSDiXe_Ej73KjOgQ",
    "uber_careem":      "BAACAgIAAxkBAAIC5mmbBndewCwKXr_or9mitgjKlSpDAAL6lQACv-DYSLfZGzJ-cvWpOgQ",
    "uber_master":      "BAACAgIAAxkBAAIC3GmbATBbMwd9OaRMDd0J05FNlnpjAALkhwACZV_RS5rI8WmK3zJ1OgQ",
    "uber_support":     "BAACAgIAAxkBAAIC1mmbAAFWjjXaphG0vnstNi3CnfWcTQACgpUAAqtp6EtWakIboxiqbjoE",
    "uber_block":       "BAACAgIAAxkBAAIC02mbAAE4iYfKQk6pwa6aZX8q3tf3FwAC95wAAhQ7aEimz619q9l_eDoE",
    "uber_cancel":      "BAACAgIAAxkBAAICjGmaw7FSiQvkdv99yPoujWKfSirWAAJWnQACFDtoSLXKf446_9NnOgQ",
    "uber_pay":         "BAACAgIAAxkBAAID5mmlkRH-iaBVRCS_kW-R7MSCU_9RAAITjwAC5XsQSVw4Yd0kWt23OgQ",
    "uber_appointment": "BAACAgIAAxkBAAIJhmnvG7XbDdID4rqFYEOLQLRV5cdBAAKRmAACbMN4S6NFtPowBL9COwQ",
    "uber_trips":       "BAACAgIAAxkBAAIJiWnvHCc5cl3738RZDWOFjV6DYuTFAAKVmAACbMN4S2jihbimI3NEOwQ",
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

# ═══════════════════════════════════════
# 🚫 الكلمات المحظورة في البصمات الصوتية
# ═══════════════════════════════════════

VOICE_BANNED_WORDS = [
    'امبعبص', 'كس', 'طيز', 'عير', 'عيري', 'امكس',
    'ابن القندرة', 'ابن النعال',
    'انعل ابوكم', 'انعل ابوك',
    'خره بشرفكم', 'خره بشرفك',
    'الكحبه', 'كحبه', 'كحبة', 'الكحبة', 'قحبه', 'قحبة',
    'منيجه', 'منيجة', 'دودكي',
    'فرخ', 'منيوك', 'تنيج', 'ينيج', 'تنيك', 'ينيك',
    'ساقطه', 'ساقطة', 'منيوجه', 'منيوكه',
    'زربه', 'خريه', 'كسي', 'زبي',
    'كساسه', 'بعابيص', 'دمبك', 'دمبك عيري', 'دنبق', 'عيوره',
    'بلاع', 'كسكوسي', 'طيزها', 'طيزي',
    'زبزوبي', 'اطياز', 'شرموطة', 'شرموطه',
    'نياك', 'زوبي', 'كوسي', 'كوس',
    'كلب', 'ابن الكلب', 'ابن السافل', 'ابن السافله',
    'بنت الكلب', 'بنت النعال', 'بنت الزمال',
    'ابن الزمال', 'ابن الخره', 'ابن القندره', 'ابن الزربه',
    'سني', 'شيعي', 'شيعة', 'شيعه', 'سنة',
    'بربوك', 'باربوك', 'ابن الحمار', 'الشيعة',
    'الشيعه', 'السنة', 'كواد',
]

_WORD_WHITELIST = {
    'كس':  ['تكسي', 'التكسي', 'تاكسي', 'التاكسي', 'ماكسي', 'باكستاني', 'باكستان', 'بلكسن', 'بلك سن', 'بلكسنن', 'كسور', 'كسارات', 'كسرا', 'كسبت'],
    'كلب': ['جلب', 'الجلب', 'يجلب', 'جلبت', 'جلبوا'],
    'ابن الزمال':  ['زمال', 'الزمال', 'زماله', 'الزماله', 'زمالة', 'الزمالة'],
    'بنت الزمال': ['زمال', 'الزمال', 'زماله', 'الزماله', 'زمالة', 'الزمالة'],
}

_GLOBAL_SAFE_WORDS = {
    'سنه', 'سنة', 'سنا', 'سنتين', 'سنوات', 'سنين',
    'تكسي', 'التكسي', 'تاكسي', 'التاكسي',
    'تكسيات', 'التكسيات', 'تاكسيات', 'التاكسيات',
    'جلب', 'الجلب', 'يجلب', 'جلبت', 'جلبوا',
    'زمال', 'الزمال', 'زماله', 'الزماله', 'زمالة', 'الزمالة',
    'مطي', 'المطي', 'مطية', 'المطية', 'مطيه', 'المطيه',
}

def _bare_word_present(word: str, text_lower: str) -> bool:
    pattern = r'(?<![^\W\d_\u0600-\u06FF])' + re.escape(word) + r'(?![^\W\d_\u0600-\u06FF])'
    if bool(re.search(pattern, text_lower, re.IGNORECASE)):
        return True
    return word in text_lower

def _is_word_match(word: str, text_lower: str) -> bool:
    if word.lower() in _GLOBAL_SAFE_WORDS:
        return False
    cleaned = text_lower
    all_safe = list(_GLOBAL_SAFE_WORDS) + _WORD_WHITELIST.get(word.lower(), [])
    for safe_word in all_safe:
        pattern_safe = r'(?<![^\W\d_\u0600-\u06FF])' + re.escape(safe_word.lower()) + r'(?![^\W\d_\u0600-\u06FF])'
        cleaned = re.sub(pattern_safe, ' ', cleaned)
    return _bare_word_present(word.lower(), cleaned)

def contains_banned_voice_word(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower().strip()
    for word in VOICE_BANNED_WORDS:
        if _is_word_match(word, text_lower):
            return True
    return False

def get_found_banned_word(text: str) -> str:
    if not text:
        return ""
    text_lower = text.lower().strip()
    for word in VOICE_BANNED_WORDS:
        if _is_word_match(word, text_lower):
            return word
    return ""

def is_adult_content(text):
    if not text:
        return False
    text_lower = text.lower()
    for kw in ADULT_KEYWORDS:
        if _is_word_match(kw, text_lower):
            return True
    return False

def is_suspicious_url(text):
    if not text:
        return False
    url_pattern = re.compile(r'(https?://\S+|www\.\S+)', re.IGNORECASE)
    if not url_pattern.search(text):
        return False
    return not any(link in text.lower() for link in WHITELIST_LINKS)

def is_downloadable_url(text):
    if not text:
        return False
    download_patterns = [
        'youtube.com/watch', 'youtu.be/', 'youtube.com/shorts',
        'youtube.com/live', 'youtube.com/embed',
        'tiktok.com/', 'vm.tiktok.com/', 'vt.tiktok.com/',
        'instagram.com/reel', 'instagram.com/reels',
        'instagram.com/p/', 'instagram.com/tv/',
        'instagram.com/stories/',
        'facebook.com/watch', 'facebook.com/share/',
        'facebook.com/videos/', 'facebook.com/reel',
        'fb.watch/', 'fb.com/',
        'twitter.com/', 'x.com/',
        'twitch.tv/', 'vimeo.com/',
        'dailymotion.com/video', 'dai.ly/',
        'snapchat.com/spotlight',
    ]
    return any(p in text.lower() for p in download_patterns)

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
        bot.send_voice(
            chat_id, chosen_voice,
            caption=CHANNEL,
            reply_to_message_id=message_id,
        )
    except:
        pass

# ═══════════════════════════════════════
# قوائم الأزرار
# ═══════════════════════════════════════

def get_main_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🚖 حول Uber",      callback_data="menu_uber"),
        telebot.types.InlineKeyboardButton("🟢 حول Baly",      callback_data="menu_baly"),
        telebot.types.InlineKeyboardButton("🟡 حول Oper",      callback_data="menu_oper"),
        telebot.types.InlineKeyboardButton("💳 ماستر كارد",    callback_data="menu_mastercard"),
        telebot.types.InlineKeyboardButton("⛽ محطات الغاز",   callback_data="menu_gas"),
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
        telebot.types.InlineKeyboardButton("🔙 رجوع",       callback_data="menu_back"),
    )
    return markup

def get_oper_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("💳 تسديد Oper", callback_data="btn_oper_pay"),
        telebot.types.InlineKeyboardButton("🔙 رجوع",       callback_data="menu_back"),
    )
    return markup

def get_mastercard_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🔧 حل مشكلة الماستر كارد", callback_data="mc_fix"),
        telebot.types.InlineKeyboardButton("💳 الحصول على الماستر",    callback_data="mc_get"),
        telebot.types.InlineKeyboardButton("🔙 رجوع",                  callback_data="menu_back"),
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
    markup.add(telebot.types.InlineKeyboardButton("🔙 رجوع",       callback_data="adm_back"))
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

    if data == "menu_gas":
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("🗺 فتح خريطة محطات الغاز", web_app=telebot.types.WebAppInfo(url="https://beautiful-melba-ea1a00.netlify.app/")),
        )
        bot.send_message(chat_id, "⛽ اضغط على الزر أدناه لفتح خريطة محطات الغاز:", reply_markup=markup)
        bot.answer_callback_query(call.id)
        return

    if data == "mc_fix":
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        try:
            bot.send_video(
                chat_id,
                "BAACAgIAAxkBAAIJDmnogyobeAzRreu4_q0o2rcPQLlhAAIpogACHxVAS0e-x-MgxJtTOwQ",
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
                "BAACAgIAAxkBAAIJe2nrzi2lV5uHV4aFr64JDE-Fzv2mAAL4lQACO4phS-8b_ZujIcceOwQ",
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
        markup.add(telebot.types.InlineKeyboardButton("📍 تجمع",                   callback_data="adm_gather"))
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
        section   = state['section']
        key       = state['key']
        new_label = message.text.strip()
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
        section   = state['section']
        key       = state['key']
        label     = state['label']
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
                bot.send_photo(gid, file_id, caption=GROUP_LINK)
                success += 1
            except:
                pass
        bot.reply_to(message, f"✅ تم إرسال التنبيه إلى {success} مجموعة!")
        return

    bot.reply_to(message, "⚠️ نوع غير صحيح، حاول مجدداً من /admin")


# ═══════════════════════════════════════
# خاص: استقبال فيديو من الأونر للحفظ
# ═══════════════════════════════════════

@bot.message_handler(content_types=['photo'],
                     func=lambda m: m.chat.type == 'private' and m.from_user.id == OWNER_ID)
def handle_private_photo(message):
    if message.from_user.id in pending_admin:
        return
    file_id = message.photo[-1].file_id
    bot.reply_to(message, f"🖼 <b>File ID الصورة:</b>\n<code>{file_id}</code>", parse_mode="HTML")

@bot.message_handler(content_types=['video'],
                     func=lambda m: m.chat.type == 'private' and m.from_user.id == OWNER_ID)
def handle_private_video(message):
    if message.from_user.id in pending_admin:
        return
    file_id = message.video.file_id
    pending_video[message.from_user.id] = file_id
    bot.reply_to(message, f"🆔 <b>File ID:</b>\n<code>{file_id}</code>", parse_mode="HTML")
    bot.send_message(message.chat.id, "📹 اختر الزر الذي تريد ربطه بهذا الفيديو:",
                     reply_markup=get_assign_buttons())


# ═══════════════════════════════════════
# خاص: رسائل الأعضاء العاديين
# ═══════════════════════════════════════

@bot.message_handler(content_types=['text'],
                     func=lambda m: m.chat.type == 'private' and m.from_user.id != OWNER_ID
                                    and m.from_user.id not in ALERT_ADMINS)
def handle_private_message(message):
    text = message.text.strip() if message.text else ""

    if is_downloadable_url(text):
        threading.Thread(
            target=download_and_send_video,
            args=(bot, message.chat.id, message.message_id, text),
            daemon=True
        ).start()
        return

    bot.send_message(
        message.chat.id,
        "👇 اختر ما تريد معرفته:",
        reply_markup=get_main_menu()
    )


# ═══════════════════════════════════════
# 🎬 دالة التحميل الموحدة المصلحة
# ═══════════════════════════════════════

def download_and_send_video(bot_instance, chat_id, reply_to_id, url):
    """دالة موحدة للتحميل — تعمل مع البوت الرئيسي وبوت التحميل"""

    if not YT_DLP_AVAILABLE:
        try:
            bot_instance.send_message(chat_id, "⚠️ خدمة التحميل غير متاحة حالياً.",
                                      reply_to_message_id=reply_to_id)
        except: pass
        return

    # تصحيح رابط Shorts
    if 'shorts/' in url:
        url = url.replace('shorts/', 'watch?v=')

    try:
        status_msg = bot_instance.send_message(
            chat_id,
            "الصقور تحملك الفيديو انتظر يابطل 🦅🔥",
            reply_to_message_id=reply_to_id
        )
    except:
        return

    filename_base = f"video_{chat_id}_{int(time.time())}"

    # ── خيارات yt_dlp — نفس إعدادات البوت الأصلي الذي يعمل ──
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{filename_base}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'socket_timeout': 30,
        'retries': 5,
        'user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/121.0.0.0 Safari/537.36'
        ),
        'http_headers': {
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
        },
    }

    downloaded_file = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # ── البحث الموثوق عن الملف المحمَّل ──
            # الطريقة 1: prepare_filename
            guessed = ydl.prepare_filename(info)

            # الطريقة 2: البحث في المجلد لو الامتداد تغيّر
            if not os.path.exists(guessed):
                for f in os.listdir('.'):
                    if f.startswith(filename_base) and not f.endswith('.part') and not f.endswith('.ytdl'):
                        guessed = f
                        break

            downloaded_file = guessed

        if not downloaded_file or not os.path.exists(downloaded_file):
            raise FileNotFoundError("الملف لم يُحمَّل بشكل صحيح")

        # ── فحص الحجم (50MB حد تيليغرام) ──
        file_size = os.path.getsize(downloaded_file)
        if file_size > 50 * 1024 * 1024:
            try:
                bot_instance.edit_message_text(
                    "⚠️ الفيديو أكبر من 50MB، لا يمكن إرساله عبر تيليغرام.",
                    chat_id, status_msg.message_id
                )
            except: pass
            return

        # ── إرسال الفيديو ──
        with open(downloaded_file, 'rb') as video_file:
            bot_instance.send_video(
                chat_id,
                video_file,
                caption=GROUP_LINK,
                supports_streaming=True,
                timeout=120
            )

        try: bot_instance.delete_message(chat_id, status_msg.message_id)
        except: pass

    except yt_dlp.utils.DownloadError as e:
        err_str = str(e).lower()
        print(f"❌ DownloadError: {e}")

        if 'private' in err_str:
            user_msg = "⚠️ الفيديو خاص أو محمي، لا يمكن تحميله."
        elif 'age' in err_str:
            user_msg = "⚠️ الفيديو مقيد بالعمر."
        elif 'copyright' in err_str:
            user_msg = "⚠️ الفيديو محمي بحقوق النشر."
        elif 'unavailable' in err_str or 'removed' in err_str or 'not exist' in err_str:
            user_msg = "⚠️ الفيديو غير متاح أو تم حذفه."
        elif 'login' in err_str or 'sign in' in err_str:
            user_msg = "⚠️ هذا الفيديو يتطلب تسجيل دخول."
        else:
            user_msg = "⚠️ حدث خطأ في التحميل. تأكد من الرابط وحاول مجدداً."

        try:
            bot_instance.edit_message_text(user_msg, chat_id, status_msg.message_id)
        except: pass

    except FileNotFoundError as e:
        print(f"❌ FileNotFoundError: {e}")
        try:
            bot_instance.edit_message_text(
                "⚠️ فشل التحميل. الرابط غير مدعوم أو انتهت صلاحيته.",
                chat_id, status_msg.message_id
            )
        except: pass

    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        try:
            bot_instance.edit_message_text(
                "⚠️ حدث خطأ غير متوقع. حاول مرة أخرى.",
                chat_id, status_msg.message_id
            )
        except: pass

    finally:
        # ── حذف جميع الملفات المؤقتة ──
        for f in os.listdir('.'):
            if f.startswith(filename_base):
                try: os.remove(f)
                except: pass


# ═══════════════════════════════════════
# معالج رسائل المجموعة
# عداد الصور الإباحية لكل مستخدم
nsfw_violations = {}

def check_and_delete_nsfw(chat_id, message_id, user_id, file_id):
    try:
        file_info = bot.get_file(file_id)
        file_url  = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        response  = requests.get(
            'https://api.sightengine.com/1.0/check.json',
            params={
                'url':        file_url,
                'models':     'nudity-2.0',
                'api_user':   SIGHTENGINE_USER,
                'api_secret': SIGHTENGINE_SECRET,
            },
            timeout=10
        )
        result = response.json()
        nudity = result.get('nudity', {})
        score  = max(
            nudity.get('sexual_activity', 0),
            nudity.get('sexual_display', 0),
            nudity.get('erotica', 0),
        )
        print(f"🔞 فحص صورة — نتيجة: {score:.2f}")
        if score >= 0.5:
            try: bot.delete_message(chat_id, message_id)
            except: pass
            nsfw_violations[user_id] = nsfw_violations.get(user_id, 0) + 1
            count = nsfw_violations[user_id]
            print(f"🚫 صورة إباحية — المستخدم {user_id} — المرة {count}")
            if count >= 3:
                try:
                    bot.restrict_chat_member(
                        chat_id, user_id,
                        telebot.types.ChatPermissions(
                            can_send_messages=False,
                            can_send_media_messages=False,
                            can_send_other_messages=False,
                            can_add_web_page_previews=False
                        )
                    )
                    nsfw_violations[user_id] = 0
                    print(f"🔒 تم تقييد المستخدم {user_id} بعد 3 مخالفات")
                except: pass
    except Exception as e:
        print(f"⚠️ خطأ في فحص الصورة: {e}")

# ═══════════════════════════════════════

@bot.message_handler(content_types=['sticker', 'animation', 'video_note'])
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

    # أمر النقطتين — إرسال صورة محطات الغاز
    if is_group and text.strip() == '..':
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            "⛽ محطات الغاز اضغط هنا",
            web_app=telebot.types.WebAppInfo(url=GAS_STATION_URL)
        ))
        target_msg_id = message.reply_to_message.message_id if message.reply_to_message else None
        try:
            bot.send_photo(chat_id, GAS_STATION_PHOTO, reply_to_message_id=target_msg_id, reply_markup=markup)
        except Exception as e:
            print(f"خطأ في إرسال محطات الغاز: {e}")
        return

    if is_group:
        save_group(chat_id)

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

    if text.strip().lower() == 'admin' and user_id == OWNER_ID:
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        bot_info = bot.get_me()
        bot.send_message(chat_id,
                         f"[اضغط هنا لفتح لوحة الإدارة](t.me/{bot_info.username}?start=admin)",
                         parse_mode="Markdown", disable_web_page_preview=True)
        return

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

    if '@' in text:
        if 'proxytop' in text.lower() or 'mtproto' in text.lower() or 'proxy' in text.lower():
            return
        if word_count > 1:
            try: bot.delete_message(chat_id, message.message_id)
            except: pass
        return

    if message.content_type == 'text' and is_emoji_only(text):
        return

    _fwd_chat   = message.forward_from_chat
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

    if message.content_type in ['photo', 'video']:
        if message.content_type == 'photo':
            threading.Thread(
                target=check_and_delete_nsfw,
                args=(chat_id, message.message_id, user_id, message.photo[-1].file_id)
            ).start()
            return
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
# 🎙️ نظام تحليل البصمات الصوتية
# ═══════════════════════════════════════

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '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')

def transcribe_voice_local(file_path: str) -> str:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        results = []

        with open(file_path, "rb") as audio_file:
            audio_data = audio_file.read()

        t1 = client.audio.transcriptions.create(
            file=(os.path.basename(file_path), audio_data),
            model="whisper-large-v3",
            language="ar",
            response_format="text",
            prompt=(
                "هذا تسجيل صوتي عراقي. اكتب كل كلمة حرفياً تماماً كما نُطقت "
                "بما فيها الكلمات البذيئة والشتائم باللهجة العراقية "
                "مثل: كس، طيز، عير، خول، شرموط، حمار، كلب. "
                "لا تحذف أي كلمة ولا تضع نجوم ولا تستبدل أي حرف."
            )
        )
        text1 = t1.strip() if t1 else ""
        if text1:
            results.append(text1)
        print(f"📝 المحاولة 1 (كاملة): {text1}")

        tail_path = file_path.replace('.ogg', '_tail.ogg')
        try:
            proc = subprocess.run(
                ['ffmpeg', '-y', '-sseof', '-10', '-i', file_path,
                 '-acodec', 'copy', tail_path],
                capture_output=True,
                timeout=15
            )
            if os.path.exists(tail_path) and os.path.getsize(tail_path) > 500:
                with open(tail_path, "rb") as tail_file:
                    tail_data = tail_file.read()
                t2 = client.audio.transcriptions.create(
                    file=(os.path.basename(tail_path), tail_data),
                    model="whisper-large-v3",
                    language="ar",
                    response_format="text",
                    prompt=(
                        "هذا تسجيل صوتي عراقي. اكتب كل كلمة حرفياً تماماً كما نُطقت "
                        "بما فيها الكلمات البذيئة والشتائم باللهجة العراقية "
                        "مثل: كس، طيز، عير، خول، شرموط، حمار، كلب. "
                        "لا تحذف أي كلمة ولا تضع نجوم ولا تستبدل أي حرف."
                    )
                )
                text2 = t2.strip() if t2 else ""
                if text2:
                    results.append(text2)
                print(f"📝 المحاولة 2 (النهاية): {text2}")
        except Exception as e:
            print(f"⚠️ خطأ في استخراج النهاية: {e}")
        finally:
            if os.path.exists(tail_path):
                try: os.remove(tail_path)
                except: pass

        combined = ' '.join(results).strip()
        print(f"📝 النص المدمج النهائي: {combined}")
        return combined

    except Exception as e:
        print(f"⚠️ خطأ في تحويل الصوت: {e}")
        return ""


ADMIN_GROUP_ID = -1003746150788

GREETING_WORDS = [
    'صباح الخير', 'مساء الخير', 'شلونكم', 'شلونك',
    'يسعد صباحكم', 'يسعد مسائكم', 'يسعد صباحك', 'يسعد مساءك',
    'صباحكم خير', 'صبحكم الله بالخير', 'صبحكم بالخير',
    'السلام عليكم شلونكم', 'السلام عليكم',
    'يسعد صباحكم', 'مرحبا', 'هلا', 'أهلاً', 'اهلا',
    'تصبحون على خير', 'تمسون على خير',
]

UBER_PAY_TRIGGERS = [
    'تسديد اوبر', 'طريقة تسديد اوبر', 'كيف تسديد اوبر',
    'كيف اسدد اوبر', 'اريد اسدد اوبر',
    'كيف يمكنني تسديد اوبر', 'كيف يمكنني الدفع لاوبر',
    'شلون اسدد اوبر', 'شلون اصدد اوبر',
    'شلون طريقة تسديد اوبر', 'شلون طريقه تسديد اوبر',
    'اخوان شلون اسدد اوبر', 'شباب شلون اسدد اوبر',
    'ماعرف اسدد اوبر', 'ما اعرف اسدد اوبر',
    'مو عارف اسدد اوبر', 'مو عارف كيف اسدد',
    'ما اعرف كيف اسدد', 'ماعرف كيف اسدد',
    'تسديد ابر', 'شلون اسدد ابر', 'طريقة تسديد ابر',
    'شلون ادفع اوبر', 'كيف ادفع اوبر', 'ادفع اوبر',
    'طريقة الدفع اوبر', 'الدفع لاوبر',
    'شلون اخلص ذمتي باوبر', 'شلون اخلص ذمتي',
    'اوبر تريد فلوس', 'اوبر تطلب فلوس',
    'عندي مبلغ باوبر', 'عندي ديون باوبر',
    'شلون اسوي تسديد', 'اسوي تسديد اوبر',
]

UBER_WITHDRAW_TRIGGERS = [
    'سحب مستحقات اوبر', 'طريقة سحب مستحقات اوبر',
    'سحب الفلوس اوبر', 'كيف اسحب من اوبر',
    'طريقة السحب اوبر', 'سحب المستحقات',
    'شلون اسحب فلوسي', 'شلون اسحب فلوسي باوبر',
    'شباب شلون اسحب فلوسي', 'اخوان شلون اسحب فلوسي',
    'احد يعرف شلون اسحب فلوسي',
    'فلوسي باوبر', 'فلوسي بأوبر', 'اسحب فلوسي',
    'مستحقات اوبر', 'سحب اوبر',
    'شلون اطلع فلوسي من اوبر', 'شلون اشيل فلوسي من اوبر',
    'اريد اشيل فلوسي', 'اريد اطلع فلوسي',
    'فلوسي محجوزه باوبر', 'فلوسي محبوسه باوبر',
    'ارباحي باوبر', 'شلون اسحب ارباحي',
    'اموالي باوبر', 'شلون اطلع اموالي',
    'حسابي باوبر فيه فلوس', 'شلون اسحب من حسابي',
    'شلون اسحب فلوسي بكريم', 'شلون اسحب فلوسي من كريم',
    'سحب فلوسي من كريم', 'سحب مستحقات كريم',
    'كيف اسحب من كريم', 'شلون اسحب من كريم',
    'فلوسي بكريم', 'مستحقات كريم',
    'اسحب فلوسي من كريم', 'اطلع فلوسي من كريم',
    'ارباحي بكريم', 'شلون اطلع فلوسي من كريم',
]

UBER_CAREEM_TRIGGERS = [
    'ربط كريم', 'ربط كريم باوبر', 'ربط كريم في اوبر',
    'طريقة ربط كريم', 'كريم واوبر', 'كريم في اوبر',
    'شلون اربط كريم', 'كيف اربط كريم',
    'شلون اربط كريم باوبر', 'شلون اربط كريم في اوبر',
    'شلون اوصل كريم باوبر', 'شلون اوصل كريم',
    'اربط كريم باوبر', 'اربط كريم في اوبر',
    'شلون اخلي كريم يشتغل باوبر',
    'كريم واوبر وين اربطهم', 'شباب كريم واوبر',
    'عندي كريم شلون اربطه', 'عندي حساب كريم',
    'شلون اضيف كريم', 'اضيف كريم باوبر',
]

UBER_MASTER_TRIGGERS = [
    'ربط الماستر', 'ربط ماستر', 'ربط الماستر باوبر',
    'طريقة ربط الماستر', 'ربط ماستر كارد',
    'اضافة ماستر', 'اضافة الماستر',
    'شلون اربط الماستر', 'كيف اربط الماستر',
    'شلون اربط الماستر باوبر', 'شلون اربط ماستر باوبر',
    'شلون اضيف الماستر', 'شلون اضيف ماستر كارد',
    'اضيف الماستر باوبر', 'اضيف ماستر باوبر',
    'شلون اوصل الماستر', 'شلون اوصل البطاقه',
    'ماستر كارد اوبر', 'بطاقتي باوبر',
    'شلون اربط بطاقتي', 'اربط بطاقتي باوبر',
    'شلون اضيف بطاقه', 'اضيف بطاقه باوبر',
    'شلون اشغل الماستر باوبر', 'الماستر مو شغال باوبر',
]

UBER_CANCEL_TRIGGERS = [
    'تعويض الغاء', 'تعويض الالغاء', 'تعويض الرحله',
    'احصل على تعويض', 'اطلب تعويض',
    'شلون احصل تعويض', 'كيف احصل تعويض',
    'شلون اطلب تعويض', 'كيف اطلب تعويض',
    'الزبون الغى الرحله', 'الزبون كنسل',
    'الزبون كنسل علي', 'الكاستمر كنسل',
    'شلون استرد فلوسي', 'استرد فلوسي من اوبر',
    'الرحله انكنسلت', 'الرحله اتلغت',
    'رحلتي انلغت شلون', 'رحلتي اتكنسلت',
    'شلون احصل على حقي', 'حقي من الغاء الرحله',
    'الغو الرحله علي', 'كنسلوا علي',
    'شلون اشتكي على زبون الغى', 'اشتكي على كنسل',
    'زبون كنسل شلون اخذ فلوسي',
]

UBER_SUPPORT_TRIGGERS = [
    'دعم اوبر', 'كول سنتر اوبر', 'خدمة عملاء اوبر',
    'التواصل مع اوبر', 'اراسل الدعم', 'اراسل اوبر',
    'شلون اراسل الدعم', 'كيف اراسل الدعم',
    'شلون اراسل اوبر', 'كيف اراسل اوبر',
    'شلون اراسل الكول سنتر', 'شلون اراسل الشركه',
    'شلون اتواصل مع اوبر', 'كيف اتواصل مع اوبر',
    'شلون احجي مع اوبر', 'شلون اكلم اوبر',
    'اكلم اوبر', 'احجي مع اوبر', 'احجي مع الشركه',
    'شلون اكلم الكول سنتر', 'اكلم الكول سنتر',
    'وين الدعم مال اوبر', 'وين كول سنتر اوبر',
    'شلون اراسل دعم اوبر', 'اراسل دعم اوبر',
    'شلون افتح تذكره', 'افتح تذكره باوبر',
    'شلون ارفع شكوى', 'ارفع شكوى باوبر',
    'عندي مشكله باوبر شلون', 'عندي مشكلة باوبر',
    'شلون اشتكي باوبر', 'اشتكي باوبر',
    'شلون اتواصل ويه الدعم', 'اتواصل ويه الدعم',
    'شلون اتواصل ويه اوبر', 'اتواصل ويه اوبر',
    'شلون احجي ويه اوبر', 'احجي ويه اوبر',
    'شلون اراسل الدعم مال اوبر', 'اراسل الدعم مال اوبر',
    'الدعم مال اوبر', 'الدعم مالت اوبر',
    'احد يعملني شلون اتواصل ويه الدعم',
    'احد يعلمني شلون اتواصل ويه الدعم',
    'اكو طريقه اتواصل ويه الدعم', 'اكو طريقه اتواصل مع الدعم',
    'طريقه اتواصل ويه اوبر', 'طريقه التواصل ويه اوبر',
    'ويه الدعم مال اوبر', 'ويه دعم اوبر',
]

UBER_TRIPS_TRIGGERS = [
    'تفاصيل الرحله', 'تفاصيل الرحلة', 'سجل الرحلات',
    'تاريخ الرحلات', 'تفاصيل رحلاتي',
    'شلون اعرف تفاصيل الرحله', 'كيف اعرف تفاصيل الرحله',
    'شلون اطلع الرحله', 'كيف اطلع الرحله',
    'شلون اشوف الرحله', 'كيف اشوف الرحله',
    'هاي رحله شلون اطلعها', 'هاي رحلة شلون اطلعها',
    'شلون اشوف رحلاتي', 'اشوف رحلاتي',
    'شلون اطلع رحلاتي', 'اطلع رحلاتي',
    'رحلاتي وين اشوفها', 'رحلاتي وين اطلعها',
    'شلون اعرف كم رحله سويت', 'كم رحله سويت',
    'شلون اشوف تفاصيل رحله قديمه',
    'الرحله الفلانيه شلون اطلع تفاصيلها',
    'فلوس الرحله وين اشوفها', 'كم اخذت من الرحله',
    'شلون اعرف كم اخذت', 'اعرف كم ربحت',
]

def _normalize_arabic(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[أإآا][\s\.]*[ؤو][\s\.]*ب[\s\.]*[اأآ][\s\.]*ر', 'اوبر', text)
    text = re.sub(r'[أإآا][\s\.]*ب[\s\.]*[اأآ][\s\.]*ر', 'اوبر', text)
    text = re.sub(r'[أإآا][\s\.]*ب[\s\.]*ر', 'اوبر', text)
    text = re.sub(r'u[\s\.]?b[\s\.]?e[\s\.]?r', 'اوبر', text, flags=re.IGNORECASE)
    text = re.sub(r'[أإآا]', 'ا', text)
    text = re.sub(r'[ةه]', 'ه', text)
    text = re.sub(r'[يى]', 'ي', text)
    text = re.sub(r'[ؤو]', 'و', text)
    text = re.sub(r'[\u064B-\u065F]', '', text)
    return text.lower().strip()

def contains_uber_withdraw_question(text: str) -> bool:
    if not text:
        return False
    norm = _normalize_arabic(text)
    for phrase in UBER_WITHDRAW_TRIGGERS:
        if _normalize_arabic(phrase) in norm:
            return True
    has_app = 'اوبر' in norm or 'كريم' in norm
    has_withdraw = any(w in norm for w in ['سحب', 'اسحب', 'مستحقات', 'فلوس', 'ارباح', 'السحب', 'اشيل', 'اطلع'])
    if has_app and has_withdraw:
        return True
    return False

def contains_uber_pay_question(text: str) -> bool:
    if not text:
        return False
    norm = _normalize_arabic(text)
    for phrase in UBER_PAY_TRIGGERS:
        if _normalize_arabic(phrase) in norm:
            return True
    has_uber = 'اوبر' in norm
    has_pay  = any(w in norm for w in ['تسديد', 'اسدد', 'اصدد', 'دفع', 'سدد', 'التسديد', 'الدفع'])
    if has_uber and has_pay:
        return True
    return False

def contains_uber_careem_question(text: str) -> bool:
    if not text:
        return False
    norm = _normalize_arabic(text)
    for phrase in UBER_CAREEM_TRIGGERS:
        if _normalize_arabic(phrase) in norm:
            return True
    has_careem = 'كريم' in norm
    has_uber   = 'اوبر' in norm
    has_link   = any(w in norm for w in ['ربط', 'اربط', 'توصيل', 'وصل'])
    if has_careem and (has_uber or has_link):
        return True
    return False

def contains_uber_master_question(text: str) -> bool:
    if not text:
        return False
    norm = _normalize_arabic(text)
    for phrase in UBER_MASTER_TRIGGERS:
        if _normalize_arabic(phrase) in norm:
            return True
    has_master = any(w in norm for w in ['ماستر', 'master', 'بطاقه', 'بطاقة', 'كارد'])
    has_link   = any(w in norm for w in ['ربط', 'اربط', 'اضافه', 'اضافة', 'اضيف'])
    if has_master and has_link:
        return True
    return False

def contains_uber_cancel_question(text: str) -> bool:
    if not text:
        return False
    norm = _normalize_arabic(text)
    for phrase in UBER_CANCEL_TRIGGERS:
        if _normalize_arabic(phrase) in norm:
            return True
    has_cancel = any(w in norm for w in ['الغاء', 'الغت', 'الغيت', 'الغو'])
    has_comp   = any(w in norm for w in ['تعويض', 'احصل', 'اطلب', 'فلوس', 'مبلغ'])
    if has_cancel and has_comp:
        return True
    return False

def contains_uber_support_question(text: str) -> bool:
    if not text:
        return False
    norm = _normalize_arabic(text)
    for phrase in UBER_SUPPORT_TRIGGERS:
        if _normalize_arabic(phrase) in norm:
            return True
    has_uber    = 'اوبر' in norm or 'الدعم' in norm
    has_support = any(w in norm for w in ['دعم', 'سبورت', 'كول سنتر', 'كولسنتر', 'اراسل', 'اتواصل', 'احجي', 'اكلم', 'خدمه', 'خدمة', 'شركه', 'شركة', 'ويه', 'مال اوبر', 'مالت اوبر'])
    if has_uber and has_support:
        return True
    if 'ويه' in norm and 'دعم' in norm:
        return True
    if 'الدعم مال' in norm or 'الدعم مالت' in norm:
        return True
    return False

def contains_uber_trips_question(text: str) -> bool:
    if not text:
        return False
    norm = _normalize_arabic(text)
    for phrase in UBER_TRIPS_TRIGGERS:
        if _normalize_arabic(phrase) in norm:
            return True
    has_trip    = any(w in norm for w in ['رحله', 'رحلة', 'رحلات', 'تريب', 'trip'])
    has_details = any(w in norm for w in ['تفاصيل', 'اطلع', 'اشوف', 'اعرف', 'سجل', 'تاريخ', 'معلومات'])
    if has_trip and has_details:
        return True
    return False

def contains_greeting(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower().strip()
    for word in GREETING_WORDS:
        if word.lower() in text_lower:
            return True
    return False

# ═══════════════════════════════════════
# 🔍 تحليل البصمة الصوتية وحذفها
# ═══════════════════════════════════════

def _check_banned_in_text(text: str) -> str:
    """يفحص النص كاملاً فقط — لا يقطعه حتى لا تحصل إيجابيات كاذبة"""
    if not text:
        return ""
    return get_found_banned_word(text)

def analyze_and_delete_voice(bot_instance, chat_id, message_id, file_path):
    try:
        combined_text = transcribe_voice_local(file_path)
        print(f"📝 النص النهائي للفحص: {combined_text}")

        if not combined_text:
            return

        def send_video(key, label):
            try:
                bot_instance.send_video(
                    chat_id,
                    FIXED_VIDEOS[key],
                    caption=CHANNEL,
                    reply_to_message_id=message_id
                )
            except Exception as e:
                print(f"⚠️ خطأ في إرسال فيديو {label}: {e}")

        banned_word = _check_banned_in_text(combined_text)

        # الكروبات التي تُحذف منها البصمة لكن لا تُحوَّل للإدارة
        VOICE_NO_FORWARD_GROUPS = {-1003980016517}

        if banned_word:
            print(f"🚫 كلمة محظورة وُجدت: {banned_word}")
            if chat_id not in VOICE_NO_FORWARD_GROUPS:
                try:
                    def get_short_context(text, banned):
                        sentences = re.split(r'[.،؟!]', text)
                        for s in sentences:
                            if banned in s.lower():
                                words = s.strip().split()
                                for i, w in enumerate(words):
                                    if banned in w.lower():
                                        start = max(0, i - 1)
                                        end   = min(len(words), i + 2)
                                        return ' '.join(words[start:end])
                        return banned

                    short_ctx = get_short_context(combined_text, banned_word)
                    if os.path.exists(file_path):
                        for attempt in range(3):
                            try:
                                with open(file_path, 'rb') as audio:
                                    bot_instance.send_voice(
                                        ADMIN_GROUP_ID,
                                        audio,
                                        caption=(
                                            f"🚨 بصمة مسيئة تم حذفها\n"
                                            f"🔴 {short_ctx}\n"
                                            f"👥 كباتن صقور العراق"
                                        ),
                                        timeout=60
                                    )
                                break
                            except Exception as e:
                                print(f"⚠️ محاولة {attempt+1} فشلت: {e}")
                                if attempt < 2:
                                    time.sleep(3)
                except Exception as e:
                    print(f"⚠️ خطأ في الإرسال للإدارة: {e}")
            try:
                bot_instance.delete_message(chat_id, message_id)
                print(f"🚫 تم حذف بصمة تحتوي على: {banned_word}")
            except Exception as e:
                print(f"⚠️ خطأ في الحذف: {e}")
            return

        if contains_uber_pay_question(combined_text):
            send_video('uber_pay', 'تسديد أوبر')
        elif contains_uber_withdraw_question(combined_text):
            send_video('uber_withdraw', 'سحب المستحقات')
        elif contains_uber_careem_question(combined_text):
            send_video('uber_careem', 'ربط كريم')
        elif contains_uber_master_question(combined_text):
            send_video('uber_master', 'ربط الماستر')
        elif contains_uber_cancel_question(combined_text):
            send_video('uber_cancel', 'تعويض الإلغاء')
        elif contains_uber_support_question(combined_text):
            send_video('uber_support', 'دعم أوبر')
        elif contains_uber_trips_question(combined_text):
            send_video('uber_trips', 'تفاصيل الرحلات')
        elif contains_greeting(combined_text):
            pass

    except Exception as e:
        print(f"⚠️ خطأ في تحليل الصوت: {e}")
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

@bot.message_handler(
    func=lambda m: m.chat.type in ['group', 'supergroup'],
    content_types=['voice']
)
def handle_group_voice(message):
    chat_id    = message.chat.id
    message_id = message.message_id
    try:
        file_info = bot.get_file(message.voice.file_id)
        file_path = f"voice_{chat_id}_{message_id}.ogg"
        downloaded = bot.download_file(file_info.file_path)
        with open(file_path, 'wb') as f:
            f.write(downloaded)
        threading.Thread(
            target=analyze_and_delete_voice,
            args=(bot, chat_id, message_id, file_path),
            daemon=True
        ).start()
    except Exception as e:
        print(f"⚠️ خطأ في تنزيل البصمة: {e}")


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


# ═══════════════════════════════════════
# ⛽ أمر النقطتين — إرسال محطات الغاز
# ═══════════════════════════════════════

GAS_STATION_PHOTO = "AgACAgIAAxkBAAIKI2oB4m7LjZUbjJ6h4HJTs7j2XSwCAAIqFWsbIKwJSHO9LMp9GiEaAQADAgADeQADOwQ"
GAS_STATION_URL   = "https://beautiful-melba-ea1a00.netlify.app/"

@bot.message_handler(
    func=lambda m: m.chat.type in ['group', 'supergroup'] and
                   m.text and m.text.strip() == '..',
    content_types=['text']
)
def handle_gas_station_command(message):
    chat_id = message.chat.id
    try: bot.delete_message(chat_id, message.message_id)
    except: pass
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        "⛽ محطات الغاز اضغط هنا",
        url=GAS_STATION_URL
    ))
    target_msg_id = message.reply_to_message.message_id if message.reply_to_message else None
    try:
        bot.send_photo(
            chat_id,
            GAS_STATION_PHOTO,
            reply_to_message_id=target_msg_id,
            reply_markup=markup
        )
    except Exception as e:
        print(f"خطأ في إرسال محطات الغاز: {e}")

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
# 🎬 بوت التحميل المستقل (المصلح)
# ═══════════════════════════════════════

dl_bot = telebot.TeleBot(DOWNLOADER_TOKEN)

@dl_bot.message_handler(commands=['start'])
def dl_start(message):
    welcome_text = (
        "اهلا وسهلا بكم بوت صقور العراق لتحميل الفيديوهات 🦅\n\n"
        "✅ أمن\n"
        "✅ سريع\n"
        "✅ بدون اعلانات\n\n"
        "📌 المنصات المدعومة:\n"
        "• YouTube\n"
        "• TikTok\n"
        "• Instagram\n"
        "• Facebook\n\n"
        "فقط انسخ رابط الفيديو والصقه هنا 👇\n\n"
        "مجموعتنا على تلغرام حياكم الله " + GROUP_LINK
    )
    dl_bot.reply_to(message, welcome_text)

@dl_bot.message_handler(func=lambda m: m.text and is_downloadable_url(m.text.strip()))
def dl_download(message):
    threading.Thread(
        target=download_and_send_video,
        args=(dl_bot, message.chat.id, message.message_id, message.text.strip()),
        daemon=True
    ).start()

@dl_bot.message_handler(func=lambda m: True)
def dl_unknown(message):
    dl_bot.reply_to(
        message,
        "⚠️ الرابط غير مدعوم.\nأرسل رابطاً من YouTube أو TikTok أو Instagram أو Facebook."
    )

def run_downloader_bot():
    print("✅ بوت التحميل يعمل...")
    while True:
        try:
            dl_bot.delete_webhook(drop_pending_updates=True)
            dl_bot.infinity_polling(timeout=20, interval=2)
        except Exception as e:
            print(f"⚠️ خطأ بوت التحميل: {e}")
            time.sleep(10)


# ═══════════════════════════════════════
# تشغيل المشروع
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
    print("✅ البوت الرئيسي يعمل...")
    resolve_default_groups()

    downloader_thread = threading.Thread(target=run_downloader_bot, daemon=True)
    downloader_thread.start()

    while True:
        try:
            bot.delete_webhook(drop_pending_updates=True)
            bot.infinity_polling(timeout=20, interval=2)
        except Exception as e:
            print(f"⚠️ خطأ: {e}")
            time.sleep(10)
