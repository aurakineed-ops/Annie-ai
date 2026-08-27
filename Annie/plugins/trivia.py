# Copyright (c) 2025 Telegram:- @RAJOWNERX1
# Trivia - Random quiz questions with rewards

import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from Annie.utils import ensure_user_exists, format_money, stylize_text, pe, pe_safe, smart_reply, get_mention
from Annie.database import users_collection

# Cooldown tracking: {user_id: last_trivia_timestamp}
trivia_cooldowns = {}

# Active trivia: {user_id: {"answer": idx, "time": timestamp, "message_id": msg_id}}
active_trivia = {}

TRIVIA_REWARD = 500
COOLDOWN_SECONDS = 300  # 5 minutes
TIMEOUT_SECONDS = 30

TRIVIA_QUESTIONS = [
    {"q": "What is the capital of Japan?", "options": ["Seoul", "Tokyo", "Beijing", "Bangkok"], "answer": 1},
    {"q": "Which anime has the most episodes?", "options": ["Naruto", "One Piece", "Sazae-san", "Dragon Ball"], "answer": 2},
    {"q": "What does CPU stand for?", "options": ["Central Process Unit", "Central Processing Unit", "Computer Personal Unit", "Central Program Utility"], "answer": 1},
    {"q": "Who created Minecraft?", "options": ["Notch", "Herobrine", "Jeb", "Dinnerbone"], "answer": 0},
    {"q": "What is the largest planet in our solar system?", "options": ["Saturn", "Neptune", "Jupiter", "Uranus"], "answer": 2},
    {"q": "In Naruto, what is the Nine-Tails fox name?", "options": ["Shukaku", "Kurama", "Matatabi", "Saiken"], "answer": 1},
    {"q": "What programming language is known as the language of the web?", "options": ["Python", "Java", "JavaScript", "C++"], "answer": 2},
    {"q": "Which element has the symbol Au?", "options": ["Silver", "Gold", "Aluminum", "Argon"], "answer": 1},
    {"q": "How many players are on a standard football team?", "options": ["9", "10", "11", "12"], "answer": 2},
    {"q": "What is the name of Goku's first son?", "options": ["Goten", "Gohan", "Vegeta Jr", "Trunks"], "answer": 1},
    {"q": "Which country invented pizza?", "options": ["France", "USA", "Italy", "Spain"], "answer": 2},
    {"q": "What year did Bitcoin launch?", "options": ["2007", "2008", "2009", "2010"], "answer": 2},
    {"q": "In Dragon Ball Z, who killed Frieza?", "options": ["Goku", "Trunks", "Vegeta", "Gohan"], "answer": 1},
    {"q": "What is the square root of 144?", "options": ["10", "11", "12", "14"], "answer": 2},
    {"q": "Which ocean is the largest?", "options": ["Atlantic", "Indian", "Arctic", "Pacific"], "answer": 3},
    {"q": "Who is the main character in Death Note?", "options": ["L", "Light Yagami", "Misa", "Ryuk"], "answer": 1},
    {"q": "What is the hardest natural substance?", "options": ["Gold", "Iron", "Diamond", "Platinum"], "answer": 2},
    {"q": "How many bones are in the human body?", "options": ["186", "206", "216", "256"], "answer": 1},
    {"q": "In which anime does Levi Ackerman appear?", "options": ["Tokyo Ghoul", "Attack on Titan", "Demon Slayer", "Jujutsu Kaisen"], "answer": 1},
    {"q": "What is 15% of 200?", "options": ["20", "25", "30", "35"], "answer": 2},
    {"q": "Which game features a battle royale on an island?", "options": ["Minecraft", "Fortnite", "Terraria", "Roblox"], "answer": 1},
    {"q": "What is the chemical formula for water?", "options": ["CO2", "H2O", "NaCl", "O2"], "answer": 1},
    {"q": "Who painted the Mona Lisa?", "options": ["Picasso", "Da Vinci", "Van Gogh", "Michelangelo"], "answer": 1},
    {"q": "What is Luffy's devil fruit?", "options": ["Mera Mera", "Gomu Gomu", "Bara Bara", "Suna Suna"], "answer": 1},
    {"q": "Which planet is known as the Red Planet?", "options": ["Venus", "Mars", "Jupiter", "Mercury"], "answer": 1},
    {"q": "In Telegram, what does a blue tick mean?", "options": ["Sent", "Delivered", "Read", "Typing"], "answer": 2},
    {"q": "What is the fastest land animal?", "options": ["Lion", "Cheetah", "Horse", "Leopard"], "answer": 1},
    {"q": "Which Hashira uses Flame Breathing in Demon Slayer?", "options": ["Giyu", "Rengoku", "Muichiro", "Tengen"], "answer": 1},
    {"q": "What does RAM stand for?", "options": ["Random Access Memory", "Read All Memory", "Run Active Module", "Random Active Memory"], "answer": 0},
    {"q": "How many continents are there?", "options": ["5", "6", "7", "8"], "answer": 2},
    {"q": "What is the currency of Japan?", "options": ["Yuan", "Won", "Yen", "Ringgit"], "answer": 2},
    {"q": "Who is known as the God of Thunder in Marvel?", "options": ["Iron Man", "Thor", "Hulk", "Loki"], "answer": 1},
    {"q": "Which vitamin does sunlight provide?", "options": ["Vitamin A", "Vitamin B", "Vitamin C", "Vitamin D"], "answer": 3},
    {"q": "In GTA V, what city is the game set in?", "options": ["Liberty City", "Vice City", "Los Santos", "San Fierro"], "answer": 2},
    {"q": "What is the boiling point of water in Celsius?", "options": ["90", "95", "100", "110"], "answer": 2},
]


async def trivia_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user_exists(update.effective_user)
    user_id = update.effective_user.id

    # Check cooldown
    now = time.time()
    last_used = trivia_cooldowns.get(user_id, 0)
    remaining = COOLDOWN_SECONDS - (now - last_used)

    if remaining > 0:
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        return await smart_reply(update, f"{pe('timer')} {stylize_text('Trivia cooldown!')} {stylize_text('Wait')} <code>{mins}m {secs}s</code>")

    # Check if already has active trivia
    if user_id in active_trivia:
        return await smart_reply(update, f"{pe('warn')} {stylize_text('You already have an active trivia! Answer it first.')}")

    # Pick random question
    question = random.choice(TRIVIA_QUESTIONS)
    correct_idx = question["answer"]

    # Build keyboard
    buttons = []
    for i, option in enumerate(question["options"]):
        buttons.append([InlineKeyboardButton(option, callback_data=f"trv_{user_id}_{i}")])

    keyboard = InlineKeyboardMarkup(buttons)

    text = (
        f"{pe('question')} <b>{stylize_text('TRIVIA TIME')}</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"{pe('user')} <b>{stylize_text('Player')}:</b> {get_mention(update.effective_user)}\n"
        f"{pe('coin_up')} <b>{stylize_text('Reward')}:</b> <code>{format_money(TRIVIA_REWARD)}</code>\n\n"
        f"{pe('book')} <b>{stylize_text(question['q'])}</b>\n\n"
        f"{pe('timer')} {stylize_text('You have 30 seconds!')}"
    )

    msg = await smart_reply(update, text, reply_markup=keyboard)

    # Store active trivia
    active_trivia[user_id] = {
        "answer": correct_idx,
        "time": now,
        "question": question["q"]
    }

    # Set cooldown
    trivia_cooldowns[user_id] = now


async def trivia_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_")

    if len(parts) != 3:
        return

    try:
        target_user_id = int(parts[1])
        chosen_idx = int(parts[2])
    except ValueError:
        return

    # Only the player who started can answer
    if query.from_user.id != target_user_id:
        await query.answer("This is not your trivia!", show_alert=True)
        return

    # Check active trivia
    if target_user_id not in active_trivia:
        await query.answer("This trivia has expired!", show_alert=True)
        return

    trivia_data = active_trivia[target_user_id]
    correct_idx = trivia_data["answer"]
    elapsed = time.time() - trivia_data["time"]

    # Remove from active
    del active_trivia[target_user_id]

    # Check timeout
    if elapsed > TIMEOUT_SECONDS:
        text = (
            f"⏳ <b>{stylize_text('TIME UP!')}</b>\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"💀 {stylize_text('You took too long!')}\n"
            f"📖 <b>{stylize_text('Answer was option')}:</b> <code>{correct_idx + 1}</code>"
        )
        try:
            await query.edit_message_text(text=text, parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    if chosen_idx == correct_idx:
        # CORRECT
        users_collection.update_one({"user_id": target_user_id}, {"$inc": {"balance": TRIVIA_REWARD}})
        text = (
            f"🎉 <b>{stylize_text('CORRECT!')}</b>\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"✅ <b>{stylize_text('Well done')}!</b> {get_mention(query.from_user)}\n"
            f"💰 <b>{stylize_text('Reward')}:</b> <code>{format_money(TRIVIA_REWARD)}</code>\n"
            f"⚡ <b>{stylize_text('Time')}:</b> <code>{elapsed:.1f}s</code>"
        )
    else:
        # WRONG
        text = (
            f"❌ <b>{stylize_text('WRONG!')}</b>\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"💀 {stylize_text('Better luck next time!')}\n"
            f"📖 <b>{stylize_text('Correct answer was option')}:</b> <code>{correct_idx + 1}</code>"
        )

    try:
        await query.edit_message_text(text=text, parse_mode=ParseMode.HTML)
    except Exception:
        pass
