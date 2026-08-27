# Copyright (c) 2025 Telegram:- @RAJOWNERX1
# Location: Bikaner, Rajasthan 
#
# All rights reserved.
#
# This code is the intellectual property of @RAJOWNERX1.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Allowed:
# - Forking for personal learning
# - Submitting improvements via pull requests
#
# Not Allowed:
# - Claiming this code as your own
# - Re-uploading without credit or permission
# - Selling or using commercially
#
# Contact for permissions:
# Email: rajownerx1@gmail.com

import html
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatType
from Annie.config import BOT_NAME, START_IMG_URL, HELP_IMG_URL, SUPPORT_GROUP, SUPPORT_CHANNEL, OWNER_LINK
from Annie.utils import ensure_user_exists, get_mention, track_group, log_to_channel, SUDO_USERS, stylize_text, pe, pe_safe

SUDO_IMG = "https://files.catbox.moe/pq0h32.jpg"

# --- 🌸 AESTHETIC KEYBOARDS ---
def get_start_keyboard(bot_username):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🌸 {stylize_text('Updates')}", url=SUPPORT_CHANNEL),
            InlineKeyboardButton(f"💗 {stylize_text('Community')}", url=SUPPORT_GROUP)
        ],
        [
            InlineKeyboardButton(f"➕ {stylize_text('Add Me')} ➕", url=f"https://t.me/{bot_username}?startgroup=true")
        ],
        [
            InlineKeyboardButton(f"✨ {stylize_text('Help')}", callback_data="help_main"),
            InlineKeyboardButton(f"👑 {stylize_text('Owner')}", url=OWNER_LINK)
        ]
    ])

def get_help_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"💗 {stylize_text('Social')}", callback_data="help_social"),
            InlineKeyboardButton(f"💰 {stylize_text('Economy')}", callback_data="help_economy")
        ],
        [
            InlineKeyboardButton(f"⚔️ {stylize_text('RPG')}", callback_data="help_rpg"),
            InlineKeyboardButton(f"🎣 {stylize_text('Skills')}", callback_data="help_skills")
        ],
        [
            InlineKeyboardButton(f"✨ {stylize_text('AI & Fun')}", callback_data="help_fun")
        ],
        [
            InlineKeyboardButton(f"🌸 {stylize_text('Group')}", callback_data="help_group"),
            InlineKeyboardButton(f"🔐 {stylize_text('Sudo')}", callback_data="help_sudo")
        ],
        [
            InlineKeyboardButton(f"🔙 {stylize_text('Back')}", callback_data="return_start")
        ]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"🔙 {stylize_text('Back')}", callback_data="help_main")]])

# --- 🚀 COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat = update.effective_chat
        ensure_user_exists(user)
        track_group(chat, user)
        
        user_link = get_mention(user)
        
        # --- THE ULTRA AESTHETIC CAPTION ---
        caption = (
            f"{pe('cherry')} {stylize_text('Konichiwa')} {user_link}! (⁠≧⁠▽⁠≦⁠)\n"
            f"ᴛʜᴇ {stylize_text('Aesthetic AI-Powered RPG Bot')}! {pe('heart')}\n\n"
            f"{pe('star')}  {stylize_text('Features')}:\n"
            f"{pe('sword')}  {stylize_text('RPG')}: {stylize_text('Kill, Rob, Protect')}\n"
            f"{pe('heart')}  {stylize_text('Social')}: {stylize_text('Marry, Couple, Waifu')}\n"
            f"{pe('money')}  {stylize_text('Economy')}: {stylize_text('Claim, Give, Shop')}\n"
            f"{pe('star')}  {stylize_text('AI')}: {stylize_text('Sassy Chatbot & Art')}\n\n"
            f"{pe('cherry')} {stylize_text('Need Help?')}\n"
            f"{stylize_text('Click the buttons below!')}"
        )

        bot_un = context.bot.username if context.bot.username else "AnnieBot"
        kb = get_start_keyboard(bot_un)

        if update.callback_query:
            try: await update.callback_query.message.edit_media(InputMediaPhoto(media=START_IMG_URL, caption=caption, parse_mode=ParseMode.HTML), reply_markup=kb)
            except: await update.callback_query.message.edit_caption(caption=caption, parse_mode=ParseMode.HTML, reply_markup=kb)
        else:
            if START_IMG_URL and START_IMG_URL.startswith("http"):
                try: await update.message.reply_photo(photo=START_IMG_URL, caption=caption, parse_mode=ParseMode.HTML, reply_markup=kb)
                except: await update.message.reply_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)
            else:
                await update.message.reply_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)

        if chat.type == ChatType.PRIVATE and not update.callback_query:
            await log_to_channel(context.bot, "command", {"user": f"{get_mention(user)} (`{user.id}`)", "action": "Started Bot", "chat": "Private"})
            
    except Exception as e:
        print(f"Start Error: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_photo(
        photo=HELP_IMG_URL,
        caption=f"{pe('cherry')} <b>{BOT_NAME} {stylize_text('Help')}</b> {pe('star')}\n\n<i>{stylize_text('Select a category below:')}</i>",
        parse_mode=ParseMode.HTML, reply_markup=get_help_keyboard()
    )

# --- 🖱️ CALLBACK HANDLER ---

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "return_start":
        await start(update, context)
        return

    if data == "help_main":
        try: await query.message.edit_media(InputMediaPhoto(media=HELP_IMG_URL, caption=f"{pe('cherry')} <b>{BOT_NAME} {stylize_text('Help')}</b> {pe('star')}\n\n<i>{stylize_text('Select a category below:')}</i>", parse_mode=ParseMode.HTML), reply_markup=get_help_keyboard())
        except: await query.message.edit_caption(caption=f"{pe_safe('cherry')} <b>{BOT_NAME} {stylize_text('Help')}</b> {pe_safe('star')}\n\n<i>{stylize_text('Select a category below:')}</i>", parse_mode=ParseMode.HTML, reply_markup=get_help_keyboard())
        return

    target_photo = HELP_IMG_URL
    kb = get_back_keyboard()
    text = ""
    
    if data == "help_social":
        text = (
            f"{pe('heart')} <b>{stylize_text('Social & Love')}</b>\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"<b>/propose @user</b>\n↳ {stylize_text('Marry someone (5% tax perk)')}\n\n"
            f"<b>/marry</b>\n↳ {stylize_text('Check status')}\n\n"
            f"<b>/divorce</b>\n↳ {stylize_text('Break up (cost 2k)')}\n\n"
            f"<b>/couple</b>\n↳ {stylize_text('Matchmaking fun')}"
        )
    elif data == "help_economy":
        text = (
            f"{pe('money')} <b>{stylize_text('Economy & Shop')}</b>\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"<b>/bal</b>\n↳ {stylize_text('Wallet & Rank')}\n\n"
            f"<b>/shop</b>\n↳ {stylize_text('Buy weapons & armor')}\n\n"
            f"<b>/give [amt] [user]</b>\n↳ {stylize_text('Transfer (10% tax)')}\n\n"
            f"<b>/claim</b>\n↳ {stylize_text('Group bonus (2k)')}\n\n"
            f"<b>/daily</b>\n↳ {stylize_text('Streak rewards')}"
        )
    elif data == "help_rpg":
        text = (
            f"{pe('sword')} <b>{stylize_text('RPG & War')}</b>\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"<b>/kill [user]</b>\n↳ {stylize_text('Murder & Loot (50%)')}\n\n"
            f"<b>/rob [amt] [user]</b>\n↳ {stylize_text('Steal coins (100% success)')}\n\n"
            f"<b>/protect 1d</b>\n↳ {stylize_text('Buy 24h shield')}\n\n"
            f"<b>/revive</b>\n↳ {stylize_text('Instant revive (500c)')}\n\n"
            f"<b>/boss</b>\n↳ {stylize_text('Fight a boss for rewards (2h CD)')}\n\n"
            f"<b>/adventure</b>\n↳ {stylize_text('Random adventure events (1h CD)')}"
        )
    elif data == "help_skills":
        text = (
            f"{pe('diamond')} <b>{stylize_text('Skills & RPG')}</b>\n"
            f"━━━━━━━━━━━━━━━\n\n"
            "<b>/fish</b>\n" + "↳ " + stylize_text("Catch fish for coins (30m CD)") + "\n\n"
            "<b>/mine</b>\n" + "↳ " + stylize_text("Mine ores for coins (45m CD)") + "\n\n"
            "<b>/chop</b>\n" + "↳ " + stylize_text("Chop wood for coins (20m CD)") + "\n\n"
            "<b>/boss</b>\n" + "↳ " + stylize_text("Fight a boss for big rewards (2h CD)") + "\n\n"
            "<b>/adventure</b>\n" + "↳ " + stylize_text("Go on an adventure (1h CD)") + "\n\n"
            "<b>/market</b>\n" + "↳ " + stylize_text("View marketplace info") + "\n\n"
            "<b>/achievements</b>\n" + "↳ " + stylize_text("View your achievements") + "\n\n"
            "<b>/profile</b>\n" + "↳ " + stylize_text("View player profile & badges") + "\n\n"
            "<b>/guild</b>\n" + "↳ " + stylize_text("Guild system (Coming Soon)")
        )
    elif data == "help_fun":
        text = (
            f"{pe('star')} <b>{stylize_text('AI & Media')}</b>\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"<b>/draw [prompt]</b>\n↳ {stylize_text('Generate anime art')}\n\n"
            f"<b>/speak [text]</b>\n↳ {stylize_text('Cute anime TTS')}\n\n"
            f"<b>/chatbot</b>\n↳ {stylize_text('AI settings')}\n\n"
            f"<b>/riddle</b>\n↳ {stylize_text('AI Quiz (1k reward)')}\n\n"
            f"<b>/dice | /slots</b>\n↳ {stylize_text('Gambling')}"
        )
    elif data == "help_group":
        text = (
            f"{pe('cherry')} <b>{stylize_text('Group Settings')}</b>\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"<b>/welcome on/off</b>\n↳ {stylize_text('Welcome images')}\n\n"
            f"<b>/ping</b>\n↳ {stylize_text('System status')}"
        )
    elif data == "help_sudo":
        if query.from_user.id not in SUDO_USERS: return await query.answer(f"{pe_safe('cross')} {stylize_text('Owner Only!')}", show_alert=True)
        target_photo = SUDO_IMG
        text = (
            f"{pe('lock')} <b>{stylize_text('Sudo Panel')}</b>\n"
            f"━━━━━━━━━━━━━━━\n\n"
            "<b>/addcoins</b>, <b>/rmcoins</b>\n"
            "<b>/freerevive</b>, <b>/unprotect</b>\n"
            "<b>/broadcast</b>, <b>/cleandb</b>\n"
            "<b>/update</b>, <b>/addsudo</b>"
        )

    try: await query.message.edit_media(InputMediaPhoto(media=target_photo, caption=text, parse_mode=ParseMode.HTML), reply_markup=kb)
    except: await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=kb)