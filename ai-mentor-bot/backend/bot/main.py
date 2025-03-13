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
        print(f"✅ AI Response: {response}")  # Debugging
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"⚠️ Error querying Together AI: {e}")
        return "⚠️ Sorry, I couldn't generate a response. Please try again later."


async def start_command(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    username = update.message.from_user.username
    add_user(user_id, username)
    await update.message.reply_text(f"Hello {username}! I'm your AI Mentor Bot. 🤖\nUse /studyplan, /explain, /quiz, or ask me anything!")

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
    print(f"✅ /studyplan command received! Args: {context.args}")  # Debugging

    if context.args:
        topic = " ".join(context.args)
    else:
        await update.message.reply_text("❌ Please provide a topic. Example: /studyplan arithmetic")
        return

    print(f"🔹 Topic received: {topic}")  # Debugging

    # Fetch past messages for better context
    past_messages = get_recent_conversations(user_id, limit=5)
    
    # Construct AI query with user context
    ai_prompt = f"""
    Previous conversation:\n{past_messages}
    Now, generate a structured study plan with 10 points under 300 words about {topic}. Ensure it's helpful and well-structured.
    """
    
    await update.message.reply_text(f"🔄 Generating your study plan on *{topic}*... Please wait.", parse_mode="Markdown")

    # Generate AI response
    study_plan_text = query_together_ai(ai_prompt)

    if not study_plan_text:
        study_plan_text = "⚠️ Sorry, I couldn't generate a study plan right now. Please try again later."

    print(f"📜 AI Response: {study_plan_text}")  # Debugging AI response

    # Save this conversation in the database
    save_conversation(user_id, f"/studyplan {topic}", study_plan_text)

    # Send response to the user
    for part in split_message(study_plan_text):
        await update.message.reply_text(part)

def save_conversation(user_id, message, response):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO conversations (user_id, message, response) VALUES (%s, %s, %s)", 
                   (user_id, message, response))
    db.commit()
    cursor.close()
    db.close()

def get_recent_conversations(user_id, limit=5):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT message, response FROM conversations WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s", 
        (user_id, limit)
    )
    messages = cursor.fetchall()
    cursor.close()
    db.close()
    
    # Format messages for AI prompt
    return "\n".join([f"User: {msg[0]}\nAI: {msg[1]}" for msg in messages])

async def explain(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    print(f"✅ /explain command received! Args: {context.args}")  # Debugging

    if context.args:
        topic = " ".join(context.args)
    else:
        await update.message.reply_text("❌ Please provide a topic. Example: /explain Python")
        return

    print(f"🔹 Topic received: {topic}")  # Debugging

    # Retrieve past messages for context
    past_messages = get_recent_conversations(user_id, limit=5)
    
    # Construct AI prompt with context
    ai_prompt = f"""
    Previous conversation:\n{past_messages}
    Now, explain {topic} in simple terms in under 500 words. Make it easy to understand.
    """
    
    await update.message.reply_text(f"🔄 Explaining *{topic}*... Please wait.", parse_mode="Markdown")

    # Get AI response
    explanation = query_together_ai(ai_prompt)

    if not explanation:
        explanation = "⚠️ Sorry, I couldn't generate an explanation right now. Please try again later."

    print(f"📜 AI Response: {explanation}")  # Debugging AI response

    # Save conversation in the database
    save_conversation(user_id, f"/explain {topic}", explanation)

    # Send response to the user
    for part in split_message(explanation):
        await update.message.reply_text(part)

# Dictionary to track active quizzes
quiz_questions = {}

# Function to escape special characters for MarkdownV2
def escape_markdown_v2(text: str) -> str:
    """
    Escapes special characters in text for Telegram MarkdownV2 formatting.
    """
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

async def quiz(update: Update, context: CallbackContext):
    user_id = update.message.chat_id

    if context.args:
        topic = " ".join(context.args)  # Get topic from user input
    else:
        await update.message.reply_text("❌ Please provide a topic. Example: /quiz tomatoes")
        return

    print(f"✅ /quiz command received! Topic: {topic}")  # Debugging

    # Prevent multiple active quizzes
    if user_id in quiz_questions:
        await update.message.reply_text("⚠️ You already have an active quiz! Answer it before starting a new one.")
        return

    # Retrieve past messages for context
    past_messages = get_recent_conversations(user_id, limit=5)

    # AI prompt with context
    prompt = f"""
    Previous conversation:\n{past_messages}
    Generate a multiple-choice quiz question about {topic}.
    Format:
    Question: <Your question>
    1. Option 1
    2. Option 2
    3. Option 3
    4. Option 4
    Answer: <Correct option number>
    """

    ai_response = query_together_ai(prompt)  # Fetch AI response

    # Debugging logs to check AI response
    print(f"✅ AI Response: {ai_response}")

    # Ensure AI response is in expected format
    if not ai_response or "Question:" not in ai_response or "Answer:" not in ai_response:
        await update.message.reply_text("⚠️ AI could not generate a quiz question. Please try again!")
        return

    try:
        lines = ai_response.strip().split("\n")

        if len(lines) < 6:
            raise ValueError("AI response format is incorrect.")

        question_text = escape_markdown_v2(lines[0].replace("Question: ", "").strip())

        options = []
        for i in range(1, 5):
            if ". " in lines[i]:
                options.append(escape_markdown_v2(lines[i].split(". ", 1)[1]))
            else:
                raise ValueError(f"Option format is incorrect: {lines[i]}")

        # Extract correct answer safely
        answer_line = lines[5].replace("Answer: ", "").strip()
        if not answer_line.isdigit():
            raise ValueError(f"Correct answer index is not a valid number: '{answer_line}'")

        correct_answer_index = int(answer_line) - 1
        if not (0 <= correct_answer_index < 4):
            raise ValueError(f"Correct answer index is out of range: {correct_answer_index + 1}")

        # Store original correct answer before shuffling
        original_correct_answer = options[correct_answer_index]

        # Shuffle options and find new correct index
        random.shuffle(options)
        correct_answer = options.index(original_correct_answer) + 1

        # Store the question in the dictionary
        quiz_questions[user_id] = {
            "question": question_text,
            "options": options,
            "answer": correct_answer
        }

        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
        quiz_text = f"🧠 *Quiz Time!* \n\n{question_text}\n\n{options_text}\n\n" \
                    "Reply with the correct option number!"

        # Save question to conversations table
        save_conversation(user_id, f"/quiz {topic}", f"Q: {question_text}\n{options_text}")

        await update.message.reply_text(escape_markdown_v2(quiz_text), parse_mode="MarkdownV2")

    except Exception as e:
        error_message = escape_markdown_v2(str(e))
        await update.message.reply_text(f"❌ *Error generating quiz:* {error_message}\nTry again!", parse_mode="MarkdownV2")

async def check_answer(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    if user_id not in quiz_questions:
        await update.message.reply_text("⚠️ *No active quiz.*\nStart a new quiz with `/quiz [topic]`.", parse_mode="MarkdownV2")
        return

    user_answer = update.message.text.strip()

    if not user_answer.isdigit():
        await update.message.reply_text("⚠️ *Please reply with a number (1-4).*", parse_mode="MarkdownV2")
        return

    user_answer = int(user_answer)
    correct_answer = quiz_questions[user_id]["answer"]

    if user_answer == correct_answer:
        response_text = "🎉 *Correct!* Well done!"
    else:
        response_text = f"❌ *Wrong!* The correct answer was `{correct_answer}`."

    # Save user answer to conversations table
    save_conversation(user_id, f"User answered: {user_answer}", response_text)

    await update.message.reply_text(response_text, parse_mode="MarkdownV2")
    del quiz_questions[user_id]  # Remove question after answering

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    text = update.message.text

    # Get recent messages for context
    past_messages = get_recent_conversations(user_id, limit=5)

    # Construct AI prompt with context
    ai_prompt = f"Previous conversation:\n{past_messages}\nUser: {text}\nAI:"

    # Generate AI response
    response = query_together_ai(ai_prompt)

    # Store the new conversation in the database
    save_conversation(user_id, text, response)

    # Send AI response to the user
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
