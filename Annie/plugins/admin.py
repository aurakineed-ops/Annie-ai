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
import os
import re as _re
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from Annie.config import OWNER_ID, UPSTREAM_REPO, GIT_TOKEN
from Annie.utils import SUDO_USERS, get_mention, resolve_target, format_money, reload_sudoers, pe, pe_safe, stylize_text, smart_reply
from Annie.database import users_collection, sudoers_collection, groups_collection

async def _safe_edit(msg, text, **kwargs):
    """Edit message with fallback if Document_invalid."""
    try:
        await msg.edit_text(text, parse_mode=ParseMode.HTML, **kwargs)
    except Exception as e:
        if "Document_invalid" in str(e):
            clean = _re.sub(r'<tg-emoji emoji-id="[^"]*">([^<]*)</tg-emoji>', r'\1', text)
            await msg.edit_text(clean, parse_mode=ParseMode.HTML, **kwargs)
        else:
            raise

async def sudo_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in SUDO_USERS: return
    msg = (
        f"{pe('lock')} <b>𝐒𝐮𝐝𝐨 𝐏𝐚𝐧𝐞𝐥</b>\n\n"
        f"<b>{pe('money')} {stylize_text('Economy')}:</b>\n"
        f"{pe('star')} /addcoins [amt] [user]\n"
        f"{pe('star')} /rmcoins [amt] [user]\n"
        f"{pe('star')} /freerevive [user]\n"
        f"{pe('star')} /unprotect [user]\n\n"
        f"<b>{pe('broadcast')} {stylize_text('Broadcast')}:</b>\n"
        f"{pe('star')} /broadcast -user ({stylize_text('Reply')})\n"
        f"{pe('star')} /broadcast -group ({stylize_text('Reply')})\n"
        f"{pe('star')} <i>{stylize_text('Flag')}:</i> -clean ({stylize_text('No Tag')})\n\n"
        f"<b>{pe('crown')} 𝐎𝐰𝐧𝐞𝐫 𝐎𝐧𝐥𝐲:</b>\n"
        f"{pe('star')} /update ({stylize_text('Pull Changes')})\n"
        f"{pe('star')} /addsudo [user]\n"
        f"{pe('star')} /rmsudo [user]\n"
        f"{pe('star')} /cleandb\n"
        f"{pe('star')} /sudolist"
    )
    await smart_reply(update, msg)

# --- UPDATER LOGIC (Unchanged) ---
async def update_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    if not UPSTREAM_REPO: return await smart_reply(update, f"{pe('cross')} <b>UPSTREAM_REPO</b> {stylize_text('missing')}!")
    msg = await smart_reply(update, f"{pe('refresh')} <b>{stylize_text('Checking for updates...')}</b>")
    try:
        import git
        try: repo = git.Repo()
        except: 
            repo = git.Repo.init()
            origin = repo.create_remote('origin', UPSTREAM_REPO)
            origin.fetch()
            repo.create_head('master', origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
    except ImportError: return await msg.edit_text(f"{pe('cross')} <b>{stylize_text('Git Error')}:</b> {stylize_text('Library missing')}.", parse_mode=ParseMode.HTML)
    except Exception as e: return await msg.edit_text(f"{pe('cross')} <b>{stylize_text('Git Error')}:</b> <code>{e}</code>", parse_mode=ParseMode.HTML)
    repo_url = UPSTREAM_REPO
    if GIT_TOKEN and "https://github.com" in repo_url: repo_url = repo_url.replace("https://", f"https://{GIT_TOKEN}@")
    try:
        repo.remotes.origin.set_url(repo_url)
        repo.remotes.origin.pull()
        await msg.edit_text(f"{pe('check')} <b>{stylize_text('Update Found')}!</b>\n{stylize_text('Restarting bot now...')} {pe('lightning')}", parse_mode=ParseMode.HTML)
        args = [sys.executable, "raj.py"]
        os.execl(sys.executable, *args)
    except Exception as e: await msg.edit_text(f"{pe('cross')} <b>{stylize_text('Update Failed')}!</b>\n{stylize_text('Error')}: <code>{e}</code>", parse_mode=ParseMode.HTML)

# --- ADMIN COMMANDS ---

async def sudolist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"{pe('crown')} <b>𝐎𝐰𝐧𝐞𝐫 & 𝐒𝐮𝐝𝐨𝐞𝐫𝐬:</b>\n\n"
    owner_doc = users_collection.find_one({"user_id": OWNER_ID})
    if not owner_doc:
        try: 
            u = await context.bot.get_chat(OWNER_ID)
            owner_name = u.first_name
        except: owner_name = "Owner"
        msg += f"{pe('crown')} <a href='tg://user?id={OWNER_ID}'><b>{html.escape(owner_name)}</b></a> ({stylize_text('Owner')})\n"
    else: msg += f"{pe('crown')} {get_mention(owner_doc)} ({stylize_text('Owner')})\n"
    for uid in SUDO_USERS:
        if uid == OWNER_ID: continue
        u_doc = users_collection.find_one({"user_id": uid})
        if u_doc: msg += f"{pe('user')} {get_mention(u_doc)}\n"
        else: msg += f"{pe('user')} <code>{uid}</code>\n"
    await smart_reply(update, msg)

# --- CONFIRMATION ---

def get_kb(act, arg):
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ 𝐘𝐞𝐬", callback_data=f"cnf|{act}|{arg}"), InlineKeyboardButton("❌ 𝐍𝐨", callback_data="cnf|cancel|0")]])

async def ask(update, text, act, arg):
    await smart_reply(update, f"{pe('warn')} <b>{stylize_text('Wait')}!</b> {text}\n{stylize_text('Are you sure')}?", reply_markup=get_kb(act, arg))

def parse_amount_and_target(args):
    amount = None
    target_str = None
    for arg in args:
        if arg.isdigit() and amount is None: amount = int(arg)
        else: target_str = arg
    return amount, target_str

# --- HANDLERS ---

async def addsudo(update, context):
    if update.effective_user.id != OWNER_ID: return
    target_arg = context.args[0] if context.args else None
    target, err = await resolve_target(update, context, specific_arg=target_arg)
    if not target: return await smart_reply(update, err or f"{pe('warn')} {stylize_text('Usage')}: /addsudo [user]")
    if target['user_id'] in SUDO_USERS: return await smart_reply(update, f"{pe('warn')} {stylize_text('Already Sudoer.')}")
    await ask(update, f"{stylize_text('Promote')} {get_mention(target)}?", "addsudo", str(target['user_id']))

async def rmsudo(update, context):
    if update.effective_user.id != OWNER_ID: return
    target_arg = context.args[0] if context.args else None
    target, err = await resolve_target(update, context, specific_arg=target_arg)
    if not target: return await smart_reply(update, err or f"{pe('warn')} {stylize_text('Usage')}: /rmsudo [user]")
    if target['user_id'] not in SUDO_USERS: return await smart_reply(update, f"{pe('warn')} {stylize_text('Not a Sudoer.')}")
    await ask(update, f"{stylize_text('Demote')} {get_mention(target)}?", "rmsudo", str(target['user_id']))

async def addcoins(update, context):
    if update.effective_user.id not in SUDO_USERS: return
    if not context.args: return await smart_reply(update, f"{pe('warn')} {stylize_text('Usage')}: <code>/addcoins 100 @user</code>")
    amount, target_str = parse_amount_and_target(context.args)
    if amount is None: return await smart_reply(update, f"{pe('warn')} {stylize_text('Invalid Amount')}!")
    target, err = await resolve_target(update, context, specific_arg=target_str)
    if not target: return await smart_reply(update, err or f"{pe('warn')} {stylize_text('Reply or Tag user.')}")
    await ask(update, f"{stylize_text('Give')} <b>{format_money(amount)}</b> {stylize_text('to')} {get_mention(target)}?", "addcoins", f"{target['user_id']}|{amount}")

async def rmcoins(update, context):
    if update.effective_user.id not in SUDO_USERS: return
    if not context.args: return await smart_reply(update, f"{pe('warn')} {stylize_text('Usage')}: <code>/rmcoins 100 @user</code>")
    amount, target_str = parse_amount_and_target(context.args)
    if amount is None: return await smart_reply(update, f"{pe('warn')} {stylize_text('Invalid Amount')}!")
    target, err = await resolve_target(update, context, specific_arg=target_str)
    if not target: return await smart_reply(update, err or f"{pe('warn')} {stylize_text('Reply or Tag user.')}")
    await ask(update, f"{stylize_text('Remove')} <b>{format_money(amount)}</b> {stylize_text('from')} {get_mention(target)}?", "rmcoins", f"{target['user_id']}|{amount}")

async def freerevive(update, context):
    if update.effective_user.id not in SUDO_USERS: return
    target_arg = context.args[0] if context.args else None
    target, err = await resolve_target(update, context, specific_arg=target_arg)
    if not target: return await smart_reply(update, err or f"{pe('warn')} {stylize_text('Usage')}: /freerevive [user]")
    await ask(update, f"{stylize_text('Free Revive')} {get_mention(target)}?", "freerevive", str(target['user_id']))

async def unprotect(update, context):
    """Remove protection from a user."""
    if update.effective_user.id not in SUDO_USERS: return
    target_arg = context.args[0] if context.args else None
    target, err = await resolve_target(update, context, specific_arg=target_arg)
    if not target: return await smart_reply(update, err or f"{pe('warn')} {stylize_text('Usage')}: /unprotect [user]")
    await ask(update, f"{stylize_text('Remove')} {pe('shield')} {stylize_text('from')} {get_mention(target)}?", "unprotect", str(target['user_id']))

async def cleandb(update, context):
    if update.effective_user.id != OWNER_ID: return
    await ask(update, f"<b>{stylize_text('WIPE DATABASE')}?</b> {pe('clean')}", "cleandb", "0")

async def getemoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Extract custom emoji IDs from a replied message."""
    if update.effective_user.id not in SUDO_USERS: return
    reply = update.message.reply_to_message
    if not reply:
        return await smart_reply(update, f"{pe('warn')} <b>{stylize_text('Reply')}</b> {stylize_text('to a message containing premium emojis')}!")
    
    entities = reply.entities or []
    found = []
    for ent in entities:
        if ent.type == "custom_emoji":
            emoji_char = reply.text[ent.offset:ent.offset + ent.length]
            found.append(f"<code>{emoji_char}</code> = <code>{ent.custom_emoji_id}</code>")
    
    if not found:
        return await smart_reply(update, f"{pe('cross')} {stylize_text('No custom emojis found in that message.')}")
    
    text = f"{pe('star')} <b>{stylize_text('Custom Emoji IDs Found')}:</b>\n\n" + "\n".join(found)
    text += f"\n\n<i>{stylize_text('Copy these IDs to Annie/utils.py')}</i>"
    await smart_reply(update, text)

async def confirm_handler(update, context):
    q = update.callback_query
    await q.answer()
    if q.from_user.id not in SUDO_USERS: return await _safe_edit(q.message, f"{pe('cross')} <b>{stylize_text('Annie')}!</b> {stylize_text('Not for you.')}")
    
    data = q.data.split("|")
    act = data[1]
    if act == "cancel": return await _safe_edit(q.message, f"{pe('cross')} <b>{stylize_text('Cancelled.')}</b>")

    if act == "addsudo":
        uid = int(data[2])
        sudoers_collection.insert_one({"user_id": uid})
        reload_sudoers()
        await _safe_edit(q.message, f"{pe('check')} {stylize_text('User')} <code>{uid}</code> {stylize_text('promoted.')}")
    elif act == "rmsudo":
        uid = int(data[2])
        sudoers_collection.delete_one({"user_id": uid})
        reload_sudoers()
        await _safe_edit(q.message, f"{pe('clean')} {stylize_text('User')} <code>{uid}</code> {stylize_text('demoted.')}")
    elif act == "addcoins":
        uid, amt = int(data[2]), int(data[3])
        users_collection.update_one({"user_id": uid}, {"$inc": {"balance": amt}})
        await _safe_edit(q.message, f"{pe('check')} {stylize_text('Added')} <b>{format_money(amt)}</b> {stylize_text('to')} <code>{uid}</code>.")
    elif act == "rmcoins":
        uid, amt = int(data[2]), int(data[3])
        users_collection.update_one({"user_id": uid}, {"$inc": {"balance": -amt}})
        await _safe_edit(q.message, f"{pe('check')} {stylize_text('Removed')} <b>{format_money(amt)}</b> {stylize_text('from')} <code>{uid}</code>.")
    elif act == "freerevive":
        uid = int(data[2])
        users_collection.update_one({"user_id": uid}, {"$set": {"status": "alive", "death_time": None}})
        await _safe_edit(q.message, f"{pe('check')} {stylize_text('User')} <code>{uid}</code> {stylize_text('revived.')}")
    elif act == "unprotect":
        uid = int(data[2])
        users_collection.update_one({"user_id": uid}, {"$set": {"protection_expiry": datetime.utcnow()}}) 
        await _safe_edit(q.message, f"{pe('shield')} {stylize_text('Protection')} <b>{stylize_text('REMOVED')}</b> {stylize_text('from')} <code>{uid}</code>.")
    elif act == "cleandb":
        users_collection.delete_many({})
        groups_collection.delete_many({})
        await _safe_edit(q.message, f"{pe('clean')} <b>{stylize_text('DATABASE WIPED')}!</b>")
  