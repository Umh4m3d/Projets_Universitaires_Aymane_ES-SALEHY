import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler,
    MessageHandler, filters
)
from handlers import (
    start_handler, link_handler,
    today_handler, week_handler,
    absence_handler, payments_handler,
    notifications_handler, requests_handler, overdue_handler,
    help_handler, unknown_handler
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")


def run_bot():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("link", link_handler))
    app.add_handler(CommandHandler("today", today_handler))
    app.add_handler(CommandHandler("week", week_handler))
    app.add_handler(CommandHandler("requests", requests_handler))
    app.add_handler(CommandHandler("notifications", notifications_handler))
    app.add_handler(CommandHandler("overdue", overdue_handler))
    app.add_handler(CommandHandler("absence", absence_handler))
    app.add_handler(CommandHandler("payments", payments_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_handler))

    logging.info("Bot starting — polling Telegram servers...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
