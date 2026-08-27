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

import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import Forbidden
from Annie.utils import SUDO_USERS, pe, pe_safe, stylize_text, smart_reply
from Annie.database import users_collection, groups_collection

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in SUDO_USERS: return
    
    args = context.args
    reply = update.message.reply_to_message
    
    if not args and not reply:
        return await update.message.reply_text(
            f"{pe('broadcast')} <b>𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐌𝐚𝐧𝐚𝐠𝐞𝐫</b>\n\n"
            f"<b>{stylize_text('Usage')}:</b>\n"
            f"{pe('star')} /broadcast -user ({stylize_text('Reply to msg')})\n"
            f"{pe('star')} /broadcast -group ({stylize_text('Reply to msg')})\n\n"
            f"<b>{stylize_text('Flags')}:</b>\n"
            f"{pe('star')} -clean : {stylize_text('Copy msg (Use for Buttons)')}",
            parse_mode=ParseMode.HTML
        )
    
    target_type = "user" if "-user" in args else "group" if "-group" in args else None
    if not target_type:
        return await smart_reply(update, f"{pe('warn')} {stylize_text('Missing flag')}: <code>-user</code> {stylize_text('or')} <code>-group</code>")

    is_clean = "-clean" in args
    
    msg_text = None
    if not reply:
        clean_args = [a for a in args if a not in ["-user", "-group", "-clean"]]
        if not clean_args: return await smart_reply(update, f"{pe('warn')} {stylize_text('Give me a message or reply to one.')}")
        msg_text = " ".join(clean_args)

    status_msg = await smart_reply(update, f"{pe('timer')} <b>{stylize_text('Broadcasting to')} {target_type}{stylize_text('s...')}</b>")
    
    count = 0
    targets = users_collection.find({}) if target_type == "user" else groups_collection.find({})
    
    for doc in targets:
        cid = doc.get("user_id") if target_type == "user" else doc.get("chat_id")
        try:
            if reply:
                # Use copy if -clean is present, allows Buttons/Captions/Media
                if is_clean: await reply.copy(cid)
                else: await reply.forward(cid)
            else:
                await context.bot.send_message(chat_id=cid, text=msg_text, parse_mode=ParseMode.HTML)
            
            count += 1
            if count % 20 == 0: await asyncio.sleep(1)
        except Forbidden:
            if target_type == "user": users_collection.delete_one({"user_id": cid})
            else: groups_collection.delete_one({"chat_id": cid})
        except Exception: pass
        
    await status_msg.edit_text(f"{pe('check')} <b>{stylize_text('Broadcast Complete')}!</b>\n{stylize_text('Sent to')} {count} {target_type}{stylize_text('s.')}",  parse_mode=ParseMode.HTML)