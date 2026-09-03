import os
import time
from dotenv import load_dotenv

# ===============================
# LOAD .env FILE
# ===============================
load_dotenv()

# Track Uptime
START_TIME = time.time()

# ===============================
# ENV VARIABLES
# ===============================
TOKEN = os.getenv("BOT_TOKEN", "").strip()
MONGO_URI = os.getenv("MONGO_URI", "").strip()

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable is missing")

# --- AI KEYS ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# Codestral usually uses the same Mistral Key
CODESTRAL_API_KEY = os.getenv("CODESTRAL_API_KEY", MISTRAL_API_KEY).strip()

PORT = int(os.environ.get("PORT", 8080))

# ===============================
# UPDATER CONFIG
# ===============================
UPSTREAM_REPO = os.getenv("UPSTREAM_REPO", "").strip()
GIT_TOKEN = os.getenv("GIT_TOKEN", "").strip()

# ===============================
# IMAGES & LINKS
# ===============================
START_IMG_URL = os.getenv(
    "START_IMG_URL",
    "https://files.catbox.moe/5501du.jpg"
)

HELP_IMG_URL = os.getenv(
    "HELP_IMG_URL",
    "https://iili.io/nHTjpVI.jpg"
)

WELCOME_IMG_URL = os.getenv(
    "WELCOME_IMG_URL",
    "https://files.catbox.moe/ae87t2.jpg"
)

SUPPORT_GROUP = os.getenv(
    "SUPPORT_GROUP",
    "https://t.me/AnnieBotSupport"
)

SUPPORT_CHANNEL = os.getenv(
    "SUPPORT_CHANNEL",
    "https://t.me/AnnieMusicBots"
)

OWNER_LINK = os.getenv(
    "OWNER_LINK",
    "https://t.me/flirt_x"
)

# ===============================
# IDS
# ===============================
try:
    LOGGER_ID = int(os.getenv("LOGGER_ID", "0").strip())
except Exception:
    LOGGER_ID = 0

try:
    OWNER_ID = int(os.getenv("OWNER_ID", "0").strip())
except Exception:
    OWNER_ID = 0

SUDO_IDS_STR = os.getenv("SUDO_IDS", "").strip()

# Convert SUDO IDs to list of ints (safe)
SUDO_IDS = []
if SUDO_IDS_STR:
    for x in SUDO_IDS_STR.split():
        try:
            SUDO_IDS.append(int(x))
        except ValueError:
            pass

# ===============================
# USERBOT CONFIG (Premium Emoji)
# ===============================
API_ID = int(os.getenv("API_ID", "0").strip())
API_HASH = os.getenv("API_HASH", "").strip()
SESSION_STRING = os.getenv("SESSION_STRING", "").strip()

# ===============================
# GAME CONSTANTS
# ===============================
BOT_NAME = "🌸 ʜᴇᴇʀɪʏᴇ ×͜࿐"

REVIVE_COST = 500
PROTECT_1D_COST = 1000
PROTECT_2D_COST = 1800
REGISTER_BONUS = 5000
CLAIM_BONUS = 2000
RIDDLE_REWARD = 1000
DIVORCE_COST = 2000
WAIFU_PROPOSE_COST = 5000

TAX_RATE = 0.10
MARRIED_TAX_RATE = 0.05

AUTO_REVIVE_HOURS = 6
AUTO_REVIVE_BONUS = 200

MIN_CLAIM_MEMBERS = 100

# ===============================
# 🛒 SHOP ITEMS (UNCHANGED)
# ===============================
SHOP_ITEMS = [
    {"id": "stick", "name": "🪵 Stick", "price": 500, "type": "weapon", "buff": 0.01},
    {"id": "brick", "name": "🧱 Brick", "price": 1000, "type": "weapon", "buff": 0.02},
    {"id": "slingshot", "name": "🪃 Slingshot", "price": 2000, "type": "weapon", "buff": 0.03},
    {"id": "knife", "name": "🔪 Knife", "price": 3500, "type": "weapon", "buff": 0.05},
    {"id": "bat", "name": "🏏 Bat", "price": 5000, "type": "weapon", "buff": 0.08},
    {"id": "axe", "name": "🪓 Axe", "price": 7500, "type": "weapon", "buff": 0.10},
    {"id": "hammer", "name": "🔨 Hammer", "price": 10000, "type": "weapon", "buff": 0.12},
    {"id": "chainsaw", "name": "🪚 Chainsaw", "price": 15000, "type": "weapon", "buff": 0.15},
    {"id": "pistol", "name": "🔫 Pistol", "price": 25000, "type": "weapon", "buff": 0.20},
    {"id": "shotgun", "name": "🧨 Shotgun", "price": 40000, "type": "weapon", "buff": 0.25},
    {"id": "uzi", "name": "🔫 Uzi", "price": 55000, "type": "weapon", "buff": 0.30},
    {"id": "katana", "name": "⚔️ Katana", "price": 75000, "type": "weapon", "buff": 0.35},
    {"id": "ak47", "name": "💥 AK-47", "price": 100000, "type": "weapon", "buff": 0.40},
    {"id": "minigun", "name": "🔥 Minigun", "price": 150000, "type": "weapon", "buff": 0.45},
    {"id": "sniper", "name": "🎯 Sniper", "price": 200000, "type": "weapon", "buff": 0.50},
    {"id": "rpg", "name": "🚀 RPG", "price": 300000, "type": "weapon", "buff": 0.55},
    {"id": "tank", "name": "🚜 Tank", "price": 500000, "type": "weapon", "buff": 0.58},
    {"id": "laser", "name": "⚡ Laser", "price": 800000, "type": "weapon", "buff": 0.59},
    {"id": "deathnote", "name": "📓 Death Note", "price": 5000000, "type": "weapon", "buff": 0.60},

    {"id": "paper", "name": "📰 Newspaper", "price": 500, "type": "armor", "buff": 0.01},
    {"id": "cardboard", "name": "📦 Cardboard", "price": 1000, "type": "armor", "buff": 0.02},
    {"id": "cloth", "name": "👕 Cloth", "price": 2500, "type": "armor", "buff": 0.05},
    {"id": "leather", "name": "🧥 Leather", "price": 8000, "type": "armor", "buff": 0.08},
    {"id": "chain", "name": "⛓️ Chain", "price": 20000, "type": "armor", "buff": 0.10},
    {"id": "riot", "name": "🛡️ Riot Shield", "price": 40000, "type": "armor", "buff": 0.15},
    {"id": "swat", "name": "👮 SWAT", "price": 60000, "type": "armor", "buff": 0.20},
    {"id": "iron", "name": "🦾 Iron Suit", "price": 100000, "type": "armor", "buff": 0.25},
    {"id": "diamond", "name": "💎 Diamond", "price": 200000, "type": "armor", "buff": 0.30},
    {"id": "obsidian", "name": "⚫ Obsidian", "price": 400000, "type": "armor", "buff": 0.35},
    {"id": "nano", "name": "🧬 Nano Suit", "price": 700000, "type": "armor", "buff": 0.40},
    {"id": "vibranium", "name": "🛡️ Vibranium", "price": 1500000, "type": "armor", "buff": 0.50},
    {"id": "force", "name": "🔮 Forcefield", "price": 3000000, "type": "armor", "buff": 0.55},
    {"id": "plot", "name": "🎬 Plot Armor", "price": 10000000, "type": "armor", "buff": 0.60},

    {"id": "cookie", "name": "🍪 Cookie", "price": 100, "type": "flex", "buff": 0},
    {"id": "coffee", "name": "☕ Starbucks", "price": 300, "type": "flex", "buff": 0},
    {"id": "rose", "name": "🌹 Rose", "price": 500, "type": "flex", "buff": 0},
    {"id": "sushi", "name": "🍣 Sushi Platter", "price": 2000, "type": "flex", "buff": 0},
    {"id": "vodka", "name": "🍾 Vodka", "price": 5000, "type": "flex", "buff": 0},
    {"id": "ring", "name": "💍 Gold Ring", "price": 10000, "type": "flex", "buff": 0},
    {"id": "ps5", "name": "🎮 PS5 Pro", "price": 15000, "type": "flex", "buff": 0},
    {"id": "iphone", "name": "📱 iPhone 16 Pro", "price": 25000, "type": "flex", "buff": 0},
    {"id": "macbook", "name": "💻 MacBook M3", "price": 50000, "type": "flex", "buff": 0},
    {"id": "gucci", "name": "👜 Gucci Bag", "price": 75000, "type": "flex", "buff": 0},
    {"id": "rolex", "name": "⌚ Rolex", "price": 100000, "type": "flex", "buff": 0},
    {"id": "diamond_ring", "name": "💎 Solitaire", "price": 250000, "type": "flex", "buff": 0},
    {"id": "tesla", "name": "🚗 Tesla", "price": 400000, "type": "flex", "buff": 0},
    {"id": "lambo", "name": "🏎️ Lambo", "price": 800000, "type": "flex", "buff": 0},
    {"id": "heli", "name": "🚁 Helicopter", "price": 1500000, "type": "flex", "buff": 0},
    {"id": "yacht", "name": "🛳️ Super Yacht", "price": 3000000, "type": "flex", "buff": 0},
    {"id": "mansion", "name": "🏰 Mansion", "price": 5000000, "type": "flex", "buff": 0},
    {"id": "jet", "name": "✈️ Private Jet", "price": 10000000, "type": "flex", "buff": 0},
    {"id": "island", "name": "🏝️ Island", "price": 50000000, "type": "flex", "buff": 0},
    {"id": "moon", "name": "🌑 The Moon", "price": 100000000, "type": "flex", "buff": 0},
    {"id": "mars", "name": "🪐 Mars", "price": 500000000, "type": "flex", "buff": 0},
    {"id": "sun", "name": "☀️ The Sun", "price": 1000000000, "type": "flex", "buff": 0},
    {"id": "galaxy", "name": "🌌 Milky Way", "price": 5000000000, "type": "flex", "buff": 0},
    {"id": "blackhole", "name": "🕳️ Black Hole", "price": 9999999999, "type": "flex", "buff": 0},
]
