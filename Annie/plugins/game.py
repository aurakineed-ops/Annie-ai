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
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from Annie.config import PROTECT_1D_COST, PROTECT_2D_COST, REVIVE_COST, AUTO_REVIVE_HOURS, OWNER_ID
from Annie.utils import ensure_user_exists, resolve_target, is_protected, get_active_protection, format_time, format_money, get_mention, check_auto_revive, stylize_text, pe, smart_reply
from Annie.database import users_collection
from Annie.plugins.chatbot import ask_mistral_raw

# --- AI NARRATION ---
async def get_narrative(action_type, attacker_mention, target_mention):
    if action_type == 'kill':
        prompt = "Write a funny, savage kill message where 'P1' kills 'P2'. Max 15 words. Use Hinglish."
    elif action_type == 'rob':
        prompt = "Write a funny robbery message where 'P1' steals from 'P2'. Max 15 words. Use Hinglish."
    else: return "P1 interaction P2."
    res = await ask_mistral_raw("Game Narrator", prompt, 50)
    text = res if res and "P1" in res else f"P1 {action_type} P2!"
    return text.replace("P1", attacker_mention).replace("P2", target_mention)

# --- KILL ---
async def kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attacker = ensure_user_exists(update.effective_user)
    target, error = await resolve_target(update, context)
    if not target: return await smart_reply(update, error if error else f"{pe('warn')} <b>{stylize_text('No Target')}</b>")

    # Checks
    if target.get('is_bot'): return await smart_reply(update, f"{pe('robot')} <b>{stylize_text('Bot Shield!')}</b> {stylize_text('Cannot kill robots.')}")
    if target['user_id'] == OWNER_ID: return await smart_reply(update, f"{pe('cherry')} <b>{stylize_text('Senpai Shield!')}</b> {stylize_text('Cannot kill the owner.')}")
    if attacker['status'] == 'dead': return await smart_reply(update, f"{pe('skull')} <b>{stylize_text('You are dead!')}</b> {stylize_text('Wait 6h or')} /revive.")
    if target['user_id'] == attacker['user_id']: return await smart_reply(update, f"{pe('cherry')} {stylize_text('Do not kill yourself.')}")
    if target['status'] == 'dead': return await smart_reply(update, f"{pe('skull')} <b>{stylize_text('Already Dead!')}</b>")
    
    expiry = get_active_protection(target)
    if expiry:
        rem = expiry - datetime.utcnow()
        return await smart_reply(update, f"{pe('shield')} <b>{stylize_text('Blocked!')}</b> {stylize_text('Target is protected for')} <code>{format_time(rem)}</code>.")

    # Logic
    base_reward = random.randint(100, 200)
    buff = sum(i['buff'] for i in attacker.get('inventory', []) if i['type'] == 'weapon')
    final_reward = int(base_reward * (1 + buff))
    
    # Loot Item (50%)
    stolen_item_text = ""
    t_inv = target.get('inventory', [])
    if t_inv and random.random() < 0.50:
        item = random.choice(t_inv)
        users_collection.update_one({"user_id": target["user_id"]}, {"$pull": {"inventory": {"id": item['id']}}})
        users_collection.update_one({"user_id": attacker["user_id"]}, {"$push": {"inventory": item}})
        stolen_item_text = f"\n{pe('cart')} <b>{stylize_text('Looted')}:</b> {item['name']}"

    # Execute
    users_collection.update_one({"user_id": target["user_id"]}, {"$set": {"status": "dead", "death_time": datetime.utcnow()}})
    users_collection.update_one({"user_id": attacker["user_id"]}, {"$inc": {"kills": 1, "balance": final_reward}})

    narration = await get_narrative("kill", get_mention(attacker), get_mention(target))
    buff_text = f"(+{int(buff*100)}% {stylize_text('Buff')})" if buff > 0 else ""

    # Kill uses only confirmed working premium emoji IDs
    e_cherry = '<tg-emoji emoji-id="6122790473917537632">🌸</tg-emoji>'
    e_sword = '<tg-emoji emoji-id="6129415619885407680">⚔️</tg-emoji>'
    e_skull = '<tg-emoji emoji-id="6129639980387015660">💀</tg-emoji>'
    e_money = '<tg-emoji emoji-id="5956031393623445676">💰</tg-emoji>'
    e_book = '<tg-emoji emoji-id="5859588916604047101">📖</tg-emoji>'

    await smart_reply(update,
        f"{e_cherry} <b>{stylize_text('MURDER')}!</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"{e_book} <i>{narration}</i>\n\n"
        f"{e_sword} <b>{stylize_text('Killer')}:</b> {get_mention(attacker)}\n"
        f"{e_skull} <b>{stylize_text('Victim')}:</b> {get_mention(target)}\n"
        f"{e_money} <b>{stylize_text('Loot')}:</b> <code>{format_money(final_reward)}</code> {buff_text}{stolen_item_text}"
    )

# --- ROB ---
async def rob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attacker = ensure_user_exists(update.effective_user)
    if not context.args: return await smart_reply(update, f"{pe('warn')} <code>/rob 100 @user</code>")
    try: amount = int(context.args[0])
    except: return await smart_reply(update, f"{pe('warn')} {stylize_text('Invalid Amount')}")

    target_arg = context.args[1] if len(context.args) > 1 else None
    target, error = await resolve_target(update, context, specific_arg=target_arg)
    if not target: return await smart_reply(update, error if error else f"{pe('warn')} <code>/rob 100 @user</code>")

    if target.get('is_bot') or target['user_id'] == OWNER_ID: return await smart_reply(update, f"{pe('shield')} {stylize_text('Protected Entity.')}")
    if attacker['status'] == 'dead': return await smart_reply(update, f"{pe('skull')} {stylize_text('Dead men steal no coins.')}")
    if target['user_id'] == attacker['user_id']: return await smart_reply(update, f"{pe('cherry')} {stylize_text('No.')}")
    
    expiry = get_active_protection(target)
    if expiry:
        rem = expiry - datetime.utcnow()
        return await smart_reply(update, f"{pe('shield')} <b>{stylize_text('Shielded!')}</b> {stylize_text('Protected for')} <code>{format_time(rem)}</code>.")

    if target['balance'] < amount: return await smart_reply(update, f"{pe('down')} {stylize_text('Too poor.')}")

    # Block
    block_chance = sum(i['buff'] for i in target.get('inventory', []) if i['type'] == 'armor')
    if random.random() < block_chance:
        return await smart_reply(update, f"{pe('shield')} <b>{stylize_text('Blocked!')}</b> {get_mention(target)} {stylize_text('armor stopped you!')}")

    # Loot Item (Dead Only)
    stolen_item_text = ""
    if target['status'] == 'dead':
        t_inv = target.get('inventory', [])
        if t_inv and random.random() < 0.20:
            item = random.choice(t_inv)
            users_collection.update_one({"user_id": target["user_id"]}, {"$pull": {"inventory": {"id": item['id']}}})
            users_collection.update_one({"user_id": attacker["user_id"]}, {"$push": {"inventory": item}})
            stolen_item_text = f"\n{pe('cart')} <b>{stylize_text('Looted Corpse')}:</b> {item['name']}"

    # Execute
    users_collection.update_one({"user_id": target["user_id"]}, {"$inc": {"balance": -amount}})
    users_collection.update_one({"user_id": attacker["user_id"]}, {"$inc": {"balance": amount}})
    
    att_link = get_mention(attacker)
    tar_link = get_mention(target)
    narration = await get_narrative("rob", att_link, tar_link)
    
    header = f"{pe('cherry')} <b>{stylize_text('GRAVE ROBBERY')}!</b>" if target['status'] == 'dead' else f"{pe('cherry')} <b>{stylize_text('ROBBERY')}!</b>"

    await smart_reply(update,
        f"{header}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"{pe('book')} <i>{narration}</i>\n\n"
        f"{pe('sword')} <b>{stylize_text('Thief')}:</b> {att_link}\n"
        f"{pe('money')} <b>{stylize_text('Stolen')}:</b> <code>{format_money(amount)}</code>{stolen_item_text}"
    )

# --- PROTECT ---
async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = ensure_user_exists(update.effective_user)
    if not context.args: return await smart_reply(update, f"{pe('shield')} <b>{stylize_text('Usage')}:</b> <code>/protect 1d</code>")

    dur = context.args[0].lower()
    if dur == '1d': cost, days = PROTECT_1D_COST, 1
    elif dur == '2d': cost, days = PROTECT_2D_COST, 2
    else: return await smart_reply(update, f"{pe('warn')} {stylize_text('1d or 2d only!')}")

    target_arg = context.args[1] if len(context.args) > 1 else None
    target, _ = await resolve_target(update, context, specific_arg=target_arg)
    if not target: target = sender
    is_self = target['user_id'] == sender['user_id']

    if not is_self and sender.get("partner_id") != target["user_id"]:
         return await smart_reply(update, f"{pe('cross')} {stylize_text('You can only protect yourself or your partner!')}")

    expiry = get_active_protection(target)
    if expiry:
        rem = expiry - datetime.utcnow()
        msg = f"{pe('shield')} <b>{stylize_text('Already Safe!')}</b> {stylize_text('Expires in')} <code>{format_time(rem)}</code>."
        if not is_self: msg = f"{pe('shield')} <b>{stylize_text('Safe!')}</b> {get_mention(target)} {stylize_text('has')} <code>{format_time(rem)}</code> {stylize_text('left.')}"
        return await smart_reply(update, msg)
    
    if sender['balance'] < cost: return await smart_reply(update, f"{pe('cross')} <b>{stylize_text('Poor!')}</b> {stylize_text('Need')} <code>{format_money(cost)}</code>.")

    users_collection.update_one({"user_id": sender["user_id"]}, {"$inc": {"balance": -cost}})
    expiry_dt = datetime.utcnow() + timedelta(days=days)
    users_collection.update_one({"user_id": target["user_id"]}, {"$set": {"protection_expiry": expiry_dt}})
    
    partner_id = target.get("partner_id")
    extra = ""
    if partner_id:
        users_collection.update_one({"user_id": partner_id}, {"$set": {"protection_expiry": expiry_dt}})
        extra = f"\n{pe('heart')} <b>{stylize_text('Bonus')}:</b> {stylize_text('Partner also protected!')}"

    if is_self: await smart_reply(update, f"{pe('shield')} <b>{stylize_text('Shield Active')}!</b> {stylize_text('Safe for')} {days} {stylize_text('days.')}{extra}")
    else: await smart_reply(update, f"{pe('shield')} <b>{stylize_text('Guardian')}!</b> {stylize_text('You protected')} {get_mention(target)}.{extra}")

async def revive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reviver = ensure_user_exists(update.effective_user)
    target, _ = await resolve_target(update, context)
    if not target: target = reviver

    if target['status'] == 'alive': return await smart_reply(update, f"{pe('star')} {stylize_text('Alive!')}")
    
    if check_auto_revive(target):
        return await smart_reply(update, f"{pe('star')} <b>{stylize_text('Miracle!')}</b> {stylize_text('Auto-revived just now.')}")

    if reviver['balance'] < REVIVE_COST: return await smart_reply(update, f"{pe('cross')} {stylize_text('Need')} <code>{format_money(REVIVE_COST)}</code>.")

    users_collection.update_one({"user_id": reviver["user_id"]}, {"$inc": {"balance": -REVIVE_COST}})
    users_collection.update_one({"user_id": OWNER_ID}, {"$inc": {"balance": REVIVE_COST}})
    users_collection.update_one({"user_id": target["user_id"]}, {"$set": {"status": "alive", "death_time": None}})
    await smart_reply(update, f"{pe('cherry')} <b>{stylize_text('Revived')}!</b> {stylize_text('Paid')} {format_money(REVIVE_COST)}.")