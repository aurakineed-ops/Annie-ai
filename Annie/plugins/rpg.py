import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from Annie.utils import pe, stylize_text, smart_reply, ensure_user_exists, get_mention, format_money
from Annie.database import users_collection


# --- FISH CATCHES ---
FISH_CATCHES = {
    "common": [
        {"name": "Sardine", "min": 50, "max": 200},
        {"name": "Trout", "min": 50, "max": 200},
        {"name": "Bass", "min": 50, "max": 200},
        {"name": "Catfish", "min": 50, "max": 200},
    ],
    "rare": [
        {"name": "Swordfish", "min": 500, "max": 1000},
        {"name": "Tuna", "min": 500, "max": 1000},
        {"name": "Salmon", "min": 500, "max": 1000},
    ],
    "legendary": [
        {"name": "Golden Koi", "min": 2000, "max": 5000},
        {"name": "Dragon Fish", "min": 2000, "max": 5000},
        {"name": "Mystic Whale", "min": 2000, "max": 5000},
    ],
    "trash": [
        {"name": "Old Boot", "min": 10, "max": 10},
        {"name": "Rusty Can", "min": 10, "max": 10},
        {"name": "Seaweed", "min": 10, "max": 10},
    ],
}

# --- MINE ORES ---
MINE_ORES = [
    {"name": "Stone", "min": 30, "max": 30, "weight": 35},
    {"name": "Iron", "min": 100, "max": 100, "weight": 25},
    {"name": "Gold", "min": 500, "max": 500, "weight": 12},
    {"name": "Diamond", "min": 2000, "max": 2000, "weight": 5},
    {"name": "Emerald", "min": 5000, "max": 5000, "weight": 3},
    {"name": "Nothing", "min": 0, "max": 0, "weight": 20},
]

# --- WOOD TYPES ---
WOOD_TYPES = [
    {"name": "Oak", "min": 50, "max": 50, "weight": 40},
    {"name": "Birch", "min": 100, "max": 100, "weight": 30},
    {"name": "Mahogany", "min": 300, "max": 300, "weight": 18},
    {"name": "Magic Tree", "min": 1000, "max": 1000, "weight": 7},
    {"name": "Hidden Treasure", "min": 3000, "max": 3000, "weight": 5},
]


def get_remaining_time(last_time, cooldown_minutes):
    """Calculate remaining cooldown time."""
    if not last_time:
        return None
    now = datetime.utcnow()
    elapsed = now - last_time
    cooldown = timedelta(minutes=cooldown_minutes)
    if elapsed < cooldown:
        remaining = cooldown - elapsed
        total_seconds = int(remaining.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}m {seconds}s"
    return None


# --- /fish COMMAND ---
async def fish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_doc = ensure_user_exists(user)

    # Check cooldown (30 minutes)
    remaining = get_remaining_time(user_doc.get("last_fish"), 30)
    if remaining:
        msg = (
            f"{pe('diamond')} {get_mention(user)}, "
            f"{stylize_text('your fishing rod is still drying!')}\n"
            f"{pe('fire')} {stylize_text('Try again in')}: <code>{remaining}</code>"
        )
        return await smart_reply(update, msg)

    # Determine catch rarity
    roll = random.randint(1, 100)
    if roll <= 5:
        category = "legendary"
        rarity_text = stylize_text("LEGENDARY")
        emoji = pe("crown")
    elif roll <= 20:
        category = "rare"
        rarity_text = stylize_text("Rare")
        emoji = pe("star")
    elif roll <= 85:
        category = "common"
        rarity_text = stylize_text("Common")
        emoji = pe("diamond")
    else:
        category = "trash"
        rarity_text = stylize_text("Trash")
        emoji = pe("gift")

    catch = random.choice(FISH_CATCHES[category])
    reward = random.randint(catch["min"], catch["max"])

    # Update database
    users_collection.update_one(
        {"user_id": user.id},
        {
            "$set": {"last_fish": datetime.utcnow()},
            "$inc": {"balance": reward, "fish_count": 1}
        }
    )

    catch_name = stylize_text(catch["name"])
    msg = (
        f"{pe('diamond')} <b>{stylize_text('FISHING')}</b> {pe('diamond')}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{pe('cherry')} {get_mention(user)} {stylize_text('cast their rod')}...\n\n"
        f"{emoji} {stylize_text('Caught')}: <b>{catch_name}</b>\n"
        f"{pe('star')} {stylize_text('Rarity')}: <b>{rarity_text}</b>\n"
        f"{pe('money')} {stylize_text('Earned')}: <code>{format_money(reward)}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    await smart_reply(update, msg)


# --- /mine COMMAND ---
async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_doc = ensure_user_exists(user)

    # Check cooldown (45 minutes)
    remaining = get_remaining_time(user_doc.get("last_mine"), 45)
    if remaining:
        msg = (
            f"{pe('sword')} {get_mention(user)}, "
            f"{stylize_text('your pickaxe is still cooling down!')}\n"
            f"{pe('fire')} {stylize_text('Try again in')}: <code>{remaining}</code>"
        )
        return await smart_reply(update, msg)

    # Weighted random ore selection
    weights = [ore["weight"] for ore in MINE_ORES]
    ore = random.choices(MINE_ORES, weights=weights, k=1)[0]

    # Found nothing
    if ore["name"] == "Nothing":
        users_collection.update_one(
            {"user_id": user.id},
            {
                "$set": {"last_mine": datetime.utcnow()},
                "$inc": {"mine_count": 1}
            }
        )
        msg = (
            f"{pe('sword')} <b>{stylize_text('MINING')}</b> {pe('sword')}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"{pe('cherry')} {get_mention(user)} {stylize_text('swung their pickaxe')}...\n\n"
            f"{pe('gift')} {stylize_text('Found nothing but rocks and dust!')}\n"
            f"{pe('lightning')} {stylize_text('Better luck next time!')}\n\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        return await smart_reply(update, msg)

    reward = random.randint(ore["min"], ore["max"])

    # Determine emoji based on ore
    ore_emojis = {
        "Stone": pe("gift"),
        "Iron": pe("sword"),
        "Gold": pe("money"),
        "Diamond": pe("diamond"),
        "Emerald": pe("star"),
    }
    ore_emoji = ore_emojis.get(ore["name"], pe("gift"))

    # Update database
    users_collection.update_one(
        {"user_id": user.id},
        {
            "$set": {"last_mine": datetime.utcnow()},
            "$inc": {"balance": reward, "mine_count": 1}
        }
    )

    ore_name = stylize_text(ore["name"])
    msg = (
        f"{pe('sword')} <b>{stylize_text('MINING')}</b> {pe('sword')}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{pe('cherry')} {get_mention(user)} {stylize_text('swung their pickaxe')}...\n\n"
        f"{ore_emoji} {stylize_text('Found')}: <b>{ore_name}</b>\n"
        f"{pe('money')} {stylize_text('Earned')}: <code>{format_money(reward)}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    await smart_reply(update, msg)


# --- /chop COMMAND ---
async def chop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_doc = ensure_user_exists(user)

    # Check cooldown (20 minutes)
    remaining = get_remaining_time(user_doc.get("last_chop"), 20)
    if remaining:
        msg = (
            f"{pe('gift')} {get_mention(user)}, "
            f"{stylize_text('your axe is still being sharpened!')}\n"
            f"{pe('fire')} {stylize_text('Try again in')}: <code>{remaining}</code>"
        )
        return await smart_reply(update, msg)

    # Weighted random wood selection
    weights = [wood["weight"] for wood in WOOD_TYPES]
    wood = random.choices(WOOD_TYPES, weights=weights, k=1)[0]
    reward = random.randint(wood["min"], wood["max"])

    # Determine emoji based on wood type
    if wood["name"] == "Hidden Treasure":
        wood_emoji = pe("crown")
        action_text = stylize_text("discovered a hidden treasure chest!")
    elif wood["name"] == "Magic Tree":
        wood_emoji = pe("star")
        action_text = stylize_text("chopped a glowing Magic Tree!")
    else:
        wood_emoji = pe("gift")
        action_text = stylize_text("chopped some wood!")

    # Update database
    users_collection.update_one(
        {"user_id": user.id},
        {
            "$set": {"last_chop": datetime.utcnow()},
            "$inc": {"balance": reward, "chop_count": 1}
        }
    )

    wood_name = stylize_text(wood["name"])
    msg = (
        f"{pe('gift')} <b>{stylize_text('WOODCUTTING')}</b> {pe('gift')}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{pe('cherry')} {get_mention(user)} {action_text}\n\n"
        f"{wood_emoji} {stylize_text('Got')}: <b>{wood_name}</b>\n"
        f"{pe('money')} {stylize_text('Earned')}: <code>{format_money(reward)}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    await smart_reply(update, msg)


# --- /profile COMMAND ---
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_doc = ensure_user_exists(user)

    # Get target (reply or self)
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        user_doc = ensure_user_exists(target_user)
    elif context.args:
        target_name = context.args[0]
        if target_name.startswith("@"):
            clean = target_name.replace("@", "").lower()
            found = users_collection.find_one({"username": clean})
            if found:
                user_doc = found
            else:
                msg = (
                    f"{pe('cherry')} {stylize_text('User not found in database!')}"
                )
                return await smart_reply(update, msg)
        elif target_name.isdigit():
            found = users_collection.find_one({"user_id": int(target_name)})
            if found:
                user_doc = found
            else:
                msg = (
                    f"{pe('cherry')} {stylize_text('User not found in database!')}"
                )
                return await smart_reply(update, msg)

    # Gather stats
    balance = user_doc.get("balance", 0)
    kills = user_doc.get("kills", 0)
    fish_count = user_doc.get("fish_count", 0)
    mine_count = user_doc.get("mine_count", 0)
    chop_count = user_doc.get("chop_count", 0)
    status = user_doc.get("status", "alive")
    partner_id = user_doc.get("partner_id")
    name = user_doc.get("name", "Unknown")

    # Rank
    rank = users_collection.count_documents({"balance": {"$gt": balance}}) + 1

    # Status emoji
    if status == "alive":
        status_text = f"{pe('heart')} {stylize_text('Alive')}"
    else:
        status_text = f"{pe('fire')} {stylize_text('Dead')}"

    # Marriage status
    if partner_id:
        partner_doc = users_collection.find_one({"user_id": partner_id})
        if partner_doc:
            partner_name = partner_doc.get("name", "Unknown")
            marriage_text = f"{pe('heart')} {stylize_text('Married to')} <b>{partner_name}</b>"
        else:
            marriage_text = f"{pe('heart')} {stylize_text('Married')}"
    else:
        marriage_text = f"{pe('cherry')} {stylize_text('Single')}"

    # Badges
    badges = []
    if fish_count >= 50:
        badges.append(f"{pe('diamond')} {stylize_text('Fisherman')}")
    if mine_count >= 50:
        badges.append(f"{pe('sword')} {stylize_text('Miner')}")
    if chop_count >= 50:
        badges.append(f"{pe('gift')} {stylize_text('Lumberjack')}")
    if kills >= 10:
        badges.append(f"{pe('fire')} {stylize_text('Killer')}")
    if balance >= 100000:
        badges.append(f"{pe('money')} {stylize_text('Rich')}")
    if partner_id:
        badges.append(f"{pe('heart')} {stylize_text('Married')}")

    badges_text = "\n".join(badges) if badges else f"<i>{stylize_text('No badges yet...')}</i>"

    msg = (
        f"{pe('crown')} <b>{stylize_text('PLAYER PROFILE')}</b> {pe('crown')}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{pe('cherry')} <b>{stylize_text('Name')}:</b> {get_mention(user_doc)}\n"
        f"{pe('money')} <b>{stylize_text('Balance')}:</b> <code>{format_money(balance)}</code>\n"
        f"{pe('star')} <b>{stylize_text('Rank')}:</b> #{rank}\n"
        f"{pe('sword')} <b>{stylize_text('Kills')}:</b> {kills}\n"
        f"{pe('lightning')} <b>{stylize_text('Status')}:</b> {status_text}\n"
        f"{pe('heart')} <b>{stylize_text('Marriage')}:</b> {marriage_text}\n\n"
        f"{pe('diamond')} <b>{stylize_text('ACTIVITIES')}</b>\n"
        f"{pe('diamond')} {stylize_text('Fish Caught')}: <b>{fish_count}</b>\n"
        f"{pe('sword')} {stylize_text('Ores Mined')}: <b>{mine_count}</b>\n"
        f"{pe('gift')} {stylize_text('Trees Chopped')}: <b>{chop_count}</b>\n\n"
        f"{pe('fire')} <b>{stylize_text('BADGES')}</b>\n"
        f"{badges_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    await smart_reply(update, msg)


# --- BOSS NAMES ---
BOSS_NAMES = [
    "Shadow Dragon", "Ancient Golem", "Fire Demon", "Ice Titan",
    "Dark Overlord", "Blood Reaper", "Storm Giant", "Void Serpent",
    "Chaos Knight", "Thunder Behemoth", "Crystal Hydra", "Phantom Lord"
]


# --- /boss COMMAND ---
async def boss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_doc = ensure_user_exists(user)

    # Check cooldown (2 hours = 120 minutes)
    remaining = get_remaining_time(user_doc.get("last_boss"), 120)
    if remaining:
        msg = (
            f"{pe('fire')} {get_mention(user)}, "
            f"{stylize_text('the boss arena is still being repaired!')}\n"
            f"{pe('lightning')} {stylize_text('Try again in')}: <code>{remaining}</code>"
        )
        return await smart_reply(update, msg)

    # Check if dead
    if user_doc.get("status") == "dead":
        msg = (
            f"{pe('fire')} {get_mention(user)}, "
            f"{stylize_text('you are dead! Use /revive first!')}"
        )
        return await smart_reply(update, msg)

    # Boss stats
    boss_name = random.choice(BOSS_NAMES)
    boss_hp = random.randint(500, 2000)

    # Player damage based on kills
    kills = user_doc.get("kills", 0)
    base_damage = random.randint(200, 800)
    kill_bonus = kills * random.randint(5, 15)
    total_damage = base_damage + kill_bonus

    boss_name_styled = stylize_text(boss_name)

    if total_damage >= boss_hp:
        # Player wins
        reward = random.randint(5000, 20000)
        users_collection.update_one(
            {"user_id": user.id},
            {
                "$set": {"last_boss": datetime.utcnow()},
                "$inc": {"balance": reward, "boss_wins": 1}
            }
        )
        msg = (
            f"{pe('crown')} <b>{stylize_text('BOSS FIGHT')}</b> {pe('crown')}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"{pe('fire')} {stylize_text('A wild')} <b>{boss_name_styled}</b> {stylize_text('appeared!')}\n"
            f"{pe('sword')} {stylize_text('Boss HP')}: <code>{boss_hp}</code>\n\n"
            f"{pe('lightning')} {get_mention(user)} {stylize_text('charged with full force!')}\n"
            f"{pe('star')} {stylize_text('Damage Dealt')}: <code>{total_damage}</code>\n\n"
            f"{pe('crown')} <b>{stylize_text('VICTORY!')}</b>\n"
            f"{pe('money')} {stylize_text('Reward')}: <code>{format_money(reward)}</code>\n"
            f"{pe('diamond')} {stylize_text('The beast has fallen!')}\n\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
    else:
        # Boss wins - player takes damage
        loss = random.randint(500, 2000)
        current_bal = user_doc.get("balance", 0)
        actual_loss = min(loss, current_bal)
        users_collection.update_one(
            {"user_id": user.id},
            {
                "$set": {"last_boss": datetime.utcnow()},
                "$inc": {"balance": -actual_loss}
            }
        )
        boss_damage = random.randint(300, 900)
        msg = (
            f"{pe('crown')} <b>{stylize_text('BOSS FIGHT')}</b> {pe('crown')}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"{pe('fire')} {stylize_text('A wild')} <b>{boss_name_styled}</b> {stylize_text('appeared!')}\n"
            f"{pe('sword')} {stylize_text('Boss HP')}: <code>{boss_hp}</code>\n\n"
            f"{pe('lightning')} {get_mention(user)} {stylize_text('attacked bravely!')}\n"
            f"{pe('star')} {stylize_text('Damage Dealt')}: <code>{total_damage}</code>\n\n"
            f"{pe('fire')} <b>{stylize_text('DEFEATED!')}</b>\n"
            f"{pe('sword')} {stylize_text('Boss hit back for')}: <code>{boss_damage}</code> {stylize_text('damage')}\n"
            f"{pe('money')} {stylize_text('Lost')}: <code>{format_money(actual_loss)}</code>\n"
            f"{pe('cherry')} {stylize_text('Better luck next time warrior!')}\n\n"
            f"━━━━━━━━━━━━━━━━━━"
        )

    await smart_reply(update, msg)


# --- ADVENTURE EVENTS ---
ADVENTURE_EVENTS = [
    "treasure",
    "monster",
    "potion",
    "nothing",
    "trader",
    "treasure",
    "monster",
    "nothing",
    "trader",
    "nothing",
]


# --- /adventure COMMAND ---
async def adventure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_doc = ensure_user_exists(user)

    # Check cooldown (1 hour = 60 minutes)
    remaining = get_remaining_time(user_doc.get("last_adventure"), 60)
    if remaining:
        msg = (
            f"{pe('star')} {get_mention(user)}, "
            f"{stylize_text('you are still resting from your last adventure!')}\n"
            f"{pe('fire')} {stylize_text('Try again in')}: <code>{remaining}</code>"
        )
        return await smart_reply(update, msg)

    event = random.choice(ADVENTURE_EVENTS)

    if event == "treasure":
        reward = random.randint(1000, 5000)
        users_collection.update_one(
            {"user_id": user.id},
            {
                "$set": {"last_adventure": datetime.utcnow()},
                "$inc": {"balance": reward, "adventure_count": 1}
            }
        )
        msg = (
            f"{pe('star')} <b>{stylize_text('ADVENTURE')}</b> {pe('star')}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"{pe('cherry')} {get_mention(user)} {stylize_text('ventured into the unknown')}...\n\n"
            f"{pe('crown')} {stylize_text('You found a hidden treasure chest!')}\n"
            f"{pe('diamond')} {stylize_text('Ancient gold coins spill out!')}\n"
            f"{pe('money')} {stylize_text('Earned')}: <code>{format_money(reward)}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━━"
        )

    elif event == "monster":
        loss = random.randint(200, 500)
        current_bal = user_doc.get("balance", 0)
        actual_loss = min(loss, current_bal)
        users_collection.update_one(
            {"user_id": user.id},
            {
                "$set": {"last_adventure": datetime.utcnow()},
                "$inc": {"balance": -actual_loss, "adventure_count": 1}
            }
        )
        msg = (
            f"{pe('star')} <b>{stylize_text('ADVENTURE')}</b> {pe('star')}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"{pe('cherry')} {get_mention(user)} {stylize_text('ventured into the unknown')}...\n\n"
            f"{pe('fire')} {stylize_text('A wild monster ambushed you!')}\n"
            f"{pe('sword')} {stylize_text('It slashed at your coin pouch!')}\n"
            f"{pe('money')} {stylize_text('Lost')}: <code>{format_money(actual_loss)}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━━"
        )

    elif event == "potion":
        # If dead, revive; if alive, bonus coins
        if user_doc.get("status") == "dead":
            users_collection.update_one(
                {"user_id": user.id},
                {
                    "$set": {"last_adventure": datetime.utcnow(), "status": "alive"},
                    "$inc": {"adventure_count": 1}
                }
            )
            msg = (
                f"{pe('star')} <b>{stylize_text('ADVENTURE')}</b> {pe('star')}\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"{pe('cherry')} {get_mention(user)} {stylize_text('ventured into the unknown')}...\n\n"
                f"{pe('heart')} {stylize_text('You found a revival potion!')}\n"
                f"{pe('lightning')} {stylize_text('The magic flows through your veins!')}\n"
                f"{pe('crown')} {stylize_text('You have been REVIVED!')}\n\n"
                f"━━━━━━━━━━━━━━━━━━"
            )
        else:
            bonus = random.randint(300, 800)
            users_collection.update_one(
                {"user_id": user.id},
                {
                    "$set": {"last_adventure": datetime.utcnow()},
                    "$inc": {"balance": bonus, "adventure_count": 1}
                }
            )
            msg = (
                f"{pe('star')} <b>{stylize_text('ADVENTURE')}</b> {pe('star')}\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"{pe('cherry')} {get_mention(user)} {stylize_text('ventured into the unknown')}...\n\n"
                f"{pe('heart')} {stylize_text('You found a health potion!')}\n"
                f"{pe('lightning')} {stylize_text('Sold it to a wandering merchant!')}\n"
                f"{pe('money')} {stylize_text('Earned')}: <code>{format_money(bonus)}</code>\n\n"
                f"━━━━━━━━━━━━━━━━━━"
            )

    elif event == "trader":
        items = ["Enchanted Sword", "Dragon Scale", "Phoenix Feather", "Mystic Amulet", "Shadow Cloak"]
        item = random.choice(items)
        item_styled = stylize_text(item)
        users_collection.update_one(
            {"user_id": user.id},
            {
                "$set": {"last_adventure": datetime.utcnow()},
                "$inc": {"adventure_count": 1}
            }
        )
        msg = (
            f"{pe('star')} <b>{stylize_text('ADVENTURE')}</b> {pe('star')}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"{pe('cherry')} {get_mention(user)} {stylize_text('ventured into the unknown')}...\n\n"
            f"{pe('diamond')} {stylize_text('You met a friendly trader!')}\n"
            f"{pe('gift')} {stylize_text('They gifted you a')}: <b>{item_styled}</b>\n"
            f"{pe('cherry')} {stylize_text('A rare collectible for your journey!')}\n\n"
            f"━━━━━━━━━━━━━━━━━━"
        )

    else:
        # Nothing happened
        users_collection.update_one(
            {"user_id": user.id},
            {
                "$set": {"last_adventure": datetime.utcnow()},
                "$inc": {"adventure_count": 1}
            }
        )
        msg = (
            f"{pe('star')} <b>{stylize_text('ADVENTURE')}</b> {pe('star')}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"{pe('cherry')} {get_mention(user)} {stylize_text('ventured into the unknown')}...\n\n"
            f"{pe('gift')} {stylize_text('The forest was peaceful today.')}\n"
            f"{pe('cherry')} {stylize_text('Nothing happened... but the journey was nice.')}\n\n"
            f"━━━━━━━━━━━━━━━━━━"
        )

    await smart_reply(update, msg)


# --- /market COMMAND ---
async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_exists(user)

    # Get top 5 richest users
    top_users = list(users_collection.find().sort("balance", -1).limit(5))

    # Market tips
    tips = [
        stylize_text("Fish prices are rising! Cast your rod now!"),
        stylize_text("Diamond ore is in high demand!"),
        stylize_text("Boss loot sells for premium coins!"),
        stylize_text("Magic Trees are rare but very valuable!"),
        stylize_text("Traders pay double for Golden Koi!"),
        stylize_text("Adventure rewards are boosted on weekends!"),
        stylize_text("Emeralds are the hottest commodity!"),
    ]
    tip = random.choice(tips)

    # Build seller list
    seller_lines = []
    for i, seller in enumerate(top_users, 1):
        s_name = seller.get("name", "Unknown")
        s_bal = seller.get("balance", 0)
        if i == 1:
            medal = pe("crown")
        elif i == 2:
            medal = pe("star")
        elif i == 3:
            medal = pe("diamond")
        else:
            medal = pe("cherry")
        line = f"{medal} <b>{i}.</b> {s_name} — <code>{format_money(s_bal)}</code>"
        seller_lines.append(line)

    sellers_text = "\n".join(seller_lines)

    msg = (
        f"{pe('money')} <b>{stylize_text('MARKETPLACE')}</b> {pe('money')}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{pe('crown')} <b>{stylize_text('Top Sellers')}</b>\n"
        f"{sellers_text}\n\n"
        f"{pe('lightning')} <b>{stylize_text('Market Trend')}</b>\n"
        f"{pe('star')} {tip}\n\n"
        f"{pe('diamond')} <b>{stylize_text('Tips')}</b>\n"
        f"{pe('cherry')} {stylize_text('Use /fish, /mine, /chop to earn!')}\n"
        f"{pe('fire')} {stylize_text('Fight /boss for big rewards!')}\n"
        f"{pe('gift')} {stylize_text('Go on /adventure for surprises!')}\n\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    await smart_reply(update, msg)


# --- ACHIEVEMENTS LIST ---
ACHIEVEMENTS_LIST = [
    {"name": "First Kill", "key": "kills", "threshold": 1, "emoji": "sword"},
    {"name": "10 Kills", "key": "kills", "threshold": 10, "emoji": "sword"},
    {"name": "50 Kills", "key": "kills", "threshold": 50, "emoji": "fire"},
    {"name": "First Fish", "key": "fish_count", "threshold": 1, "emoji": "diamond"},
    {"name": "50 Fish", "key": "fish_count", "threshold": 50, "emoji": "diamond"},
    {"name": "First Mine", "key": "mine_count", "threshold": 1, "emoji": "sword"},
    {"name": "50 Mines", "key": "mine_count", "threshold": 50, "emoji": "star"},
    {"name": "First Chop", "key": "chop_count", "threshold": 1, "emoji": "gift"},
    {"name": "50 Chops", "key": "chop_count", "threshold": 50, "emoji": "gift"},
    {"name": "Rich", "key": "balance", "threshold": 100000, "emoji": "money"},
    {"name": "Ultra Rich", "key": "balance", "threshold": 1000000, "emoji": "crown"},
    {"name": "Married", "key": "partner_id", "threshold": None, "emoji": "heart"},
    {"name": "Boss Slayer", "key": "boss_wins", "threshold": 5, "emoji": "fire"},
    {"name": "Adventurer", "key": "adventure_count", "threshold": 20, "emoji": "star"},
]


# --- /achievements COMMAND ---
async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_doc = ensure_user_exists(user)

    lines = []
    unlocked_count = 0
    total_count = len(ACHIEVEMENTS_LIST)

    for ach in ACHIEVEMENTS_LIST:
        ach_name = stylize_text(ach["name"])
        emoji = pe(ach["emoji"])

        if ach["key"] == "partner_id":
            # Special check for marriage
            is_unlocked = user_doc.get("partner_id") is not None
        else:
            value = user_doc.get(ach["key"], 0)
            is_unlocked = value >= ach["threshold"]

        if is_unlocked:
            unlocked_count += 1
            status_icon = pe("heart")
            line = f"{status_icon} {emoji} <b>{ach_name}</b> — {stylize_text('Unlocked')}"
        else:
            status_icon = pe("lock")
            line = f"{status_icon} {emoji} {ach_name} — {stylize_text('Locked')}"

        lines.append(line)

    achievements_text = "\n".join(lines)
    progress = stylize_text(f"{unlocked_count}/{total_count}")

    msg = (
        f"{pe('crown')} <b>{stylize_text('ACHIEVEMENTS')}</b> {pe('crown')}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{pe('star')} {stylize_text('Progress')}: <b>{progress}</b>\n\n"
        f"{achievements_text}\n\n"
        f"{pe('cherry')} {stylize_text('Keep grinding to unlock them all!')}\n\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    await smart_reply(update, msg)


# --- /guild COMMAND ---
async def guild(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_exists(user)

    msg = (
        f"{pe('crown')} <b>{stylize_text('GUILD SYSTEM')}</b> {pe('crown')}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{pe('star')} {stylize_text('Coming Soon...')}\n\n"
        f"{pe('sword')} {stylize_text('Create Guild')} — {stylize_text('Form your own clan!')}\n"
        f"{pe('heart')} {stylize_text('Join Guild')} — {stylize_text('Team up with others!')}\n"
        f"{pe('fire')} {stylize_text('Guild Wars')} — {stylize_text('Battle rival guilds!')}\n"
        f"{pe('money')} {stylize_text('Guild Bank')} — {stylize_text('Shared treasury!')}\n\n"
        f"{pe('diamond')} {stylize_text('Stay tuned for updates!')}\n"
        f"{pe('cherry')} {stylize_text('Big things are coming...')}\n\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    await smart_reply(update, msg)
