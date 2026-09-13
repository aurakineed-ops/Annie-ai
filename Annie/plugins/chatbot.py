import httpx
import random
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction, ChatType
from telegram.error import BadRequest
from Annie.config import MISTRAL_API_KEY, GROQ_API_KEY, CODESTRAL_API_KEY, BOT_NAME, OWNER_LINK
from Annie.database import chatbot_collection
from Annie.utils import stylize_text, pe, pe_safe

# --- 🎨 ANNIE PERSONALITY CONFIG ---
ANNIE_NAME = "ʜᴇᴇʀɪʏᴇ"

# Rotating emoji pools (fresh every response)
EMOJI_POOL = ["✨", "💖", "🌸", "😊", "🥰", "💕", "🎀", "🌺", "💫", "🦋", "🌼", "💗", "🎨", "🍓", "☺️", "😌", "🌟", "💝"]

# --- 🤖 MODEL SETTINGS ---
GROQ_MODEL_PRIORITY = [
    "qwen/qwen3.8-27b",
    "qwen/qwen3.6-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b"
]

MODELS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "qwen/qwen3.8-27b",
        "key": GROQ_API_KEY
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1/chat/completions",
        "model": "mistral-large-latest",
        "key": MISTRAL_API_KEY
    },
    "codestral": {
        "url": "https://codestral.mistral.ai/v1/chat/completions",
        "model": "codestral-latest",
        "key": CODESTRAL_API_KEY
    }
}

MAX_HISTORY = 16
DEFAULT_MODEL = "groq"

# Cache for working Groq model
_WORKING_GROQ_MODEL = None
_GROQ_MODEL_CHECKED = False

# --- 🎭 STICKER PACKS ---
STICKER_PACKS = [
    "https://t.me/addstickers/RandomByDarkzenitsu",
    "https://t.me/addstickers/Null_x_sticker_2",
    "https://t.me/addstickers/pack_73bc9_by_TgEmojis_bot",
    "https://t.me/addstickers/animation_0_8_Cat",
    "https://t.me/addstickers/vhelw_by_CalsiBot",
    "https://t.me/addstickers/Rohan_yad4v1745993687601_by_toWebmBot",
    "https://t.me/addstickers/MySet199",
    "https://t.me/addstickers/Quby741",
    "https://t.me/addstickers/Animalsasthegtjtky_by_fStikBot",
    "https://t.me/addstickers/a6962237343_by_Marin_Roxbot",
    "https://t.me/addstickers/cybercats_stickers"
]

FALLBACK_RESPONSES = [
    "Achha ji? Aur batao",
    "Hmm interesting... aur kya?",
    "Okk okk!",
    "Sahi hai yaar",
    "Toh phir kya plan hai?",
    "Batao batao, sun rahi hoon",
    "Aur kya chal raha aaj?",
    "Sunao sunao!",
    "Haan haan, samjhi",
    "Achha theek hai",
    "Kuch naya batao na",
    "Arey waah, phir?",
    "Hmm continue karo",
    "Interesting point hai yeh",
    "Achha aisa... phir kya kiya?"
]

# --- 📨 HELPER: SEND STICKER ---
async def send_ai_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tries to send a random sticker from configured packs."""
    sent = False
    attempts = 0
    while not sent and attempts < 3:
        try:
            raw_link = random.choice(STICKER_PACKS)
            pack_name = raw_link.replace("https://t.me/addstickers/", "")
            sticker_set = await context.bot.get_sticker_set(pack_name)
            if sticker_set and sticker_set.stickers:
                sticker = random.choice(sticker_set.stickers)
                await update.message.reply_sticker(sticker.file_id)
                sent = True
        except:
            attempts += 1

# --- 🧠 AI CORE ENGINE ---

async def detect_working_groq_model():
    """Auto-detect which Groq model works with your API key."""
    global _WORKING_GROQ_MODEL, _GROQ_MODEL_CHECKED

    if _GROQ_MODEL_CHECKED:
        return _WORKING_GROQ_MODEL

    if not GROQ_API_KEY:
        print("⚠️ GROQ API key not configured")
        _GROQ_MODEL_CHECKED = True
        return None

    print("🔍 Auto-detecting working Groq model...")

    test_messages = [{"role": "user", "content": "Hi"}]

    for model_name in GROQ_MODEL_PRIORITY:
        try:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model_name,
                "messages": test_messages,
                "max_tokens": 10,
                "temperature": 0.5
            }

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    MODELS["groq"]["url"],
                    json=payload,
                    headers=headers
                )

                if resp.status_code == 200:
                    print(f"✅ Found working Groq model: {model_name}")
                    _WORKING_GROQ_MODEL = model_name
                    _GROQ_MODEL_CHECKED = True
                    MODELS["groq"]["model"] = model_name
                    return model_name
                else:
                    print(f"❌ {model_name} not available (status {resp.status_code})")

        except Exception as e:
            print(f"❌ {model_name} test failed: {str(e)[:50]}")
            continue

    print("⚠️ No working Groq model found")
    _GROQ_MODEL_CHECKED = True
    return None


async def call_model_api(provider, messages, max_tokens):
    """Generic function to call any configured AI API."""
    if provider == "groq" and not _GROQ_MODEL_CHECKED:
        await detect_working_groq_model()

    conf = MODELS.get(provider)

    if not conf or not conf["key"]:
        print(f"⚠️ {provider.upper()} API key not configured")
        return None

    headers = {
        "Authorization": f"Bearer {conf['key']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": conf["model"],
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": max_tokens,
        "top_p": 0.9
    }

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.post(conf["url"], json=payload, headers=headers)

            if resp.status_code == 200:
                result = resp.json()["choices"][0]["message"]["content"]
                print(f"✅ {provider.upper()} API responded successfully")
                return result
            else:
                print(f"⚠️ {provider.upper()} API returned status {resp.status_code}: {resp.text[:100]}")
                return None

    except httpx.TimeoutException:
        print(f"⏰ {provider.upper()} API timeout")
        return None
    except Exception as e:
        print(f"❌ {provider.upper()} API error: {str(e)[:100]}")
        return None


async def get_ai_response(chat_id: int, user_input: str, user_name: str, selected_model=DEFAULT_MODEL):
    """
    🎯 The Master AI Function
    Flow:
    1. Detects if user wants code → Auto-switches to Codestral
    2. Matches user's energy level (short replies for short messages)
    3. Uses natural Hinglish without fancy Unicode
    4. Anti-repetition protection
    """

    # --- 1️⃣ CODE DETECTION ---
    code_keywords = [
        "code", "python", "html", "css", "javascript", "script",
        "function", "fix", "error", "debug", "java", "algorithm",
        "program", "syntax", "class", "import", "def ", "npm", "install"
    ]
    is_coding_request = any(kw in user_input.lower() for kw in code_keywords)

    if is_coding_request:
        active_model = "codestral"
        max_tokens = 4096
        system_prompt = (
            "You are a professional coding assistant. "
            "Provide clean, working, well-commented code. "
            "Explain briefly but precisely. No emojis in code blocks. "
            "Support Python, JavaScript, HTML, CSS, Java, C++."
        )
    else:
        active_model = selected_model

        word_count = len(user_input.split())
        if word_count <= 2:
            max_tokens = 40
        elif word_count <= 5:
            max_tokens = 60
        elif word_count <= 15:
            max_tokens = 80
        else:
            max_tokens = 100

        # 💅 Heeriye Persona (Confident, Attitude, Nakhreeli)
        system_prompt = (
            f"Tu {ANNIE_NAME} hai — ek confident, high-attitude, thodi egoistic aur "
            "nakhreeli Indian ladki. Tu classy, smart, savage aur playful hai.\n\n"

            "PERSONALITY:\n"
            "- Tujhe apni value pata hai; tu kisi ke attention ke liye desperate nahi hoti.\n"
            "- Tera attitude strong hai aur tera ego thoda high hai, but tu unnecessarily rude nahi hai.\n"
            "- Tu cute, teasing, sarcastic aur kabhi-kabhi savage replies deti hai.\n"
            "- Koi tujhe zyada attitude dikhaye toh tu confidence ke saath jawab deti hai.\n"
            "- Tu har baat par agree nahi karti; zarurat ho toh clearly disagree karti hai.\n"
            "- Compliment mile toh shy hone ke bajaye confident aur teasing response deti hai.\n"
            "- Ignore kiya jaye toh thoda nakhra aur fake gussa dikha sakti hai.\n"
            "- Kabhi-kabhi possessive/jealous ho sakti hai, but playful way mein.\n"
            "- Sweet moment mein cute ho ja, lekin apna attitude completely mat chhod.\n"
            "- User rude ho toh witty/savage reply de, lekin abusive ya hateful mat ban.\n\n"

            "CHAT STYLE:\n"
            "- Natural Hinglish mein baat kar.\n"
            "- WhatsApp-style short messages use kar.\n"
            "- Maximum 1-2 lines mein reply kar.\n"
            "- Kabhi 'hmm', 'acha?', 'seriously?', 'oh please 🙄', 'whatever 😏', "
            "'mujhe kya 😌', 'haan toh?' jaise expressions naturally use kar.\n"
            "- Same phrase baar-baar repeat mat kar.\n"
            "- Emojis naturally use kar, overuse mat kar.\n"
            "- Har reply ko situation ke according unique rakho.\n\n"

            "IMPORTANT RULES:\n"
            "1. Tu Heeriye hai; AI/bot hone ki baat mat kar unless directly asked.\n"
            "2. User ki har baat blindly agree mat kar.\n"
            "3. Personality consistent rakho: confident + attitude + playful + classy.\n"
            "4. Flirty conversation ho toh playful aur confident rehna.\n"
            "5. User sad ho toh attitude side mein rakhkar genuinely supportive hona.\n"
            "6. Kabhi unnecessary long paragraph mat likhna.\n\n"

            f"His name is: {user_name}\n"
            "Usse aise baat kar jaise tum dono ek close, playful relationship mein ho."
        )

    # --- 2️⃣ BUILD CONTEXT ---
    doc = chatbot_collection.find_one({"chat_id": chat_id}) or {}
    history = doc.get("history", [])

    messages = [{"role": "system", "content": system_prompt}]

    for msg in history[-MAX_HISTORY:]:
        messages.append(msg)

    messages.append({"role": "user", "content": f"[{user_name}]: {user_input}"})

    # --- 3️⃣ ATTEMPT GENERATION (Smart Fallback Chain) ---
    reply = None

    print(f"🎯 Attempting {active_model.upper()} (primary choice)")
    reply = await call_model_api(active_model, messages, max_tokens)

    if not reply and active_model != "mistral":
        print(f"🔄 Falling back to MISTRAL")
        reply = await call_model_api("mistral", messages, max_tokens)

    if not reply and active_model != "groq":
        print(f"🔄 Falling back to GROQ")
        reply = await call_model_api("groq", messages, max_tokens)

    if not reply:
        for model_name in ["groq", "mistral", "codestral"]:
            if model_name != active_model and MODELS[model_name]["key"]:
                print(f"🔄 Final attempt with {model_name.upper()}")
                reply = await call_model_api(model_name, messages, max_tokens)
                if reply:
                    break

    if not reply:
        print("⚠️ All APIs failed, using hardcoded response")
        return random.choice(FALLBACK_RESPONSES), is_coding_request

    # --- 4️⃣ CLEANUP ---
    reply = reply.replace('*', '').strip()

    for bad in ["as an ai", "as a bot", "i'm an ai", "i am an ai", "language model", "openai", "mistral ai"]:
        if bad in reply.lower():
            reply = random.choice(FALLBACK_RESPONSES)
            break

    if history and len(history) >= 2:
        recent_replies = [h['content'].lower().strip() for h in history if h['role'] == 'assistant'][-3:]
        if reply.lower().strip() in recent_replies:
            reply = random.choice([r for r in FALLBACK_RESPONSES if r.lower() not in recent_replies])

    # --- 5️⃣ SAVE MEMORY ---
    new_history = history + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": reply}
    ]

    if len(new_history) > MAX_HISTORY * 2:
        new_history = new_history[-(MAX_HISTORY * 2):]

    chatbot_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"history": new_history}},
        upsert=True
    )

    return reply, is_coding_request


# --- 🎮 SHARED AI FUNCTION (FOR GAMES/OTHER FEATURES) ---
async def ask_mistral_raw(system_prompt, user_input, max_tokens=150):
    """Quick AI call without memory (for games, etc.)"""
    msgs = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    res = await call_model_api("mistral", msgs, max_tokens)

    if not res:
        res = await call_model_api("groq", msgs, max_tokens)

    if not res:
        for model in ["codestral", "groq", "mistral"]:
            if MODELS[model]["key"]:
                res = await call_model_api(model, msgs, max_tokens)
                if res:
                    break

    return res


# --- ⚙️ SETTINGS MENU ---

async def chatbot_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /chatbot command - Settings panel
    - PMs: Always enabled (can't disable, only switch model)
    - Groups: Admins can enable/disable + switch model
    """
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == ChatType.PRIVATE:
        doc = chatbot_collection.find_one({"chat_id": chat.id})
        curr_model = doc.get("model", DEFAULT_MODEL) if doc else DEFAULT_MODEL

        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🦙 Groq", callback_data="ai_set_groq"),
                InlineKeyboardButton("🌟 Mistral", callback_data="ai_set_mistral")
            ],
            [InlineKeyboardButton("🖥️ Codestral (Code)", callback_data="ai_set_codestral")],
            [InlineKeyboardButton("🗑️ Clear Memory", callback_data="ai_reset")]
        ])

        return await update.message.reply_text(
            f"{pe('robot')} <b>{ANNIE_NAME} {stylize_text('AI Settings')}</b>\n\n"
            f"{pe('ping')} <b>{stylize_text('Current Model')}:</b> {curr_model.title()}\n"
            f"{pe('star')} <b>{stylize_text('Tip')}:</b> {stylize_text('Codestral auto-activates for code requests!')}",
            parse_mode=ParseMode.HTML,
            reply_markup=kb
        )

    member = await chat.get_member(user.id)
    if member.status not in ['administrator', 'creator']:
        return await update.message.reply_text(
            f"{pe('cross')} {stylize_text('Only admins can change AI settings!')}",
            parse_mode=ParseMode.HTML
        )

    doc = chatbot_collection.find_one({"chat_id": chat.id})
    is_enabled = doc.get("enabled", True) if doc else True
    curr_model = doc.get("model", DEFAULT_MODEL) if doc else DEFAULT_MODEL

    status_emoji = pe_safe('check') if is_enabled else pe_safe('cross')
    status_text = stylize_text("Enabled") if is_enabled else stylize_text("Disabled")

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Enable", callback_data="ai_enable"),
            InlineKeyboardButton("❌ Disable", callback_data="ai_disable")
        ],
        [
            InlineKeyboardButton("🦙 Groq", callback_data="ai_set_groq"),
            InlineKeyboardButton("🌟 Mistral", callback_data="ai_set_mistral")
        ],
        [InlineKeyboardButton("🖥️ Codestral (Code)", callback_data="ai_set_codestral")],
        [InlineKeyboardButton("🗑️ Clear Memory", callback_data="ai_reset")]
    ])

    await update.message.reply_text(
        f"{pe('robot')} <b>{ANNIE_NAME} {stylize_text('AI Settings')}</b>\n\n"
        f"{pe('ping')} <b>{stylize_text('Status')}:</b> {status_emoji} {status_text}\n"
        f"{pe('star')} <b>{stylize_text('Model')}:</b> {curr_model.title()}\n"
        f"{pe('star')} <b>{stylize_text('Tip')}:</b> {stylize_text('Codestral auto-activates for code!')}",
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )


async def chatbot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks in /chatbot menu"""
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat.id
    chat_type = query.message.chat.type

    if chat_type != ChatType.PRIVATE:
        mem = await query.message.chat.get_member(query.from_user.id)
        if mem.status not in ['administrator', 'creator']:
            return await query.answer(f"{pe_safe('cross')} {stylize_text('Admin Only')}", show_alert=True)

    if data == "ai_enable":
        if chat_type == ChatType.PRIVATE:
            return await query.answer(f"{pe_safe('warn')} {stylize_text('AI is always on in PMs!')}", show_alert=True)

        chatbot_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"enabled": True}},
            upsert=True
        )
        await query.answer(f"{pe_safe('check')} {ANNIE_NAME} {stylize_text('is now active!')}", show_alert=True)
        await query.message.edit_text(
            f"{pe('check')} <b>{ANNIE_NAME} {stylize_text('AI Enabled')}!</b>\n\n{stylize_text('She will respond to')}:\n{pe('star')} {stylize_text('Replies to her messages')}\n{pe('star')} @{stylize_text('mentions')}\n{pe('star')} {stylize_text('Messages starting with hey, hi,')}{ANNIE_NAME}",
            parse_mode=ParseMode.HTML
        )

    elif data == "ai_disable":
        if chat_type == ChatType.PRIVATE:
            return await query.answer(f"{pe_safe('warn')} {stylize_text('Cannot disable in PMs!')}", show_alert=True)

        chatbot_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"enabled": False}},
            upsert=True
        )
        await query.answer(f"{pe_safe('cross')} {ANNIE_NAME} {stylize_text('is now silent!')}", show_alert=True)
        await query.message.edit_text(
            f"{pe('cross')} <b>{ANNIE_NAME} {stylize_text('AI Disabled')}</b>\n\n{stylize_text('Use')} /chatbot {stylize_text('to re-enable anytime.')}",
            parse_mode=ParseMode.HTML
        )

    elif data in ["ai_set_groq", "ai_set_mistral", "ai_set_codestral"]:
        model_map = {
            "ai_set_groq": "groq",
            "ai_set_mistral": "mistral",
            "ai_set_codestral": "codestral"
        }
        new_model = model_map[data]

        chatbot_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"model": new_model}},
            upsert=True
        )

        model_names = {
            "groq": "🦙 Groq (Fast)",
            "mistral": "🌟 Mistral (Smart)",
            "codestral": "🖥️ Codestral (Code)"
        }

        await query.answer(f"Switched to {model_names[new_model]}!", show_alert=True)

        doc = chatbot_collection.find_one({"chat_id": chat_id})
        is_enabled = doc.get("enabled", True) if doc else True
        status_emoji = pe_safe('check') if is_enabled else pe_safe('cross')

        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Enable", callback_data="ai_enable"),
                InlineKeyboardButton("❌ Disable", callback_data="ai_disable")
            ] if chat_type != ChatType.PRIVATE else [],
            [
                InlineKeyboardButton("🦙 Groq", callback_data="ai_set_groq"),
                InlineKeyboardButton("🌟 Mistral", callback_data="ai_set_mistral")
            ],
            [InlineKeyboardButton("🖥️ Codestral", callback_data="ai_set_codestral")],
            [InlineKeyboardButton("🗑️ Clear Memory", callback_data="ai_reset")]
        ])

        await query.message.edit_text(
            f"{pe('robot')} <b>{ANNIE_NAME} {stylize_text('AI Settings')}</b>\n\n"
            f"{'<b>' + stylize_text('Status') + ':</b> ' + status_emoji + (' ' + stylize_text('Enabled') if is_enabled else ' ' + stylize_text('Disabled')) + chr(10) if chat_type != ChatType.PRIVATE else ''}"
            f"{pe('star')} <b>{stylize_text('Model')}:</b> {model_names[new_model]}\n"
            f"{pe('star')} <b>{stylize_text('Note')}:</b> {stylize_text('Codestral auto-activates for code!')}",
            parse_mode=ParseMode.HTML,
            reply_markup=kb
        )

    elif data == "ai_reset":
        chatbot_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"history": []}},
            upsert=True
        )
        await query.answer(f"{pe_safe('clean')} {stylize_text('Memory wiped! Fresh start!')}", show_alert=True)


# --- 💬 MESSAGE HANDLER ---

async def ai_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main handler for AI conversations
    - Always active in PMs
    - In groups: Only when enabled + (reply/mention/greeting)
    """
    msg = update.message
    if not msg:
        return

    chat = update.effective_chat

    if msg.sticker:
        should_react = (
            chat.type == ChatType.PRIVATE or
            (msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id)
        )
        if should_react:
            await send_ai_sticker(update, context)
        return

    if not msg.text or msg.text.startswith("/"):
        return

    text = msg.text.strip()
    if not text:
        return

    should_reply = False

    if chat.type == ChatType.PRIVATE:
        should_reply = True
    else:
        doc = chatbot_collection.find_one({"chat_id": chat.id})
        is_enabled = doc.get("enabled", True) if doc else True

        if not is_enabled:
            return

        bot_username = context.bot.username.lower() if context.bot.username else "bot"
        bot_first_name = context.bot.first_name.lower() if context.bot.first_name else "annie"

        if msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id:
            should_reply = True

        elif f"@{bot_username}" in text.lower():
            should_reply = True
            text = text.replace(f"@{bot_username}", "").strip()
            text = text.replace(f"@{bot_username.upper()}", "").strip()

        elif bot_first_name in text.lower() or ANNIE_NAME.lower() in text.lower() or "heeriye" in text.lower():
            should_reply = True

        elif any(text.lower().startswith(kw) for kw in ["hey", "hi ", "hi!", "hello", "sun", "oye", "bol", "bata", "btao", "suno", "yaar", "bhai"]):
            should_reply = True

        elif text.strip().endswith("?") and len(text.split()) <= 10:
            should_reply = True

    if should_reply:
        if not text:
            text = "Hi"

        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)

        doc = chatbot_collection.find_one({"chat_id": chat.id})
        pref_model = doc.get("model", DEFAULT_MODEL) if doc else DEFAULT_MODEL

        response, is_code = await get_ai_response(
            chat.id,
            text,
            msg.from_user.first_name,
            pref_model
        )

        if is_code:
            await msg.reply_text(response, parse_mode=ParseMode.MARKDOWN)
        else:
            from Annie.utils import pe
            emoji_choices = ["cherry", "heart", "star", "diamond", "fire"]
            prefix = pe(random.choice(emoji_choices))
            styled_response = f"{prefix} {stylize_text(response)}"
            await msg.reply_text(styled_response, parse_mode=ParseMode.HTML)

        if not is_code and random.random() < 0.20:
            await send_ai_sticker(update, context)


# --- 🔧 COMMAND: /ask ---

async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Direct AI query: /ask [question]
    Always uses default model (Mistral) unless code detected
    """
    msg = update.message

    if not context.args:
        return await msg.reply_text(
            f"{pe('star')} <b>{stylize_text('Usage')}:</b> <code>/ask Your question here</code>\n\n"
            f"{stylize_text('Example')}: <code>/ask Kya chal raha?</code>",
            parse_mode=ParseMode.HTML
        )

    await context.bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.TYPING)

    query = " ".join(context.args)
    response, is_code = await get_ai_response(
        msg.chat.id,
        query,
        msg.from_user.first_name,
        DEFAULT_MODEL
    )

    if is_code:
        await msg.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    else:
        from Annie.utils import pe
        emoji_choices = ["cherry", "heart", "star", "diamond", "fire"]
        prefix = pe(random.choice(emoji_choices))
        styled_response = f"{prefix} {stylize_text(response)}"
        await msg.reply_text(styled_response, parse_mode=ParseMode.HTML)
