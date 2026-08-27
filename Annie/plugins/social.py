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
import asyncio
import re as _re
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatType
from Annie.utils import ensure_user_exists, resolve_target, get_mention, format_money, stylize_text, pe, pe_safe, smart_reply
from Annie.database import users_collection
from Annie.config import DIVORCE_COST
from Annie.plugins.chatbot import ask_mistral_raw

async def _safe_edit_social(msg, text):
    """Edit message with fallback if Document_invalid."""
    try:
        await msg.edit_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        if "Document_invalid" in str(e):
            clean = _re.sub(r'<tg-emoji emoji-id="[^"]*">([^<]*)</tg-emoji>', r'\1', text)
            await msg.edit_text(clean, parse_mode=ParseMode.HTML)
        else:
            raise

# ... (Helpers remain same) ...
def get_progress_bar(percent):
    filled = int(percent / 10)
    bar = "█" * filled + "▒" * (10 - filled)
    return bar
def get_love_comment(percent):
    if percent < 30: return f"{pe('broken_heart')} {stylize_text('Terrible!')}"
    if percent < 80: return f"{pe('heart')} {stylize_text('Cute!')}"
    return f"{pe('fire')} {stylize_text('Soulmates!')}"

async def couple_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == ChatType.PRIVATE: return await smart_reply(update, f"{pe('cross')} {stylize_text('Group Only!')}")

    user1 = ensure_user_exists(user)
    target, _ = await resolve_target(update, context)
    if target: user2 = target
    else:
        try:
            pipeline = [{"$match": {"seen_groups": chat.id, "user_id": {"$ne": user.id}}}, {"$sample": {"size": 1}}]
            results = list(users_collection.aggregate(pipeline))
            if not results: return await smart_reply(update, f"{pe('broken_heart')} {stylize_text('Forever Alone.')}")
            user2 = results[0]
        except: return
    
    percent = random.randint(0, 100)
    star_e = pe('star')
    await update.message.reply_text(
        f"{pe('cherry')} <b>{stylize_text('Couple Matcher')}</b>\n━━━━━━━━━━━━━━━\n\n{pe('heart')} {get_mention(user1)}\n{pe('heart')} {get_mention(user2)}\n\n{star_e} <b>{stylize_text('Score')}:</b> {percent}%\n<code>{get_progress_bar(percent)}</code>\n{star_e} <i>{get_love_comment(percent)}</i>",
        parse_mode=ParseMode.HTML
    )

async def propose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = ensure_user_exists(update.effective_user)
    if sender.get("partner_id"): return await smart_reply(update, f"{pe('heart')} {stylize_text('Already Married!')}")
    
    target_arg = context.args[0] if context.args else None
    target, error = await resolve_target(update, context, specific_arg=target_arg)
    if not target: return await smart_reply(update, error or f"{stylize_text('Usage')}: <code>/propose @user</code>")
    if target['user_id'] == sender['user_id'] or target.get('partner_id'): return await smart_reply(update, f"{pe('broken_heart')} {stylize_text('Invalid.')}")

    s_id, t_id = sender['user_id'], target['user_id']
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("💍 Accept", callback_data=f"marry_y|{s_id}|{t_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"marry_n|{s_id}|{t_id}")]])
    
    msg = await smart_reply(update, f"{pe('cherry')} <b>{stylize_text('Proposal')}!</b>\n\n{pe('heart')} {get_mention(sender)} {stylize_text('loves')} {get_mention(target)}!\n<i>{stylize_text('Will you marry them?')}</i>\n{pe('timer')} {stylize_text('30s...')}", reply_markup=kb)
    
    async def delete():
        await asyncio.sleep(30)
        try: await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id, text=f"{pe_safe('cross')} {stylize_text('Expired.')}", parse_mode=ParseMode.HTML)
        except: pass
    asyncio.create_task(delete())

async def marry_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_arg = context.args[0] if context.args else None
    target, _ = await resolve_target(update, context, specific_arg=target_arg)
    user = target if target else ensure_user_exists(update.effective_user)
    
    pid = user.get("partner_id")
    if pid:
        p = users_collection.find_one({"user_id": pid})
        status = f"{pe('ring')} {stylize_text('Married to')} {get_mention(p) if p else pid}"
    else: status = f"{pe('star')} {stylize_text('Single')}"
    
    await smart_reply(update, f"{pe('cherry')} <b>{stylize_text('Status')}:</b>\n{pe('heart')} {get_mention(user)}\n{status}")

async def divorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user_exists(update.effective_user)
    if not user.get("partner_id"): return await smart_reply(update, f"{pe('cross')} {stylize_text('Single.')}")
    if user['balance'] < DIVORCE_COST: return await smart_reply(update, f"{pe('cross')} {stylize_text('Cost')}: {format_money(DIVORCE_COST)}")
    
    pid = user["partner_id"]
    users_collection.update_one({"user_id": user["user_id"]}, {"$set": {"partner_id": None}, "$inc": {"balance": -DIVORCE_COST}})
    users_collection.update_one({"user_id": pid}, {"$set": {"partner_id": None}})
    await smart_reply(update, f"{pe('broken_heart')} <b>{stylize_text('Divorced!')}</b> {stylize_text('Paid')} {format_money(DIVORCE_COST)}.")

async def proposal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split("|")
    action, p_id, t_id = data[0], int(data[1]), int(data[2])
    
    if query.from_user.id != t_id: return await query.answer(f"{pe_safe('cross')} {stylize_text('Not for you!')}", show_alert=True)
    
    if action == "marry_y":
        users_collection.update_one({"user_id": p_id}, {"$set": {"partner_id": t_id}})
        users_collection.update_one({"user_id": t_id}, {"$set": {"partner_id": p_id}})
        await _safe_edit_social(query.message, f"{pe('heart')} <b>{stylize_text('Just Married')}!</b>\n<a href='tg://user?id={p_id}'>{stylize_text('P1')}</a> {pe('heart')} <a href='tg://user?id={t_id}'>{stylize_text('P2')}</a>\n{pe('star')} {stylize_text('5% Tax Perk Active!')}")
    elif action == "marry_n":
        roast = await ask_mistral_raw("Roaster", "Roast a rejected proposal.")
        await _safe_edit_social(query.message, f"{pe('cross')} <b>{stylize_text('Rejected!')}</b>\n{pe('fire')} {stylize_text(roast or 'Ouch.')}")