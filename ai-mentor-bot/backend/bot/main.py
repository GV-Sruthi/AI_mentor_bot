# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/")
# def read_root():
#     return {"message": "FastAPI is running!"}

# @app.post("/ask-ai")
# def ask_ai(request: dict):
#     return {"response": f"AI Response to: {request['prompt']}"}

import os
import logging
import random
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

# Initialize Together AI client
client = Together(api_key=TOGETHER_API_KEY)

# Configure logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


# Function to call Llama 3.3-70B on Together AI
def query_together_ai(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=[
                {"role": "system", "content": "You are a friendly AI mentor. Help students learn complex topics, generate structured study plans, and provide clear explanations."},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


# Command: Start
async def startcommand(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello! I'm your AI Mentor Bot. 🤖\n"
                                    "Use /studyplan to get a study plan, /quiz for a quiz, \n"
                                    "or simply ask me anything!")


# Command: Study Plan (Generated using AI)
async def studyplan(update: Update, context: CallbackContext):
    study_plan_text = query_together_ai("Generate a structured study plan for learning AI and ML.")
    await update.message.reply_text(f"📚 Your personalized study plan:\n\n{study_plan_text}")


# Command: Explain a Topic
async def explain(update: Update, context: CallbackContext):
    if context.args:
        topic = " ".join(context.args)
        explanation = query_together_ai(f"Explain {topic} in simple terms.")
    else:
        explanation = "❌ Please provide a topic. Example: /explain Python"

    await update.message.reply_text(explanation)


# Command: Quiz
quiz_questions = [
    {"question": "What is the output of `print(2 ** 3)`?", "options": ["6", "8", "9"], "answer": "8"},
    {"question": "Which keyword is used to define a function in Python?", "options": ["func", "define", "def"], "answer": "def"},
    {"question": "What does `len([1, 2, 3])` return?", "options": ["3", "2", "None"], "answer": "3"}
]

user_quiz_data = {}  # Store user's quiz state


async def quiz(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    question = random.choice(quiz_questions)

    # Store the question and answer for this user
    user_quiz_data[user_id] = question

    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(question["options"])])
    quiz_text = f"🧠 *Quiz Time!*\n\n{question['question']}\n\n{options_text}\n\nReply with the correct option number!"

    await update.message.reply_text(quiz_text, parse_mode="MarkdownV2")


async def check_answer(update: Update, context: CallbackContext):
    user_id = update.message.chat_id

    if user_id in user_quiz_data:
        question_data = user_quiz_data[user_id]
        correct_answer = question_data["answer"]
        user_answer = update.message.text.strip()

        try:
            user_choice = int(user_answer)
            if 1 <= user_choice <= len(question_data["options"]):  # Ensure valid range
                selected_option = question_data["options"][user_choice - 1]

                if selected_option == correct_answer:
                    await update.message.reply_text("✅ Correct! Well done.")
                else:
                    await update.message.reply_text(f"❌ Incorrect. The correct answer was: {correct_answer}")
            else:
                await update.message.reply_text("❌ Please reply with a valid option number.")

            del user_quiz_data[user_id]  # Remove quiz data after answering

        except ValueError:
            await update.message.reply_text("❌ Invalid response. Please reply with a number.")

    else:
        await update.message.reply_text("ℹ️ Use /quiz to start a new quiz first!")


# Handle user messages (AI-powered responses)
async def handle_message(update: Update, context: CallbackContext):
    text: str = update.message.text
    logging.info(f'User ({update.message.chat.id}): "{text}"')

    response = query_together_ai(text)  # Call AI API

    logging.info(f'Bot: {response}')
    await update.message.reply_text(response)


# Error handling
async def error(update: Update, context: CallbackContext):
    logging.error(f'Update {update} caused error {context.error}')


# Main function to run the bot
def main():
    print('Starting bot...')
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", startcommand))
    app.add_handler(CommandHandler("studyplan", studyplan))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(CommandHandler("quiz", quiz))

    # Message handler for AI-powered responses
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Check answers for quizzes
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))

    # Error handling
    app.add_error_handler(error)

    logging.info("🤖 Bot is running...")
    app.run_polling(poll_interval=3)


if __name__ == "__main__":
    main()
