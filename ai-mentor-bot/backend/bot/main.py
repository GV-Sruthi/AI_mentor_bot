import os
import logging
import re
import random
import mysql.connector
from together import Together
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, CallbackContext
)

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Initialize Together AI client
client = Together(api_key=TOGETHER_API_KEY)

# Configure logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def connect_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def add_user(user_id, username):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("INSERT IGNORE INTO users (telegram_id, username) VALUES (%s, %s)", (user_id, username))
    db.commit()
    cursor.close()
    db.close()

def query_together_ai(prompt: str) -> str:
    """Call Llama 3.3-70B on Together AI."""
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI mentor."},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error querying Together AI: {e}")
        return "⚠️ Sorry, I couldn't generate a response. Please try again later."

async def start_command(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    username = update.message.from_user.username
    add_user(user_id, username)
    await update.message.reply_text("Hello! I'm your AI Mentor Bot. 🤖\nUse /studyplan, /quiz, or ask me anything!")

def split_message(text, max_length=4096):
    parts = []
    while len(text) > max_length:
        split_index = text.rfind("\n", 0, max_length)
        if split_index == -1:
            split_index = max_length
        parts.append(text[:split_index])
        text = text[split_index:].lstrip()
    parts.append(text)
    return parts

async def studyplan(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    print("✅ /studyplan command received!")
    await update.message.reply_text("🔄 Generating your study plan... Please wait.")
    study_plan_text = query_together_ai("Generate a structured study plan for learning AI and ML.")
    if not study_plan_text:
        study_plan_text = "⚠️ Sorry, I couldn't generate a study plan right now. Please try again later."
    for part in split_message(study_plan_text):
        await update.message.reply_text(part)

async def explain(update: Update, context: CallbackContext):
    if context.args:
        topic = " ".join(context.args)
        explanation = query_together_ai(f"Explain {topic} in simple terms.")
    else:
        explanation = "❌ Please provide a topic. Example: /explain Python"
    await update.message.reply_text(explanation)

quiz_questions = {}

def escape_markdown_v2(text):
    """Escape special characters for Telegram MarkdownV2."""
    return re.sub(r'([_*\[\]()~`>#+-=|{}.!])', r'\\\1', text)

async def quiz(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    topic = "Artificial Intelligence"

    if context.args:
        topic = " ".join(context.args)  # Extract topic from user input

    prompt = f"Generate a multiple-choice quiz question about {topic}.\n" \
             "Format:\n" \
             "Question: <Your question>\n" \
             "1. Option 1\n" \
             "2. Option 2\n" \
             "3. Option 3\n" \
             "4. Option 4\n" \
             "Answer: <Correct option number>"

    ai_response = query_together_ai(prompt)  # Fetch AI response

    try:
        lines = ai_response.strip().split("\n")

        # Validate response length
        if len(lines) < 6:
            raise ValueError("AI response format is incorrect.")

        question_text = escape_markdown_v2(lines[0].replace("Question: ", "").strip())

        options = []
        for i in range(1, 5):
            if ". " in lines[i]:  # Ensure valid format
                options.append(escape_markdown_v2(lines[i].split(". ", 1)[1]))
            else:
                raise ValueError("Option format is incorrect.")

        correct_answer_index = int(lines[5].replace("Answer: ", "").strip()) - 1
        if not (0 <= correct_answer_index < 4):
            raise ValueError("Correct answer index is out of range.")

        shuffled_options = options[:]
        random.shuffle(shuffled_options)
        correct_answer = shuffled_options.index(options[correct_answer_index]) + 1

        quiz_questions[user_id] = {
            "question": question_text,
            "options": shuffled_options,
            "answer": correct_answer
        }

        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(shuffled_options)])
        quiz_text = f"🧠 *Quiz Time!* \n\n{question_text}\n\n{options_text}\n\n" \
                    "Reply with the correct option number!"

        await update.message.reply_text(quiz_text, parse_mode="MarkdownV2")

    except Exception as e:
        error_message = escape_markdown_v2(str(e))
        await update.message.reply_text(f"❌ Error generating quiz: {error_message}\\nTry again!", parse_mode="MarkdownV2")
        
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    text = update.message.text
    response = query_together_ai(text)
    for part in split_message(response):
        await update.message.reply_text(part)

def main():
    print('Starting bot...')
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("studyplan", studyplan))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("🤖 Bot is running...")
    app.run_polling(poll_interval=3)

if __name__ == "__main__":
    main()
