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

import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatType
from Annie.database import groups_collection
from Annie.utils import get_mention, ensure_user_exists, pe, stylize_text, smart_reply
from Annie.config import WELCOME_IMG_URL, BOT_NAME, START_IMG_URL, SUPPORT_GROUP

async def welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable/Disable Welcomes."""
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    
    if chat.type == ChatType.PRIVATE:
        return await smart_reply(update, f"{pe('cross')} <b>{stylize_text('This command works in grp only baby!')}</b>")
    
    member = await chat.get_member(user.id)
    if member.status not in ['administrator', 'creator']:
        return await smart_reply(update, f"{pe('cross')} <b>{stylize_text('Admin only!')}</b>")

    if not args:
        return await smart_reply(update, f"{pe('warn')} <b>{stylize_text('Usage')}:</b> <code>/welcome on</code> {stylize_text('or')} <code>off</code>")
    
    state = args[0].lower()
    if state in ['on', 'enable', 'yes']:
        groups_collection.update_one({"chat_id": chat.id}, {"$set": {"welcome_enabled": True}}, upsert=True)
        await smart_reply(update, f"{pe('check')} <b>𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐌𝐞𝐬𝐬𝐚𝐠𝐞𝐬 𝐄𝐧𝐚𝐛𝐥𝐞𝐝!</b>")
    elif state in ['off', 'disable', 'no']:
        groups_collection.update_one({"chat_id": chat.id}, {"$set": {"welcome_enabled": False}}, upsert=True)
        await smart_reply(update, f"{pe('cross')} <b>𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐌𝐞𝐬𝐬𝐚𝐠𝐞𝐬 𝐃𝐢𝐬𝐚𝐛𝐥𝐞𝐝!</b>")
    else:
        await smart_reply(update, f"{pe('warn')} {stylize_text('Invalid option. Use')} <code>on</code> {stylize_text('or')} <code>off</code>.")

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    
    for member in update.message.new_chat_members:
        # --- 🤖 BOT ADDED TO GROUP ---
        if member.id == context.bot.id:
            adder = update.message.from_user
            ensure_user_exists(adder)
            
            groups_collection.update_one({"chat_id": chat.id}, {"$set": {"welcome_enabled": True, "title": chat.title}}, upsert=True)
            
            cherry_e = pe('cherry')
            star_e = pe('star')
            gift_e = pe('gift')
            txt = (
                f"{cherry_e} <b>𝐀𝐫𝐢𝐠𝐚𝐭𝐨 {get_mention(adder)}!</b>\n\n"
                f"ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴀᴅᴅɪɴɢ <b>{chat.title}</b>! {star_e}\n\n"
                f"{gift_e} <b>ꜰɪʀꜱᴛ ᴛɪᴍᴇ ʙᴏɴᴜꜱ:</b>\n"
                f"ᴛʏᴘᴇ <code>/claim</code> ꜰᴀꜱᴛ ᴛᴏ ɢᴇᴛ 𝟐,𝟎𝟎𝟎 ᴄᴏɪɴꜱ!\n"
                f"(ᴏɴʟʏ ᴛʜᴇ ꜰɪʀꜱᴛ ᴘᴇʀꜱᴏɴ ɢᴇᴛꜱ ɪᴛ!)"
            )
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("💬 𝐒𝐮𝐩𝐩𝐨𝐫𝐭", url=SUPPORT_GROUP)]])
            
            # Use Welcome Image (gyi5iu.jpg) for this interaction
            try: await update.message.reply_photo(WELCOME_IMG_URL, caption=txt, parse_mode=ParseMode.HTML, reply_markup=kb)
            except: await update.message.reply_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)

        # --- 👤 USER JOINED GROUP ---
        else:
            ensure_user_exists(member)
            group_data = groups_collection.find_one({"chat_id": chat.id})
            
            if group_data and group_data.get("welcome_enabled"):
                greetings = ["Hello", "Hiii", "Welcome", "Kon'nichiwa"]
                greet = random.choice(greetings)
                cherry_e = pe('cherry')
                heart_e = pe('heart')
                txt = f"{cherry_e} <b>{greet} {get_mention(member)}!</b>\n\nᴡᴇʟᴄᴏᴍᴇ ᴛᴏ <b>{chat.title}</b> {heart_e}\nᴅᴏɴ'ᴛ ꜰᴏʀɢᴇᴛ ᴛᴏ /register!"
                try: await update.message.reply_photo(WELCOME_IMG_URL, caption=txt, parse_mode=ParseMode.HTML)
                except: await smart_reply(update, txt)