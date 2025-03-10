import mysql.connector
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ContextTypes
)
import random
from dotenv import load_dotenv
import os

load_dotenv()  # This will read the .env file and load the environment variables

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # This retrieves your token from the .env file

print(TOKEN)  # Test to see if your token is loaded correctly. It should print your bot token.


# Set up logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Database connection functions
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",   
        user="root",         
        password="your_password",  
        database="your_database_name"
    )

# Save Study Plan to DB
def save_study_plan(user_id, study_plan):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            query = "INSERT INTO study_plans (user_id, study_plan) VALUES (%s, %s)"
            cursor.execute(query, (user_id, study_plan))
            connection.commit()
            print("✅ Study plan saved successfully!")
        except mysql.connector.Error as e:
            print(f"❌ Error saving study plan: {e}")
        finally:
            cursor.close()
            connection.close()

# Retrieve Study Plan from DB
def retrieve_study_plan(user_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            query = "SELECT study_plan FROM study_plans WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchall()
            if result:
                return result[-1][0]  # Return the latest study plan
            return None
        except mysql.connector.Error as e:
            print(f"❌ Error retrieving study plan: {e}")
        finally:
            cursor.close()
            connection.close()


# Command Handlers
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hello! I'm your AI Mentor Bot. How can I assist you?")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()


async def studyplan(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    study_plan_text = "Here's your personalized study plan: [Your AI logic here]"
    save_study_plan(user_id, study_plan_text)
    await update.message.reply_text(f"Study plan saved! Your plan:\n\n{study_plan_text}")

async def explain(update: Update, context: CallbackContext) -> None:
    if context.args:
        topic = " ".join(context.args)
        explanation = f"🔍 Explanation for {topic}:\n"
        
        if topic.lower() == "python":
            explanation += "Python is a high-level, interpreted programming language known for its simplicity and readability."
        elif topic.lower() == "oop":
            explanation += "Object-Oriented Programming (OOP) is a paradigm based on objects and classes."
        else:
            explanation += "I don't have an explanation for that yet. Try another topic!"
    else:
        explanation = "Please provide a topic. Example: /explain Python"
    
    await update.message.reply_text(explanation, parse_mode="Markdown")

# Sample quiz questions
quiz_questions = [
    {"question": "What is the output of `print(2 ** 3)`?", "options": ["6", "8", "9"], "answer": "8"},
    {"question": "Which keyword is used to define a function in Python?", "options": ["func", "define", "def"], "answer": "def"},
    {"question": "What does `len([1, 2, 3])` return?", "options": ["3", "2", "None"], "answer": "3"}
]

user_quiz_answers = {}

async def quiz(update: Update, context: CallbackContext) -> None:
    question = random.choice(quiz_questions)
    user_quiz_answers[update.message.chat_id] = question["answer"]

    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(question["options"])])
    quiz_text = f"🧠 Quiz Time!\n\n{question['question']}\n\n{options_text}\n\nReply with the correct option number!"
    
    await update.message.reply_text(quiz_text, parse_mode="Markdown")

async def check_answer(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    if user_id in user_quiz_answers:
        correct_answer = user_quiz_answers[user_id]
        user_answer = update.message.text.strip()
        
        if user_answer.isdigit() and int(user_answer) in range(1, 4):
            selected_option = quiz_questions[0]["options"][int(user_answer) - 1]
            if selected_option == correct_answer:
                await update.message.reply_text("✅ Correct! Well done.")
            else:
                await update.message.reply_text(f"❌ Incorrect. The correct answer was: {correct_answer}")
            del user_quiz_answers[user_id]
        else:
            await update.message.reply_text("Please reply with a valid option number (1, 2, or 3).")
    else:
        await update.message.reply_text("Use /quiz to start a new quiz first!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("studyplan", studyplan))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))

    logging.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
