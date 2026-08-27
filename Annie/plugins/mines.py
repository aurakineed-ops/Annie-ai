# Copyright (c) 2025 Telegram:- @RAJOWNERX1
# Mines Game - 5x5 grid gambling game

import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from Annie.utils import ensure_user_exists, format_money, stylize_text, pe, pe_safe, smart_reply, get_mention
from Annie.database import users_collection

# Active games stored in memory: {user_id: game_data}
active_mines = {}

GRID_SIZE = 5
MINE_COUNT = 5
MIN_BET = 100

# Multipliers for each safe tile revealed
MULTIPLIERS = [1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 8.0]


def create_grid():
    """Create a 5x5 grid with 5 mines placed randomly."""
    grid = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
    mines_placed = 0
    while mines_placed < MINE_COUNT:
        r = random.randint(0, GRID_SIZE - 1)
        c = random.randint(0, GRID_SIZE - 1)
        if not grid[r][c]:
            grid[r][c] = True
            mines_placed += 1
    return grid


def build_keyboard(game_data):
    """Build the inline keyboard for the current game state."""
    revealed = game_data["revealed"]
    grid = game_data["grid"]
    keyboard = []

    for r in range(GRID_SIZE):
        row = []
        for c in range(GRID_SIZE):
            if revealed[r][c]:
                if grid[r][c]:
                    row.append(InlineKeyboardButton("💣", callback_data=f"mine_noop"))
                else:
                    row.append(InlineKeyboardButton("💎", callback_data=f"mine_noop"))
            else:
                row.append(InlineKeyboardButton("❓", callback_data=f"mine_{r}_{c}"))
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


def build_gameover_keyboard(game_data):
    """Reveal all tiles after game over."""
    grid = game_data["grid"]
    revealed = game_data["revealed"]
    keyboard = []

    for r in range(GRID_SIZE):
        row = []
        for c in range(GRID_SIZE):
            if grid[r][c]:
                row.append(InlineKeyboardButton("💣", callback_data="mine_noop"))
            elif revealed[r][c]:
                row.append(InlineKeyboardButton("💎", callback_data="mine_noop"))
            else:
                row.append(InlineKeyboardButton("◻️", callback_data="mine_noop"))
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


async def mines_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user_exists(update.effective_user)
    user_id = update.effective_user.id

    # Check if already in a game
    if user_id in active_mines:
        return await smart_reply(update, f"{pe('warn')} {stylize_text('You already have an active mines game!')} {stylize_text('Use')} /cashout {stylize_text('or finish it.')}")

    # Check bet amount
    if not context.args:
        return await smart_reply(update, f"{pe('dice')} <b>{stylize_text('MINES GAME')}</b>\n\n{pe('star')} {stylize_text('Usage')}: <code>/mines 500</code>\n{pe('coin_up')} {stylize_text('Minimum bet')}: <code>{format_money(MIN_BET)}</code>\n{pe('diamond')} {stylize_text('Pick safe tiles to multiply your bet!')}\n{pe('fire')} {stylize_text('Hit a mine and lose everything!')}")

    try:
        bet = int(context.args[0])
    except ValueError:
        return await smart_reply(update, f"{pe('cross')} {stylize_text('Invalid bet amount!')}")

    if bet < MIN_BET:
        return await smart_reply(update, f"{pe('cross')} {stylize_text('Minimum bet is')} <code>{format_money(MIN_BET)}</code>!")

    if user.get("balance", 0) < bet:
        return await smart_reply(update, f"{pe('cross')} {stylize_text('Not enough coins!')} {stylize_text('You have')} <code>{format_money(user.get('balance', 0))}</code>")

    # Deduct bet
    users_collection.update_one({"user_id": user_id}, {"$inc": {"balance": -bet}})

    # Create game
    grid = create_grid()
    game_data = {
        "grid": grid,
        "revealed": [[False] * GRID_SIZE for _ in range(GRID_SIZE)],
        "bet": bet,
        "tiles_revealed": 0,
        "current_multiplier": 1.0,
        "current_value": bet
    }
    active_mines[user_id] = game_data

    keyboard = build_keyboard(game_data)
    text = (
        f"{pe('dice')} <b>{stylize_text('MINES GAME')}</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"{pe('user')} <b>{stylize_text('Player')}:</b> {get_mention(update.effective_user)}\n"
        f"{pe('money')} <b>{stylize_text('Bet')}:</b> <code>{format_money(bet)}</code>\n"
        f"{pe('star')} <b>{stylize_text('Multiplier')}:</b> <code>1.0x</code>\n"
        f"{pe('diamond')} <b>{stylize_text('Value')}:</b> <code>{format_money(bet)}</code>\n\n"
        f"{pe('fire')} {stylize_text('Pick tiles! 5 mines hidden. Use')} /cashout {stylize_text('to collect.')}"
    )
    await smart_reply(update, text, reply_markup=keyboard)


async def mines_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "mine_noop":
        return

    # Parse position
    parts = data.split("_")
    if len(parts) != 3:
        return

    try:
        r, c = int(parts[1]), int(parts[2])
    except ValueError:
        return

    # Check active game
    if user_id not in active_mines:
        await query.answer("No active game!", show_alert=True)
        return

    game_data = active_mines[user_id]

    # Check if already revealed
    if game_data["revealed"][r][c]:
        return

    # Reveal tile
    game_data["revealed"][r][c] = True

    if game_data["grid"][r][c]:
        # HIT A MINE - Game Over
        del active_mines[user_id]
        keyboard = build_gameover_keyboard(game_data)
        bet = game_data["bet"]
        text = (
            f"💣 <b>{stylize_text('BOOM! GAME OVER')}</b>\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"💀 <b>{stylize_text('You hit a mine!')}</b>\n"
            f"💸 <b>{stylize_text('Lost')}:</b> <code>{format_money(bet)}</code>\n\n"
            f"🎲 {stylize_text('Better luck next time!')}"
        )
        try:
            await query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        except Exception:
            pass
    else:
        # SAFE TILE
        game_data["tiles_revealed"] += 1
        idx = min(game_data["tiles_revealed"] - 1, len(MULTIPLIERS) - 1)
        game_data["current_multiplier"] = MULTIPLIERS[idx]
        game_data["current_value"] = int(game_data["bet"] * game_data["current_multiplier"])

        keyboard = build_keyboard(game_data)
        mult = game_data["current_multiplier"]
        value = game_data["current_value"]
        bet = game_data["bet"]
        tiles = game_data["tiles_revealed"]

        text = (
            f"🎲 <b>{stylize_text('MINES GAME')}</b>\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"👤 <b>{stylize_text('Player')}:</b> {get_mention(query.from_user)}\n"
            f"💰 <b>{stylize_text('Bet')}:</b> <code>{format_money(bet)}</code>\n"
            f"✨ <b>{stylize_text('Multiplier')}:</b> <code>{mult}x</code>\n"
            f"💎 <b>{stylize_text('Value')}:</b> <code>{format_money(value)}</code>\n"
            f"🏆 <b>{stylize_text('Tiles')}:</b> <code>{tiles}/20</code>\n\n"
            f"💎 {stylize_text('Safe! Keep going or')} /cashout"
        )
        try:
            await query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        except Exception:
            pass

        # Auto-win if all safe tiles revealed
        if game_data["tiles_revealed"] >= (GRID_SIZE * GRID_SIZE - MINE_COUNT):
            del active_mines[user_id]
            winnings = game_data["current_value"]
            users_collection.update_one({"user_id": user_id}, {"$inc": {"balance": winnings}})
            keyboard = build_gameover_keyboard(game_data)
            text = (
                f"🏆 <b>{stylize_text('JACKPOT! ALL SAFE!')}</b>\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"🎉 <b>{stylize_text('You cleared the board!')}</b>\n"
                f"💰 <b>{stylize_text('Won')}:</b> <code>{format_money(winnings)}</code>\n"
                f"✨ <b>{stylize_text('Multiplier')}:</b> <code>{game_data['current_multiplier']}x</code>"
            )
            try:
                await query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            except Exception:
                pass


async def cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in active_mines:
        return await smart_reply(update, f"{pe('cross')} {stylize_text('You have no active mines game!')}")

    game_data = active_mines[user_id]

    if game_data["tiles_revealed"] == 0:
        return await smart_reply(update, f"{pe('warn')} {stylize_text('Reveal at least one tile before cashing out!')}")

    winnings = game_data["current_value"]
    bet = game_data["bet"]
    profit = winnings - bet
    mult = game_data["current_multiplier"]
    tiles = game_data["tiles_revealed"]

    del active_mines[user_id]

    # Add winnings
    users_collection.update_one({"user_id": user_id}, {"$inc": {"balance": winnings}})

    text = (
        f"{pe('check')} <b>{stylize_text('CASHED OUT')}</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"{pe('user')} <b>{stylize_text('Player')}:</b> {get_mention(update.effective_user)}\n"
        f"{pe('money')} <b>{stylize_text('Bet')}:</b> <code>{format_money(bet)}</code>\n"
        f"{pe('star')} <b>{stylize_text('Multiplier')}:</b> <code>{mult}x</code>\n"
        f"{pe('diamond')} <b>{stylize_text('Tiles Revealed')}:</b> <code>{tiles}</code>\n"
        f"{pe('coin_up')} <b>{stylize_text('Profit')}:</b> <code>{format_money(profit)}</code>\n"
        f"{pe('cash')} <b>{stylize_text('Total Received')}:</b> <code>{format_money(winnings)}</code>"
    )
    await smart_reply(update, text)
