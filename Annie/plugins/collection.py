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
import httpx
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from Annie.database import groups_collection, users_collection
from Annie.utils import ensure_user_exists, get_mention, pe

# In-Memory Drop Storage
active_drops = {}
DROP_MESSAGE_COUNT = 100

WAIFU_NAMES = [
    ("Rem", "rem"), ("Ram", "ram"), ("Emilia", "emilia"), ("Asuna", "asuna"), 
    ("Zero Two", "zero two"), ("Makima", "makima"), ("Nezuko", "nezuko"),
    ("Hinata", "hinata"), ("Sakura", "sakura"), ("Mikasa", "mikasa"), 
    ("Yor", "yor"), ("Anya", "anya"), ("Power", "power")
]

async def check_drops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_chat: return
    chat = update.effective_chat
    if chat.type == "private": return

    group = groups_collection.find_one_and_update(
        {"chat_id": chat.id}, {"$inc": {"msg_count": 1}}, upsert=True, return_document=True
    )
    
    if group.get("msg_count", 0) % DROP_MESSAGE_COUNT == 0:
        char = random.choice(WAIFU_NAMES)
        name, slug = char
        
        async with httpx.AsyncClient() as client:
            r = await client.get(f"https://api.waifu.im/search?included_tags={slug}")
            url = r.json()['images'][0]['url'] if r.status_code == 200 else "https://telegra.ph/file/5e5480760e412bd402e88.jpg"

        active_drops[chat.id] = name.lower()
        
        await update.message.reply_photo(
            photo=url,
            caption=f"{pe('cherry')} <b>ᴀ ᴡᴀɪꜰᴜ ᴀᴘᴘᴇᴀʀᴇᴅ!</b>\n\nɢᴜᴇꜱꜱ ʜᴇʀ ɴᴀᴍᴇ ᴛᴏ ᴄᴏʟʟᴇᴄᴛ ʜᴇʀ!\n<i>ʀᴇᴘʟʏ ᴛᴏ ᴛʜɪꜱ ɪᴍᴀɢᴇ.</i>",
            parse_mode=ParseMode.HTML
        )

async def collect_waifu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.message
    
    if chat.id not in active_drops: return
    
    guess = msg.text.lower().strip()
    correct = active_drops[chat.id]
    
    if guess == correct:
        user = ensure_user_exists(msg.from_user)
        del active_drops[chat.id]
        
        rarity = random.choice(["Common", "Rare", "Epic", "Legendary"])
        waifu = {"name": correct.title(), "rarity": rarity, "date": datetime.utcnow()}
        users_collection.update_one({"user_id": user['user_id']}, {"$push": {"waifus": waifu}})
        
        await msg.reply_text(
            f"{pe('cherry')} <b>ᴄᴏʟʟᴇᴄᴛᴇᴅ!</b>\n\n{pe('heart')} {get_mention(user)} ᴄᴀᴜɢʜᴛ <b>{correct.title()}</b>!\n{pe('star')} <b>ʀᴀʀɪᴛʏ:</b> {rarity}",
            parse_mode=ParseMode.HTML
        )