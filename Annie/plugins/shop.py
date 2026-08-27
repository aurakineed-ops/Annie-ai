from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from Annie.utils import ensure_user_exists, format_money, get_mention, pe, pe_safe, stylize_text, smart_reply
from Annie.database import users_collection
from Annie.config import SHOP_ITEMS

ITEMS_PER_PAGE = 6

# --- HELPERS ---

def get_rarity(price):
    if price < 5000: return f"{pe('star')} {stylize_text('Common')}"
    if price < 20000: return f"{pe('check')} {stylize_text('Uncommon')}"
    if price < 100000: return f"{pe('diamond')} {stylize_text('Rare')}"
    if price < 1000000: return f"{pe('fire')} {stylize_text('Epic')}"
    if price < 10000000: return f"{pe('crown')} {stylize_text('Legendary')}"
    return f"{pe('fire')} {stylize_text('GODLY')}"

def get_description(item):
    """Generates a cool description based on item type."""
    if item['id'] == "deathnote": return stylize_text("Writes names. Deletes people. 60% Kill Buff.")
    if item['id'] == "plot": return stylize_text("Literal Plot Armor. You cannot die. 60% Block.")
    
    if item['type'] == 'weapon':
        return stylize_text(f"A deadly weapon. Increases your kill rewards by +{int(item['buff']*100)}%.")
    elif item['type'] == 'armor':
        return stylize_text(f"Protective gear. Gives a {int(item['buff']*100)}% chance to block any robbery attempt.")
    elif item['type'] == 'flex':
        return stylize_text("A useless item for rich people. Shows off your massive wealth.")
    return stylize_text("Unknown Item.")

# --- KEYBOARD BUILDERS ---

def get_main_menu_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚔️ 𝐖𝐞𝐚𝐩𝐨𝐧𝐬", callback_data="shop_cat|weapon"),
            InlineKeyboardButton("🛡️ 𝐀𝐫𝐦𝐨𝐫", callback_data="shop_cat|armor")
        ],
        [
            InlineKeyboardButton("💎 𝐅𝐥𝐞𝐱 & 𝐕𝐈𝐏", callback_data="shop_cat|flex")
        ],
        [InlineKeyboardButton("🔙 𝐂𝐥𝐨𝐬𝐞", callback_data="shop_close")]
    ])

def get_category_kb(category_type, page=0):
    items = [i for i in SHOP_ITEMS if i['type'] == category_type]
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_items = items[start_idx:end_idx]
    
    keyboard = []
    row = []
    for item in current_items:
        price_k = f"{item['price']//1000}k" if item['price'] >= 1000 else item['price']
        text = f"{item['name']} [{price_k}]"
        callback = f"shop_view|{item['id']}|{category_type}|{page}"
        row.append(InlineKeyboardButton(text, callback_data=callback))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️", callback_data=f"shop_cat|{category_type}|{page-1}"))
    nav.append(InlineKeyboardButton("🔙 𝐌𝐞𝐧𝐮", callback_data="shop_home"))
    if end_idx < len(items): nav.append(InlineKeyboardButton("➡️", callback_data=f"shop_cat|{category_type}|{page+1}"))
    
    keyboard.append(nav)
    return InlineKeyboardMarkup(keyboard)

def get_item_kb(item_id, category, page, can_afford, is_owned):
    kb = []
    if is_owned:
        kb.append([InlineKeyboardButton("✅ 𝐎𝐰𝐧𝐞𝐝", callback_data="shop_owned")])
    elif can_afford:
        kb.append([InlineKeyboardButton("💳 𝐁𝐮𝐲 𝐍𝐨𝐰", callback_data=f"shop_buy|{item_id}|{category}|{page}")])
    else:
        kb.append([InlineKeyboardButton("❌ 𝐂𝐚𝐧'𝐭 𝐀𝐟𝐟𝐨𝐫𝐝", callback_data="shop_poor")])
        
    kb.append([InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤", callback_data=f"shop_cat|{category}|{page}")])
    return InlineKeyboardMarkup(kb)

# --- MENUS ---

async def shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = ensure_user_exists(update.effective_user)
        bal = format_money(user['balance'])
        
        text = (
            f"{pe('cherry')} <b>𝐁𝐚𝐤𝐚 𝐌𝐚𝐫𝐤𝐞𝐭𝐩𝐥𝐚𝐜𝐞</b>\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"{pe('user')} <b>{stylize_text('Customer')}:</b> {get_mention(user)}\n"
            f"{pe('money')} <b>{stylize_text('Wallet')}:</b> <code>{bal}</code>\n\n"
            f"<i>{stylize_text('Select a category to browse!')}</i>"
        )
        
        kb = get_main_menu_kb()
        
        if update.callback_query:
            await _safe_edit(update.callback_query, text, reply_markup=kb)
        else:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
            
    except Exception as e:
        print(f"Shop Error: {e}")
        # Fallback in case of error
        if update.callback_query:
            await update.callback_query.answer(f"{pe_safe('cross')} {stylize_text('Shop Error')}", show_alert=True)
        else:
            await smart_reply(update, f"{pe('cross')} <b>{stylize_text('Shop Error')}:</b> {stylize_text('Please check logs.')}")

# --- CALLBACK HANDLER ---

import re as _re

async def _safe_edit(query, text, reply_markup=None):
    """Edit message with fallback if Document_invalid."""
    try:
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    except Exception as e:
        if "Document_invalid" in str(e):
            clean = _re.sub(r'<tg-emoji emoji-id="[^"]*">([^<]*)</tg-emoji>', r'\1', text)
            await query.message.edit_text(clean, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        else:
            raise

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = ensure_user_exists(query.from_user)
    data = query.data.split("|")
    action = data[0]
    
    if action == "shop_close":
        await query.message.delete()
        return

    if action == "shop_home":
        await shop_menu(update, context)
        return
    
    # --- CATEGORY VIEW ---
    if action == "shop_cat":
        cat_type = data[1]
        page = int(data[2]) if len(data) > 2 else 0
        
        titles = {
            "weapon": f"{pe('sword')} <b>𝐖𝐞𝐚𝐩𝐨𝐧𝐬 𝐀𝐫𝐦𝐨𝐫𝐲</b>\n<i>{stylize_text('Lethal gear for killers.')}</i>",
            "armor": f"{pe('shield')} <b>𝐃𝐞𝐟𝐞𝐧𝐬𝐞 𝐒𝐲𝐬𝐭𝐞𝐦𝐬</b>\n<i>{stylize_text('Protection against thieves.')}</i>",
            "flex": f"{pe('diamond')} <b>𝐕𝐈𝐏 𝐅𝐥𝐞𝐱 𝐙𝐨𝐧𝐞</b>\n<i>{stylize_text('Pure status symbols.')}</i>"
        }
        
        text = f"{titles.get(cat_type, 'Shop')}\n\n{pe('money')} <b>{stylize_text('Balance')}:</b> <code>{format_money(user['balance'])}</code>"
        
        await _safe_edit(query, text, reply_markup=get_category_kb(cat_type, page))
        return

    # --- ITEM INSPECTOR ---
    if action == "shop_view":
        item_id, cat, page = data[1], data[2], data[3]
        item = next((i for i in SHOP_ITEMS if i['id'] == item_id), None)
        if not item: return await query.answer(f"{pe_safe('cross')} {stylize_text('Item removed.')}", show_alert=True)
        
        # Stats Display
        rarity = get_rarity(item['price'])
        desc = get_description(item)
        
        stats = ""
        life = f"{pe('star')} {stylize_text('Permanent')}" if item['type'] == 'flex' else f"{pe('timer')} {stylize_text('24 Hours')}"
        
        if item['type'] == 'weapon':
            stats = f"{pe('sword')} <b>{stylize_text('Buff')}:</b> +{int(item['buff']*100)}% {stylize_text('Kill Loot')}"
        elif item['type'] == 'armor':
            stats = f"{pe('shield')} <b>{stylize_text('Defense')}:</b> {int(item['buff']*100)}% {stylize_text('Block Chance')}"
        
        is_owned = any(i['id'] == item_id for i in user.get('inventory', []))
        can_afford = user['balance'] >= item['price']
        
        text = (
            f"{pe('cherry')} <b>{item['name']}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{pe('book')} <i>{desc}</i>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{pe('money')} <b>{stylize_text('Price')}:</b> <code>{format_money(item['price'])}</code>\n"
            f"{pe('star')} <b>{stylize_text('Rarity')}:</b> {rarity}\n"
            f"{stats}\n"
            f"{pe('timer')} <b>{stylize_text('Life')}:</b> {life}\n\n"
            f"{pe('money')} <b>{stylize_text('Your Wallet')}:</b> <code>{format_money(user['balance'])}</code>"
        )
        
        await _safe_edit(query, text, reply_markup=get_item_kb(item_id, cat, page, can_afford, is_owned))
        return

    # --- BUY ACTION ---
    if action == "shop_buy":
        item_id = data[1]
        item = next((i for i in SHOP_ITEMS if i['id'] == item_id), None)
        
        if not item: return await query.answer(f"{pe_safe('cross')} Error", show_alert=True)
        
        # Re-fetch user to be safe
        user = ensure_user_exists(query.from_user)

        if user['balance'] < item['price']:
            need_msg = f"You need {format_money(item['price'])}!"
            return await query.answer(f"{pe_safe('cross')} {stylize_text(need_msg)}", show_alert=True)
            
        # FAIR PLAY: Unique Items
        if any(i['id'] == item_id for i in user.get('inventory', [])):
            return await query.answer(f"{pe_safe('warn')} {stylize_text('You already own this item!')}", show_alert=True)
            
        # Add Timestamp for 24h expiry
        from datetime import datetime
        item_with_time = item.copy()
        item_with_time['bought_at'] = datetime.utcnow()

        users_collection.update_one(
            {"user_id": user['user_id']},
            {
                "$inc": {"balance": -item['price']},
                "$push": {"inventory": item_with_time}
            }
        )
        
        bought_msg = f"Bought {item['name']}!"
        await query.answer(f"{pe_safe('party')} {stylize_text(bought_msg)}", show_alert=True)
        
        # Refresh View to show "Owned"
        await shop_callback(update, context)

    # --- ALERTS ---
    if action == "shop_poor":
        await query.answer(f"{pe_safe('down')} {stylize_text('You are too poor for this!')}", show_alert=True)
    
    if action == "shop_owned":
        await query.answer(f"{pe_safe('cart')} {stylize_text('You already have this in your inventory!')}", show_alert=True)

# --- SHORTCUT (/buy) ---
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user_exists(update.effective_user)
    
    if not context.args: 
        return await smart_reply(update, f"{pe('warn')} <b>{stylize_text('Usage')}:</b> <code>/buy knife</code>")
    
    item_key = context.args[0].lower()
    item = next((i for i in SHOP_ITEMS if i['id'] == item_key), None)
    
    if not item: 
        return await smart_reply(update, f"{pe('cross')} {stylize_text('Item')} <b>{item_key}</b> {stylize_text('not found in shop.')}")
    
    if user['balance'] < item['price']: 
        return await smart_reply(update, f"{pe('cross')} {stylize_text('You need')} <code>{format_money(item['price'])}</code>!")
    
    if any(i['id'] == item_key for i in user.get('inventory', [])): 
        return await smart_reply(update, f"{pe('warn')} {stylize_text('You already own this item!')}")

    from datetime import datetime
    item_with_time = item.copy()
    item_with_time['bought_at'] = datetime.utcnow()

    users_collection.update_one(
        {"user_id": user['user_id']}, 
        {"$inc": {"balance": -item['price']}, "$push": {"inventory": item_with_time}}
    )
    await smart_reply(update, f"{pe('check')} {stylize_text('Bought')} <b>{item['name']}</b>!")