import os
import logging
import re
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
    await update.message.reply_text("Hello! I'm your AI Mentor Bot. 🤖\nUse /studyplan, /quiz, or ask me anything!")

# Function to split long messages

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
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

async def quiz(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    topic = "Artificial Intelligence"
    if context.args:
        topic = " ".join(context.args)
    prompt = f"Generate a multiple-choice quiz question about {topic}."
    ai_response = query_together_ai(prompt)
    try:
        lines = ai_response.split("\n")
        question_text = escape_markdown_v2(lines[0].replace("Question: ", "").strip())
        options = [escape_markdown_v2(lines[i].split(". ")[1]) for i in range(2, 5)]
        correct_answer_index = int(lines[5].replace("Answer: ", "").strip()) - 1
        shuffled_options = options[:]
        random.shuffle(shuffled_options)
        correct_answer = shuffled_options.index(options[correct_answer_index]) + 1
        quiz_questions[user_id] = {"question": question_text, "options": shuffled_options, "answer": correct_answer}
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(shuffled_options)])
        quiz_text = f"🧠 *Quiz Time!* \n\n{question_text}\n\n{options_text}\n\nReply with the correct option number!"
        await update.message.reply_text(quiz_text, parse_mode="MarkdownV2")
    except Exception as e:
        await update.message.reply_text(f"❌ Error generating quiz: {escape_markdown_v2(str(e))}\nTry again!", parse_mode="MarkdownV2")

async def check_answer(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in quiz_questions:
        question_data = quiz_questions[user_id]
        correct_answer = question_data["answer"]
        user_answer = update.message.text.strip()
        try:
            user_choice = int(user_answer)
            if 1 <= user_choice <= len(question_data["options"]):
                selected_option = question_data["options"][user_choice - 1]
                if selected_option == question_data["options"][correct_answer - 1]:
                    await update.message.reply_text("✅ Correct! Well done.")
                else:
                    await update.message.reply_text(f"❌ Incorrect. The correct answer was: {question_data['options'][correct_answer - 1]}")
            else:
                await update.message.reply_text("❌ Please reply with a valid option number.")
            del quiz_questions[user_id]
        except ValueError:
            await update.message.reply_text("❌ Invalid response. Please reply with a number.")
    else:
        await update.message.reply_text("ℹ️ Use /quiz to start a new quiz first!")

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    response = query_together_ai(text)
    for part in split_message(response):
        await update.message.reply_text(part)

async def error(update: Update, context: CallbackContext):
    logging.error(f'Update {update} caused error {context.error}')

def main():
    print('Starting bot...')
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("studyplan", studyplan))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))
    app.add_error_handler(error)
    logging.info("🤖 Bot is running...")
    app.run_polling(poll_interval=3)

if __name__ == "__main__":
    main()

