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

from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from Annie.utils import ensure_user_exists, format_money, pe, smart_reply, stylize_text
from Annie.database import users_collection

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user_exists(update.effective_user)
    now = datetime.utcnow()
    last = user.get("last_daily")
    
    if last and (now - last) < timedelta(hours=24):
        rem = timedelta(hours=24) - (now - last)
        wait_text = f"Wait {int(rem.total_seconds()//3600)}h."
        return await smart_reply(update, f"{pe('timer')} <b>{stylize_text('Cooldown!')}</b> {stylize_text(wait_text)}")
    
    streak = user.get("daily_streak", 0)
    if last and (now - last) > timedelta(hours=48): streak = 0 # Reset
    
    streak += 1
    reward = 500
    bonus = 10000 if streak % 7 == 0 else 0
    
    msg = f"{pe('cherry')} <b>{stylize_text('Day')} {streak}!</b>\n{pe('money')} {stylize_text('Received')}: <code>{format_money(reward)}</code>"
    if bonus: msg += f"\n{pe('gift')} <b>{stylize_text('Weekly Bonus')}:</b> <code>{format_money(bonus)}</code>"
        
    users_collection.update_one(
        {"user_id": user['user_id']},
        {
            "$set": {"last_daily": now, "daily_streak": streak},
            "$inc": {"balance": reward + bonus}
        }
    )
    await smart_reply(update, msg)