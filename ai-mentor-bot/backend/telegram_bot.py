import mysql.connector
import os
import logging
import random
from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
)
import requests

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Check if token is loaded
if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN not found. Make sure you have a .env file with the correct token.")

# Logging setup
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# API URL for FastAPI backend
backend_url = "http://localhost:8000/process_message"

# Send message to FastAPI backend for processing
async def send_message_to_backend(message, chat_id):
    response = requests.post(backend_url, json={"message": message})
    
    if response.status_code == 200:
        reply = response.json().get("reply")
    else:
        reply = f"Error: {response.status_code}"
    
    return reply

# Command Handlers
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "👋 Hello! I'm your AI Mentor Bot. Here are some commands you can use:\n"
        "💡 /studyplan - Generate a personalized study plan.\n"
        "📝 /explain <topic> - Get explanations on various topics.\n"
        "🧠 /quiz - Test your knowledge with a quiz.\n"
        "🤖 Just ask me anything else, and I'll try to help you!"
    )

async def studyplan(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_message = "Create a study plan for a beginner learning Python programming."
    
    reply = await send_message_to_backend(user_message, user_id)
    await update.message.reply_text(reply)

async def explain(update: Update, context: CallbackContext) -> None:
    if context.args:
        topic = " ".join(context.args).lower()
        message = f"Explain {topic}"
        user_id = update.message.from_user.id
        
        reply = await send_message_to_backend(message, user_id)
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("❌ Please provide a topic. Example: /explain Python")

async def ask(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("❌ Please ask a question. Example: /ask What is AI?")
        return

    question = " ".join(context.args)
    user_id = update.message.from_user.id

    reply = await send_message_to_backend(question, user_id)
    await update.message.reply_text(reply)

async def quiz(update: Update, context: CallbackContext) -> None:
    question = random.choice([
        "What is the output of `print(2 ** 3)`?",
        "Which keyword is used to define a function in Python?",
        "What does `len([1, 2, 3])` return?"
    ])
    await update.message.reply_text(f"🧠 Quiz Time! {question}")

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    user_id = update.message.from_user.id

    reply = await send_message_to_backend(user_message, user_id)
    await update.message.reply_text(reply)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("studyplan", studyplan))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("ask", ask))
    
    # Message handler for general queries (calls FastAPI backend)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
