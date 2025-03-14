from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import requests
import logging
import pytz

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

backend_url = "http://localhost:8000/process_message"

async def send_message_to_backend(message, chat_id):
    response = requests.post(backend_url, json={"message": message})
    if response.status_code == 200:
        return response.json().get("reply")
    return f"Error: {response.status_code}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I'm your AI Mentor Bot. How can I assist you today?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id
    reply = await send_message_to_backend(user_message, chat_id)
    await update.message.reply_text(reply)

def main():
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler(timezone=pytz.utc)  # Or your desired timezone
    scheduler.start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("🤖 Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
