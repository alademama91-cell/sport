import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Use /scores /schedule /live to get sports updates."
    )

async def scores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Replace with real sports API call
    await update.message.reply_text("Today's scores: (demo data) Team A 2 - 1 Team B")

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Upcoming matches: (demo data) Team A vs Team C, tomorrow 20:00")

async def live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Live now: (demo data) Team B vs Team D, 1-1, 67'")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scores", scores))
    app.add_handler(CommandHandler("schedule", schedule))
    app.add_handler(CommandHandler("live", live))
    app.run_polling()
