import os
import logging
import re
import random
import urllib.parse
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
DB_URL = os.getenv("DB_URL")

# Initialize Together AI client
client = Together(api_key=TOGETHER_API_KEY)

# Configure logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def connect_db():
    url = os.getenv("DB_URL")
    parsed_url = urllib.parse.urlparse(url)

    return mysql.connector.connect(
        host=parsed_url.hostname,
        user=parsed_url.username,
        password=parsed_url.password,
        database=parsed_url.path.lstrip('/'),
        port=parsed_url.port
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

# Function to escape special characters for MarkdownV2
def escape_markdown_v2(text: str) -> str:
    """
    Escapes special characters in text for Telegram MarkdownV2 formatting.
    """
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

# async def quiz(update: Update, context: CallbackContext):
#     """Generate a quiz question based on the user's topic input and send it."""
#     if context.args:
#         topic = " ".join(context.args)
#     else:
#         await update.message.reply_text("❌ Please provide a topic. Example: /quiz space")
#         return

#     print(f"✅ Generating quiz for topic: {topic}")

#     # AI Request
#     prompt = f"Generate a short quiz question about {topic}."
#     ai_response = query_together_ai(prompt)  
#     promptans = f"What's the correct answer to {prompt}?"

#     if not ai_response:
#         await update.message.reply_text("⚠️ AI could not generate a valid quiz. Try again!")
#         return

#     try:
        
#         print(f"✅ Quiz Question: {prompt}")
#         print(f"✅ Correct Answer: {[promptans]}")

#         # ✅ FIX: Add `parse_mode="Markdown"` to format messages properly
#         await update.message.reply_text(
#             f"🧠 *Quiz Time!*\n\n{prompt}\n\nReply with your answer!",
#             parse_mode="Markdown"
#         )

#         # Store answer temporarily in context.chat_data
#         context.chat_data["quiz_answer"] = {promptans}

#     except Exception as e:
#         print(f"❌ Error: {e}")
#         await update.message.reply_text(f"❌ Error processing quiz: {str(e)}")


# async def check_answer(update: Update, context: CallbackContext):
#     """Check user's answer and provide feedback."""
#     user_response = update.message.text.strip().lower()
#     correct_answer = context.chat_data.get("quiz_answer")

#     promptcheck = f"Is {correct_answer} and {user_response} same? Answer in yes or no"

#     if {promptcheck}.strip().lower() == "no":
#         await update.message.reply_text("⚠️ No active quiz. Start a new quiz with /quiz [topic].")
#         return

#     # Check the answer
#     if user_response == correct_answer:
#         response = "🎉 *Correct!* 🎉"
#     else:
#         response = f"❌ *Wrong!* The correct answer was: `{correct_answer}`"

#     await update.message.reply_text(response, parse_mode="Markdown")

#     # Clear stored answer
#     context.chat_data.pop("quiz_answer", None)

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
    #app.add_handler(CommandHandler("quiz", quiz))
    #app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("🤖 Bot is running...")
    app.run_polling(poll_interval=3)

if __name__ == "__main__":
    main()
