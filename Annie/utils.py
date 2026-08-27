import html
import re
import asyncio
from datetime import datetime, timedelta
from telegram import Bot, User, Chat
from telegram.constants import ParseMode, ChatType
from telegram.error import TelegramError
from Annie.database import users_collection, sudoers_collection, groups_collection
from Annie.config import OWNER_ID, SUDO_IDS_STR, LOGGER_ID, BOT_NAME, AUTO_REVIVE_HOURS, AUTO_REVIVE_BONUS

SUDO_USERS = set()

def reload_sudoers():
    """Loads Sudo users from Env and DB."""
    try:
        SUDO_USERS.clear()
        SUDO_USERS.add(OWNER_ID)
        if SUDO_IDS_STR:
            for x in SUDO_IDS_STR.split(","):
                if x.strip().isdigit(): SUDO_USERS.add(int(x.strip()))
        for doc in sudoers_collection.find({}):
            SUDO_USERS.add(doc["user_id"])
    except Exception as e:
        print(f"Sudo Load Error: {e}")

reload_sudoers()

# --- 🌸 PREMIUM EMOJI SYSTEM ---
# All IDs verified from @RawDataBot screenshots
USE_CUSTOM_EMOJI = True

# Custom emoji IDs - ALL from user's @RawDataBot screenshots
CUSTOM_EMOJI_IDS = {
    "cherry": "5096268443787724055",
    "heart": "5039598514980520994",
    "money": "6310090437168206901",
    "trophy": "5188344996356448758",
    "sword": "6129415619885407680",
    "gift": "6150106367135847353",
    "diamond": "5830034391941785825",
    "shield": "6217753021170849224",
    "skull": "5954090983233369091",
    "fire": "6311799464784827510",
    "star": "5044404656399189404",
    "warn": "5855178350263276469",
    "crown": "6217568930282608300",
    "robot": "5042328396193864923",
    "lightning": "6327952072280910418",
    "ring": "5262922516426420894",
    "broken_heart": "6309675822500289147",
    "cart": "5400090058030075645",
    "wallet": "5197434882321567830",
    "calendar": "5854847234054558104",
    "mic": "5388632425314140043",
    "art": "6328118240270622647",
    "ping": "6312014341998647233",
    "broadcast": "5388632425314140043",
    "cross": "6215407840178216561",
    "book": "5258247826202882951",
    "dagger": "6129415619885407680",
    "lock": "5429405838345265327",
    "refresh": "6217266023419091458",
    "check": "5832229652805985405",
    "party": "5361964771509808811",
    "user": "6100147565246813025",
    "timer": "5854847234054558104",
    "down": "6228566073784928267",
    "clean": "5039614900280754969",
    "cash": "5197434882321567830",
    "dice": "6242155109791307482",
    "rose": "6098098075572638745",
    "kiss": "5289850733011693663",
    "link": "6275878213746955453",
    "warn_yellow": "5039665997506675838",
    "warn_red": "6122658764450439038",
    "verified": "6309930986507342804",
    "sale": "6309644434879288417",
    "free": "6311871800624026387",
    "buy": "6309938631549129690",
    "music": "5039771357349413873",
    "online": "6311891639077967303",
    "trophy1": "5765089714717596171",
    "trophy2": "5767304320114498155",
    "trophy3": "5764928223947267454",
    "heart_neon": "6181316288158109677",
    "heart_pink": "5039598514980520994",
    "heart_fire": "6309675822500289147",
    "dollar": "5197434882321567830",
    "coin_up": "5382164415019768638",
    "siren": "6228495924084082954",
    "megaphone": "6309567477655279083",
    "clover": "5258040062028822951",
    "wine": "5361964771509808811",
    "question": "5436113877181941026",
    "no_btn": "6337074578522642080",
    "yes_btn": "6338853910458930994",
    "stop": "6271674836628541366",
    "apple": "6300749342860904648",
    "lollipop": "6327978464854940714",
    "snowman": "5039936198194234403",
    "pin": "5098574205570516021",
    "soon": "5040025078247457682",
    "point_hand": "4983489775190147940",
    "red_dot": "4927197721900614739",
    "eye": "6309988898530226635",
    "laugh": "6156966559483960850",
    "facepalm": "5956333265399845477",
    "cry": "6226417091193341702",
    "hundred": "6154464668019596444",
    "love_tape": "5271721134889395048",
}

# Fallback emojis (always work)
EMOJI_MAP = {
    "cherry": "🌸", "heart": "💗", "money": "💰", "trophy": "🏆",
    "sword": "⚔️", "gift": "🎁", "diamond": "💎", "shield": "🛡️",
    "skull": "💀", "fire": "🔥", "star": "✨", "warn": "⚠️",
    "dice": "🎲", "crown": "👑", "robot": "🤖", "lightning": "⚡",
    "ring": "💍", "broken_heart": "💔", "cart": "🛒", "wallet": "👛",
    "calendar": "📅", "mic": "🎙", "art": "🎨", "ping": "📡",
    "broadcast": "📢", "cross": "❌", "book": "📖", "bride": "👰",
    "cash": "💸", "down": "🔻", "list": "📋", "heal": "❤️‍🩹",
    "clean": "🧹", "refresh": "🔄", "lock": "🔐", "user": "👤",
    "timer": "⏳", "check": "✅", "party": "🎉", "dagger": "🗡",
}

def pe(name):
    """Get emoji by name. Uses custom emoji if enabled, otherwise normal."""
    if USE_CUSTOM_EMOJI and name in CUSTOM_EMOJI_IDS:
        fallback = EMOJI_MAP.get(name, "")
        return f'<tg-emoji emoji-id="{CUSTOM_EMOJI_IDS[name]}">{fallback}</tg-emoji>'
    return EMOJI_MAP.get(name, "")

def pe_safe(name):
    """Always returns normal emoji - safe for edit_message_text and callbacks."""
    return EMOJI_MAP.get(name, "")

async def smart_reply(update, text, reply_markup=None, **kwargs):
    """Send message with proper parse mode. Falls back to normal emojis if Document_invalid."""
    import re as _re
    try:
        return await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup, **kwargs)
    except Exception as e:
        if "Document_invalid" in str(e):
            # Strip custom emoji tags and use fallback
            clean_text = _re.sub(r'<tg-emoji emoji-id="[^"]*">([^<]*)</tg-emoji>', r'\1', text)
            return await update.message.reply_text(clean_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup, **kwargs)
        raise

# Dummy function for backward compatibility
async def start_userbot():
    pass

# --- 🌸 AESTHETIC FONT ENGINE ---
def stylize_text(text):
    """Converts normal text to Premium Aesthetic Small Caps."""
    font_map = {
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ꜰ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 'ꜱ', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ',
        'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
        'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ',
        'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒', 
        '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗'
    }

    def apply_style(t):
        return "".join(font_map.get(c, c) for c in t)

    pattern = r"(@\w+|https?://\S+|`[^`]+`|/[a-zA-Z0-9_]+)"
    parts = re.split(pattern, str(text))
    result = []
    for part in parts:
        if re.match(pattern, part): result.append(part)
        else: result.append(apply_style(part))

    return "".join(result)

# --- 🌟 ULTIMATE DASHBOARD LOGGER ---
async def log_to_channel(bot: Bot, event_type: str, details: dict):
    if LOGGER_ID == 0: return
    now = datetime.now().strftime("%I:%M:%S %p | %d %b")

    headers = {
        "start": f"{pe('cherry')} <b>{stylize_text('SYSTEM ONLINE')}</b>",
        "join": f"{pe('party')} <b>{stylize_text('NEW GROUP JOINED')}</b>",
        "leave": f"{pe('broken_heart')} <b>{stylize_text('LEFT GROUP')}</b>",
        "command": f"{pe('user')} <b>{stylize_text('ADMIN COMMAND')}</b>",
        "transfer": f"{pe('cash')} <b>{stylize_text('TRANSACTION')}</b>"
    }
    header = headers.get(event_type, f"{pe('book')} <b>{stylize_text('LOG ENTRY')}</b>")

    text = f"{header}\n━━━━━━━━━━━━━━━━━━\n"
    if 'user' in details:
        text += f"{pe('user')} <b>{stylize_text('User')}:</b> {details['user']}\n"
    if 'chat' in details:
        text += f"{pe('shield')} <b>{stylize_text('Chat')}:</b> {html.escape(details['chat'])}\n"
    if 'action' in details:
        text += f"{pe('star')} <b>{stylize_text('Action')}:</b> {details['action']}\n"
    if 'link' in details:
        link_val = details['link']
        if link_val and link_val.startswith("http"):
            text += f"{pe('lock')} <b>{stylize_text('Invite')}:</b> <a href='{link_val}'>{stylize_text('Click to Join')}</a>\n"
        else:
            text += f"{pe('lock')} <b>{stylize_text('Invite')}:</b> <i>{stylize_text('Hidden/Private')}</i>\n"
    text += f"━━━━━━━━━━━━━━━━━━\n{pe('timer')} <code>{now}</code>"

    try: 
        await bot.send_message(chat_id=LOGGER_ID, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        print(f"Log Error: {e}")

# --- HELPERS ---

def get_mention(user_data, custom_name=None):
    if isinstance(user_data, (User, Chat)):
        uid = user_data.id
        first_name = user_data.first_name if hasattr(user_data, "first_name") else user_data.title
    elif isinstance(user_data, dict):
        uid = user_data.get("user_id")
        first_name = user_data.get("name", "User")
    else:
        return "Unknown"
    name = custom_name or first_name
    safe_name = html.escape(name)
    return f"<a href='tg://user?id={uid}'><b>{safe_name}</b></a>"

def check_auto_revive(user_doc):
    try:
        if user_doc['status'] != 'dead': return False
        death_time = user_doc.get('death_time')
        if not death_time: return False
        if datetime.utcnow() - death_time > timedelta(hours=AUTO_REVIVE_HOURS):
            users_collection.update_one(
                {"user_id": user_doc["user_id"]}, 
                {"$set": {"status": "alive", "death_time": None}, "$inc": {"balance": AUTO_REVIVE_BONUS}}
            )
            return True
    except: pass
    return False

def ensure_user_exists(tg_user):
    try:
        user_doc = users_collection.find_one({"user_id": tg_user.id})
        username = tg_user.username.lower() if tg_user.username else None
        if not user_doc:
            new_user = {
                "user_id": tg_user.id, "name": tg_user.first_name, "username": username, "is_bot": tg_user.is_bot,
                "balance": 0, "inventory": [], "waifus": [], "daily_streak": 0, "last_daily": None,
                "kills": 0, "status": "alive", "protection_expiry": datetime.utcnow(), 
                "registered_at": datetime.utcnow(), "death_time": None, "seen_groups": []
            }
            users_collection.insert_one(new_user)
            return new_user
        else:
            if check_auto_revive(user_doc): 
                user_doc['status'] = 'alive'
                user_doc['balance'] += AUTO_REVIVE_BONUS
            updates = {}
            if user_doc.get("username") != username: updates["username"] = username
            if user_doc.get("name") != tg_user.first_name: updates["name"] = tg_user.first_name
            if "waifu_coins" in user_doc: users_collection.update_one({"user_id": tg_user.id}, {"$unset": {"waifu_coins": ""}})
            if updates: users_collection.update_one({"user_id": tg_user.id}, {"$set": updates})
            return user_doc
    except Exception as e:
        print(f"DB Error: {e}")
        return {"user_id": tg_user.id, "name": tg_user.first_name, "balance": 0, "inventory": [], "kills": 0, "status": "alive"}

def track_group(chat, user=None):
    try:
        if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            if not groups_collection.find_one({"chat_id": chat.id}):
                groups_collection.insert_one({"chat_id": chat.id, "title": chat.title, "claimed": False})
            if user:
                users_collection.update_one({"user_id": user.id}, {"$addToSet": {"seen_groups": chat.id}})
    except Exception as e:
        print(f"Track Group Error: {e}")

async def resolve_target(update, context, specific_arg=None):
    if update.message.reply_to_message:
        return ensure_user_exists(update.message.reply_to_message.from_user), None
    query = specific_arg if specific_arg else (context.args[0] if context.args else None)
    if not query: return None, None
    if query.isdigit():
        doc = users_collection.find_one({"user_id": int(query)})
        if doc: return doc, None
        return None, f"{pe('cross')} <b>{stylize_text('Annie')}!</b> ID <code>{query}</code> {stylize_text('not found.')}"
    clean_username = query.replace("@", "").lower()
    doc = users_collection.find_one({"username": clean_username})
    if doc: return doc, None
    return None, f"{pe('cross')} <b>{stylize_text('Oops')}!</b> {stylize_text('User')} <code>@{clean_username}</code> {stylize_text('has not started me.')}"

def get_active_protection(user_data):
    try:
        now = datetime.utcnow()
        self_expiry = user_data.get("protection_expiry")
        partner_expiry = None
        partner_id = user_data.get("partner_id")
        if partner_id:
            partner = users_collection.find_one({"user_id": partner_id})
            if partner: partner_expiry = partner.get("protection_expiry")
        valid_expiries = []
        if self_expiry and self_expiry > now: valid_expiries.append(self_expiry)
        if partner_expiry and partner_expiry > now: valid_expiries.append(partner_expiry)
        if not valid_expiries: return None
        return max(valid_expiries)
    except: return None

def is_protected(user_data):
    return get_active_protection(user_data) is not None

def format_money(amount): return f"${amount:,}"

def format_time(timedelta_obj):
    total_seconds = int(timedelta_obj.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}h {minutes}m"
