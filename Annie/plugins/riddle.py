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

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatType
from Annie.plugins.chatbot import ask_mistral_raw
from Annie.database import riddles_collection, users_collection
from Annie.utils import format_money, ensure_user_exists, get_mention, pe, stylize_text, smart_reply
from Annie.config import RIDDLE_REWARD

async def riddle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts a new AI riddle."""
    chat = update.effective_chat
    if chat.type == ChatType.PRIVATE: return await smart_reply(update, f"{pe('cross')} {stylize_text('Group Only!')}")

    # Check active riddle
    if riddles_collection.find_one({"chat_id": chat.id}):
        return await smart_reply(update, f"{pe('warn')} {stylize_text('A riddle is already active! Guess it.')}")

    msg = await smart_reply(update, f"{pe('star')} <b>{stylize_text('Generating AI Riddle...')}</b>")

    # Generate
    prompt = "Generate a short, hard riddle. Format: 'Riddle: [Question] | Answer: [OneWordAnswer]'. Do not add anything else."
    response = await ask_mistral_raw(system_prompt="You are a Riddle Master.", user_input=prompt)
    
    if not response or "|" not in response:
        return await msg.edit_text(f"{pe('warn')} {stylize_text('AI Brain Freeze. Try again.')}", parse_mode=ParseMode.HTML)

    try:
        parts = response.split("|")
        question = parts[0].replace("Riddle:", "").strip()
        answer = parts[1].replace("Answer:", "").strip().lower()
    except:
        return await msg.edit_text(f"{pe('warn')} {stylize_text('AI Error.')}", parse_mode=ParseMode.HTML)

    # Save
    riddles_collection.insert_one({"chat_id": chat.id, "answer": answer})

    await msg.edit_text(
        f"{pe('cherry')} <b>𝐀𝐈 𝐑𝐢𝐝𝐝𝐥𝐞 𝐂𝐡𝐚𝐥𝐥𝐞𝐧𝐠𝐞!</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"<i>{question}</i>\n\n"
        f"{pe('gift')} <b>ʀᴇᴡᴀʀᴅ:</b> <code>{format_money(RIDDLE_REWARD)}</code>\n"
        f"{pe('down')} <i>ʀᴇᴘʟʏ ᴡɪᴛʜ ʏᴏᴜʀ ᴀɴꜱᴡᴇʀ!</i>",
        parse_mode=ParseMode.HTML
    )

async def check_riddle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks user messages for the answer."""
    if not update.message or not update.message.text: return
    chat = update.effective_chat
    text = update.message.text.strip().lower()

    riddle = riddles_collection.find_one({"chat_id": chat.id})
    if not riddle: return

    if text == riddle['answer']:
        user = update.effective_user
        ensure_user_exists(user)
        
        # Winner
        users_collection.update_one({"user_id": user.id}, {"$inc": {"balance": RIDDLE_REWARD}})
        riddles_collection.delete_one({"chat_id": chat.id})
        
        await update.message.reply_text(
            f"{pe('cherry')} <b>𝐂𝐨𝐫𝐫𝐞𝐜𝐭!</b>\n\n"
            f"{pe('heart')} <b>ᴡɪɴɴᴇʀ:</b> {get_mention(user)}\n"
            f"{pe('money')} <b>ᴡᴏɴ:</b> <code>{format_money(RIDDLE_REWARD)}</code>\n"
            f"{pe('lock')} <b>ᴀɴꜱᴡᴇʀ:</b> <i>{riddle['answer'].title()}</i>",
            parse_mode=ParseMode.HTML
        )