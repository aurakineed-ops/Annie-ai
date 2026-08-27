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

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from Annie.config import REGISTER_BONUS, OWNER_ID, TAX_RATE, CLAIM_BONUS, MARRIED_TAX_RATE, SHOP_ITEMS, MIN_CLAIM_MEMBERS
from Annie.utils import ensure_user_exists, get_mention, format_money, resolve_target, log_to_channel, stylize_text, track_group, pe, pe_safe, smart_reply
from Annie.database import users_collection, groups_collection
from Annie.plugins.chatbot import ask_mistral_raw

# --- INVENTORY CALLBACK ---
async def inventory_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split("|")
    item_id = data[1]
    
    item = next((i for i in SHOP_ITEMS if i['id'] == item_id), None)
    if not item: return await query.answer(f"{pe_safe('cross')} Error", show_alert=True)

    rarity = f"{pe_safe('star')} {stylize_text('Common')}"
    if item['price'] > 50000: rarity = f"{pe_safe('diamond')} {stylize_text('Rare')}"
    if item['price'] > 500000: rarity = f"{pe_safe('crown')} {stylize_text('Legendary')}"
    if item['price'] > 10000000: rarity = f"{pe_safe('fire')} {stylize_text('Godly')}"

    text = f"{pe_safe('diamond')} {stylize_text(item['name'])}\n{pe_safe('money')} {format_money(item['price'])}\n{pe_safe('star')} {rarity}\n{pe_safe('shield')} {stylize_text('Safe (Until Death)')}"
    await query.answer(text, show_alert=True)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if users_collection.find_one({"user_id": user.id}): 
        return await smart_reply(update, f"{pe('cherry')} <b>{stylize_text('Ara')}?</b> {get_mention(user)}, {stylize_text('Already Registered!')}")
    
    ensure_user_exists(user)
    users_collection.update_one({"user_id": user.id}, {"$set": {"balance": REGISTER_BONUS}})
    await smart_reply(update, f"{pe('cherry')} <b>{stylize_text('Yayy')}!</b> {get_mention(user)} {stylize_text('Registered!')}\n{pe('gift')} <b>{stylize_text('Bonus')}:</b> <code>+{format_money(REGISTER_BONUS)}</code>")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target, error = await resolve_target(update, context)
    if not target and not error: target = ensure_user_exists(update.effective_user)
    elif not target: return await smart_reply(update, error)

    rank = users_collection.count_documents({"balance": {"$gt": target["balance"]}}) + 1
    heart_e = pe('heart')
    skull_e = pe('skull')
    status = f"{heart_e} {stylize_text('Alive')}" if target['status'] == 'alive' else f"{skull_e} {stylize_text('Dead')}"
    
    inventory = target.get('inventory', [])
    weapons = [i for i in inventory if i['type'] == 'weapon']
    armors = [i for i in inventory if i['type'] == 'armor']
    flex = [i for i in inventory if i['type'] == 'flex']
    
    best_w = max(weapons, key=lambda x: x['buff'])['name'] if weapons else stylize_text("None")
    best_a = max(armors, key=lambda x: x['buff'])['name'] if armors else stylize_text("None")
    
    kb = []
    row = []
    for item in flex:
        row.append(InlineKeyboardButton(item['name'], callback_data=f"inv_view|{item['id']}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    
    msg = (
        f"{pe('cherry')} <b>{get_mention(target)}</b>\n"
        f"{pe('money')} <b>{format_money(target['balance'])}</b> | {pe('trophy')} <b>#{rank}</b>\n"
        f"{pe('heart')} <b>{status}</b> | {pe('sword')} <b>{target['kills']} {stylize_text('Kills')}</b>\n\n"
        f"{pe('gift')} <b>{stylize_text('Active Gear')}:</b>\n"
        f"{pe('sword')} {best_w}\n{pe('shield')} {best_a}\n\n"
        f"{pe('diamond')} <b>{stylize_text('Flex Collection')}:</b>"
    )
    if not flex: msg += f"\n<i>{stylize_text('Empty...')}</i>"
    await smart_reply(update, msg, reply_markup=InlineKeyboardMarkup(kb) if kb else None)

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rich = users_collection.find().sort("balance", -1).limit(10)
    kills = users_collection.find().sort("kills", -1).limit(10)
    trophy_e = pe('trophy')
    def get_badge(i): return [f"{trophy_e}",f"{trophy_e}",f"{trophy_e}"][i-1] if i<=3 else f"<code>{i}.</code>"

    msg = f"{pe('cherry')} <b>{stylize_text('GLOBAL LEADERBOARD')}</b> {pe('cherry')}\n━━━━━━━━━━━━━━━\n\n{pe('money')} <b>{stylize_text('Top Richest')}</b>:\n"
    for i, d in enumerate(rich, 1): msg += f"{get_badge(i)} {get_mention(d)} » <b>{format_money(d['balance'])}</b>\n"
    
    msg += f"\n{pe('sword')} <b>{stylize_text('Top Killers')}</b>:\n"
    for i, d in enumerate(kills, 1): msg += f"{get_badge(i)} {get_mention(d)} » <b>{d.get('kills',0)} {stylize_text('Kills')}</b>\n"
    await smart_reply(update, msg)

# ... (Keep claim and give functions from previous version, they are fine) ...
# I am re-pasting them below for completeness.

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    ensure_user_exists(user)
    group_doc = groups_collection.find_one({"chat_id": chat.id})
    if not group_doc: return 
    if group_doc.get("claimed"): return await smart_reply(update, f"{pe('cross')} <b>{stylize_text('Too late!')}</b> {stylize_text('Claimed.')}")
    
    try: count = await context.bot.get_chat_member_count(chat.id)
    except: return await smart_reply(update, f"{pe('warn')} {stylize_text('Admin Rights Needed!')}")

    if count < MIN_CLAIM_MEMBERS:
        roast = await ask_mistral_raw("Roaster", f"Roast {user.first_name} for claiming in a group with only {count} members.")
        need_text = f"Need {MIN_CLAIM_MEMBERS} members."
        return await smart_reply(update, f"{pe('cross')} <b>{stylize_text('Failed!')}</b> {stylize_text(need_text)}\n{pe('fire')} {stylize_text(roast or 'Lol no.')}")
    
    users_collection.update_one({"user_id": user.id}, {"$inc": {"balance": CLAIM_BONUS}})
    groups_collection.update_one({"chat_id": chat.id}, {"$set": {"claimed": True}})
    claimed_text = f"Claimed {format_money(CLAIM_BONUS)}!"
    await smart_reply(update, f"{pe('cherry')} <b>{stylize_text(claimed_text)}</b> {pe('money')}")

async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = ensure_user_exists(update.effective_user)
    args = context.args
    if not args: return await smart_reply(update, f"{pe('warn')} <b>{stylize_text('Usage')}:</b> <code>/give 100 @user</code>")
    amount = None
    target_str = None
    for arg in args:
        if arg.isdigit() and amount is None: amount = int(arg)
        else: target_str = arg
    if amount is None: return await smart_reply(update, f"{pe('warn')} {stylize_text('Invalid Amount')}")

    target, error = await resolve_target(update, context, specific_arg=target_str)
    if not target: return await smart_reply(update, error or f"{pe('warn')} {stylize_text('Tag someone.')}")

    if amount <= 0 or sender['balance'] < amount or sender['user_id'] == target['user_id']: return await smart_reply(update, f"{pe('warn')} {stylize_text('Invalid Transaction.')}")

    tax_rate = MARRIED_TAX_RATE if sender.get("partner_id") == target["user_id"] else TAX_RATE
    tax = int(amount * tax_rate)
    final = amount - tax
    
    users_collection.update_one({"user_id": sender["user_id"]}, {"$inc": {"balance": -amount}})
    users_collection.update_one({"user_id": target["user_id"]}, {"$inc": {"balance": final}})
    users_collection.update_one({"user_id": OWNER_ID}, {"$inc": {"balance": tax}})

    msg = f"{pe('cherry')} <b>{stylize_text('Transfer Complete')}!</b>\n\n{pe('lightning')} {stylize_text('From')}: {get_mention(sender)}\n{pe('lightning')} {stylize_text('To')}: {get_mention(target)}\n{pe('money')} {stylize_text('Sent')}: <code>{format_money(final)}</code>\n{pe('shield')} {stylize_text('Tax')}: <code>{format_money(tax)}</code>"
    await smart_reply(update, msg)
    await log_to_channel(context.bot, "transfer", {"user": sender['name'], "action": f"Sent {amount} to {target['name']}", "chat": "Economy"})