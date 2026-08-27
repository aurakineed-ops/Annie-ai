import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from Annie.utils import ensure_user_exists, get_mention, format_money, pe, stylize_text, smart_reply
from Annie.database import users_collection

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Real Telegram Dice."""
    user = ensure_user_exists(update.effective_user)
    chat_id = update.effective_chat.id
    
    if not context.args: 
        return await smart_reply(update, f"{pe('dice')} <b>{stylize_text('Usage')}:</b> <code>/dice [amount]</code>")
    
    try: bet = int(context.args[0])
    except: return await smart_reply(update, f"{pe('warn')} {stylize_text('Invalid Bet.')}")
    
    if bet < 50: return await smart_reply(update, f"{pe('warn')} {stylize_text('Min bet is $50.')}")
    if user['balance'] < bet: return await smart_reply(update, f"{pe('down')} {stylize_text('Not enough money.')}")
    
    # Send the native Dice
    msg = await context.bot.send_dice(chat_id, emoji='🎲')
    result = msg.dice.value # 1-6
    
    # Wait for animation
    await asyncio.sleep(3)
    
    if result > 3: # 4, 5, 6 Wins
        win_amt = bet 
        users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": win_amt}})
        await update.message.reply_text(
            f"{pe('dice')} <b>{stylize_text('Result')}:</b> {result}\n{pe('cherry')} <b>{stylize_text('You Won!')}</b> +<code>{format_money(win_amt)}</code>",
            reply_to_message_id=msg.message_id,
            parse_mode=ParseMode.HTML
        )
    else: # 1, 2, 3 Loses
        users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": -bet}})
        await update.message.reply_text(
            f"{pe('dice')} <b>{stylize_text('Result')}:</b> {result}\n{pe('skull')} <b>{stylize_text('You Lost!')}</b> -<code>{format_money(bet)}</code>",
            reply_to_message_id=msg.message_id,
            parse_mode=ParseMode.HTML
        )

async def slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Real Telegram Slots."""
    user = ensure_user_exists(update.effective_user)
    chat_id = update.effective_chat.id
    bet = 100 # Fixed bet
    
    if user['balance'] < bet: return await smart_reply(update, f"{pe('down')} {stylize_text('Need $100 to spin.')}")
    
    users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": -bet}})
    
    # Send native Slot Machine
    msg = await context.bot.send_dice(chat_id, emoji='🎰')
    value = msg.dice.value 
    # Values: 1-64. 
    # 64 = 777 (Jackpot), 1 = all different, 43 = grapes/grapes/grapes etc.
    # Telegram logic is complex, simpler approximation:
    
    await asyncio.sleep(2) # Wait for spin
    
    # Winning logic based on Telegram API values
    if value == 64: # 777
        prize = bet * 10
        users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": prize}})
        text = f"{pe('dice')} <b>{stylize_text('JACKPOT! (777)')}</b>\n{pe('cherry')} {stylize_text('You won')} <code>{format_money(prize)}</code>!"
    elif value in [1, 22, 43]: # 3 matching fruits usually
        prize = bet * 3
        users_collection.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": prize}})
        text = f"{pe('dice')} <b>{stylize_text('Winner!')}</b>\n{pe('money')} {stylize_text('You won')} <code>{format_money(prize)}</code>!"
    else:
        text = f"{pe('dice')} <b>{stylize_text('Lost!')}</b> {pe('skull')} {stylize_text('Better luck next time.')}"

    await smart_reply(update, text, reply_to_message_id=msg.message_id)