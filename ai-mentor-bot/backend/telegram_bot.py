import mysql.connector
import os
import logging
import random
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Check if token is loaded
if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN not found. Make sure you have a .env file with the correct token.")

# Logging setup
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Database connection function
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "your_database_name")
        )
        return conn
    except mysql.connector.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

# Save Study Plan to DB
def save_study_plan(user_id, study_plan):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            query = "INSERT INTO study_plans (user_id, study_plan) VALUES (%s, %s)"
            cursor.execute(query, (user_id, study_plan))
            connection.commit()
            logging.info("✅ Study plan saved successfully!")
        except mysql.connector.Error as e:
            logging.error(f"❌ Error saving study plan: {e}")
        finally:
            cursor.close()
            connection.close()

# Retrieve Study Plan from DB
def retrieve_study_plan(user_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            query = "SELECT study_plan FROM study_plans WHERE user_id = %s ORDER BY id DESC LIMIT 1"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except mysql.connector.Error as e:
            logging.error(f"❌ Error retrieving study plan: {e}")
        finally:
            cursor.close()
            connection.close()
    return None

# Command Handlers
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hello! I'm your AI Mentor Bot. Use /studyplan to get a study plan or /quiz for a quiz!")

async def studyplan(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    study_plan_text = "📚 Here's your personalized study plan: [Generated AI Study Plan]"  # Placeholder logic
    save_study_plan(user_id, study_plan_text)
    await update.message.reply_text(f"✅ Study plan saved!\n\n{study_plan_text}")

async def explain(update: Update, context: CallbackContext) -> None:
    if context.args:
        topic = " ".join(context.args).lower()
        explanation = f"🔍 Explanation for *{topic.capitalize()}*:\n"

        explanations = {
            "python": "Python is a high-level programming language known for its readability.",
            "oop": "Object-Oriented Programming (OOP) is a paradigm based on objects and classes."
        }
        explanation += explanations.get(topic, "I don't have an explanation for that yet. Try another topic!")
    else:
        explanation = "❌ Please provide a topic. Example: /explain Python"

    await update.message.reply_text(explanation, parse_mode="Markdown")

# Sample quiz questions
quiz_questions = [
    {"question": "What is the output of `print(2 ** 3)`?", "options": ["6", "8", "9"], "answer": "8"},
    {"question": "Which keyword is used to define a function in Python?", "options": ["func", "define", "def"], "answer": "def"},
    {"question": "What does `len([1, 2, 3])` return?", "options": ["3", "2", "None"], "answer": "3"}
]

user_quiz_answers = {}

async def quiz(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    question = random.choice(quiz_questions)

    user_quiz_answers[user_id] = question["answer"]

    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(question["options"])])
    quiz_text = f"🧠 *Quiz Time!*\n\n{question['question']}\n\n{options_text}\n\nReply with the correct option number!"

    await update.message.reply_text(quiz_text, parse_mode="Markdown")

async def check_answer(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id

    if user_id in user_quiz_answers:
        correct_answer = user_quiz_answers[user_id]
        user_answer = update.message.text.strip()

        try:
            user_choice = int(user_answer)
            selected_option = quiz_questions[0]["options"][user_choice - 1]  # Get user's selected option

            if selected_option == correct_answer:
                await update.message.reply_text("✅ Correct! Well done.")
            else:
                await update.message.reply_text(f"❌ Incorrect. The correct answer was: {correct_answer}")

            del user_quiz_answers[user_id]  # Remove quiz data after answering
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Invalid response. Please reply with a valid option number (1, 2, or 3).")
    else:
        await update.message.reply_text("ℹ️ Use /quiz to start a new quiz first!")

# Main function to run the bot
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("studyplan", studyplan))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(CommandHandler("quiz", quiz))

    # Message handler for quiz answers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))

    logging.info("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
