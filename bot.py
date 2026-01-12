import sqlite3
import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from dotenv import load_dotenv
import os

# =====================
# ENVIRONMENT VARIABLES
# =====================
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")

# =====================
# LOGGING
# =====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =====================
# ADMIN SETTINGS
# =====================
ADMIN_ID = 7783336659  # replace with your Telegram ID

# =====================
# DATABASE SETUP
# =====================
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_seen TEXT,
    last_seen TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    event TEXT,
    timestamp TEXT
)
""")

conn.commit()

# =====================
# ANALYTICS FUNCTIONS
# =====================
def log_user(user):
    now = datetime.now().isoformat()

    cursor.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)",
        (user.id, user.username, now, now)
    )

    cursor.execute(
        "UPDATE users SET last_seen=? WHERE user_id=?",
        (now, user.id)
    )

    conn.commit()

def log_event(user_id, event):
    cursor.execute(
        "INSERT INTO events (user_id, event, timestamp) VALUES (?, ?, ?)",
        (user_id, event, datetime.now().isoformat())
    )
    conn.commit()

# =====================
# BOT MENU
# =====================
def main_menu(user_id=None):
    keyboard = [
        [
            InlineKeyboardButton("🌐 Website", callback_data="website"),
            InlineKeyboardButton("✈️ Telegram Channel", callback_data="telegram")
        ]
    ]

    if user_id == ADMIN_ID:
        keyboard.append([
            InlineKeyboardButton("📊 Analytics", callback_data="analytics")
        ])

    return InlineKeyboardMarkup(keyboard)

# =====================
# /START COMMAND
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    log_user(user)
    log_event(user.id, "start_bot")

    welcome_message = (
        "👋 Welcome to PokeninJapan!\n\n"
        "We offer wholesale for Pokémon cards, TCGs, One Piece cards & more 🇯🇵\n\n"
        "Use the buttons below to:\n"
        "🌐 Visit our website\n"
        "✈️ Join our Telegram channel\n\n"
        "Select an option below 👇"
    )

    await update.message.reply_text(
        welcome_message,
        reply_markup=main_menu(user.id)
    )

# =====================
# BUTTON HANDLER
# =====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "website":
        log_event(user.id, "click_website")
        await query.message.reply_text(
            "🌐 Visit our website:\nhttps://pokeninjapan.site"
        )

    elif query.data == "telegram":
        log_event(user.id, "click_telegram")
        await query.message.reply_text(
            "✈️ Join our Telegram channel:\nhttps://t.me/Pokeninjapan"
        )

    elif query.data == "analytics":
        if user.id != ADMIN_ID:
            await query.message.reply_text("❌ You are not allowed to see analytics.")
            return

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM events WHERE event='click_website'")
        website_clicks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM events WHERE event='click_telegram'")
        telegram_clicks = cursor.fetchone()[0]

        stats_message = (
            "📊 Bot Analytics\n\n"
            f"👥 Total Users: {total_users}\n"
            f"🌐 Website Clicks: {website_clicks}\n"
            f"✈️ Telegram Clicks: {telegram_clicks}"
        )

        await query.message.reply_text(stats_message)

# =====================
# BOT STARTUP
# =====================
if __name__ == "__main__":
    from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
    import os

    TOKEN = os.getenv("BOT_TOKEN")
    PORT = int(os.environ.get("PORT", 8443))  # Render sets a PORT automatically
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Webhook setup ONLY
    WEBHOOK_URL = f"https://telegrambot-lm09.onrender.com/{TOKEN}"
    print(f"🤖 Starting bot via webhook at {WEBHOOK_URL}...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )



