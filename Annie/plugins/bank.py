# Copyright (c) 2025 Telegram:- @RAJOWNERX1
# Bank System - Safe storage for coins

from telegram import Update
from telegram.ext import ContextTypes
from Annie.utils import ensure_user_exists, format_money, stylize_text, pe, smart_reply, get_mention
from Annie.database import users_collection


def parse_bank_amount(amount_str: str):
    normalized = amount_str.replace(",", "").replace("_", "").lower()

    if normalized in {"all", "allbalance", "all-balance", "all_balance"}:
        return "all"

    try:
        return int(normalized)
    except ValueError:
        return None


async def bank_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user_exists(update.effective_user)
    args = context.args

    if not args:
        return await show_bank_balance(update, user)

    action = args[0].lower()

    if action in {"balance", "bal", "b"}:
        return await show_bank_balance(update, user)
    elif action in {"deposit", "dep", "d"}:
        return await bank_deposit(update, user, args)
    elif action in {"withdraw", "with", "wd", "w"}:
        return await bank_withdraw(update, user, args)
    else:
        text = (
            f"{pe('crown')} <b>{stylize_text('BANK COMMANDS')}</b> {pe('diamond')}\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"{pe('check')} <code>/bank</code> — {stylize_text('Check balance')}\n"
            f"{pe('coin_up')} <code>/bank deposit 500</code> / <code>/bank dep 500</code> — {stylize_text('Deposit coins')}\n"
            f"{pe('coin_up')} <code>/bank deposit all</code> — {stylize_text('Deposit all wallet balance')}\n"
            f"{pe('cash')} <code>/bank withdraw 500</code> / <code>/bank with 500</code> — {stylize_text('Withdraw coins')}\n"
            f"{pe('cash')} <code>/bank withdraw all</code> — {stylize_text('Withdraw all bank balance')}\n"
        )
        return await smart_reply(update, text)


async def show_bank_balance(update: Update, user):
    bank_bal = user.get("bank_balance", 0)
    wallet_bal = user.get("balance", 0)
    daily_interest = int(bank_bal * 0.02)

    text = (
        f"{pe('crown')} <b>{stylize_text('BANK ACCOUNT')}</b> {pe('diamond')}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"{pe('user')} <b>{stylize_text('Owner')}:</b> {get_mention(update.effective_user)}\n\n"
        f"{pe('wallet')} <b>{stylize_text('Wallet')}:</b> <code>{format_money(wallet_bal)}</code>\n"
        f"{pe('shield')} <b>{stylize_text('Bank')}:</b> <code>{format_money(bank_bal)}</code>\n"
        f"{pe('coin_up')} <b>{stylize_text('Daily Interest')}:</b> <code>{format_money(daily_interest)}</code> (2%)\n\n"
        f"{pe('lock')} {stylize_text('Bank coins are safe from robbery!')}"
    )
    return await smart_reply(update, text)


async def bank_deposit(update: Update, user, args):
    if len(args) < 2:
        return await smart_reply(update, f"{pe('warn')} <b>{stylize_text('Usage')}:</b> <code>/bank deposit 500</code>")

    amount_str = args[1]
    wallet_bal = user.get("balance", 0)

    parsed_amount = parse_bank_amount(amount_str)
    if parsed_amount == "all":
        amount = wallet_bal
    elif isinstance(parsed_amount, int):
        amount = parsed_amount
    else:
        return await smart_reply(update, f"{pe('cross')} {stylize_text('Invalid amount! Use a number or all.')}")

    if amount <= 0:
        return await smart_reply(update, f"{pe('cross')} {stylize_text('Amount must be positive!')}")

    if wallet_bal < amount:
        return await smart_reply(update, f"{pe('cross')} {stylize_text('Not enough coins in wallet!')} {stylize_text('You have')} <code>{format_money(wallet_bal)}</code>")

    users_collection.update_one(
        {"user_id": user["user_id"]},
        {"$inc": {"balance": -amount, "bank_balance": amount}}
    )

    new_bank = user.get("bank_balance", 0) + amount
    text = (
        f"{pe('check')} <b>{stylize_text('DEPOSIT SUCCESS')}</b> {pe('diamond')}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"{pe('coin_up')} <b>{stylize_text('Deposited')}:</b> <code>{format_money(amount)}</code>\n"
        f"{pe('shield')} <b>{stylize_text('Bank Balance')}:</b> <code>{format_money(new_bank)}</code>\n"
        f"{pe('wallet')} <b>{stylize_text('Wallet Left')}:</b> <code>{format_money(wallet_bal - amount)}</code>"
    )
    return await smart_reply(update, text)


async def bank_withdraw(update: Update, user, args):
    if len(args) < 2:
        return await smart_reply(update, f"{pe('warn')} <b>{stylize_text('Usage')}:</b> <code>/bank withdraw 500</code>")

    amount_str = args[1]
    bank_bal = user.get("bank_balance", 0)

    parsed_amount = parse_bank_amount(amount_str)
    if parsed_amount == "all":
        amount = bank_bal
    elif isinstance(parsed_amount, int):
        amount = parsed_amount
    else:
        return await smart_reply(update, f"{pe('cross')} {stylize_text('Invalid amount! Use a number or all.')}")

    if amount <= 0:
        return await smart_reply(update, f"{pe('cross')} {stylize_text('Amount must be positive!')}")

    if bank_bal < amount:
        return await smart_reply(update, f"{pe('cross')} {stylize_text('Not enough coins in bank!')} {stylize_text('You have')} <code>{format_money(bank_bal)}</code>")

    users_collection.update_one(
        {"user_id": user["user_id"]},
        {"$inc": {"balance": amount, "bank_balance": -amount}}
    )

    new_wallet = user.get("balance", 0) + amount
    text = (
        f"{pe('check')} <b>{stylize_text('WITHDRAWAL SUCCESS')}</b> {pe('diamond')}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"{pe('cash')} <b>{stylize_text('Withdrawn')}:</b> <code>{format_money(amount)}</code>\n"
        f"{pe('wallet')} <b>{stylize_text('Wallet Balance')}:</b> <code>{format_money(new_wallet)}</code>\n"
        f"{pe('shield')} <b>{stylize_text('Bank Left')}:</b> <code>{format_money(bank_bal - amount)}</code>"
    )
    return await smart_reply(update, text)
