AI Mentor Telegram Bot

AI Mentor is a Telegram bot that provides study plans and explanations for various topics. It is built with Python and uses Railway for database hosting.

Features

/start - Registers the user and welcomes them.
/studyplan [topic] - Generates a structured study plan for the given topic.
/explain [topic] - Provides a clear explanation of the given topic.
Supports natural language queries for AI-powered responses.
Tech Stack

Python (Telegram Bot API, Together AI)
MySQL (Hosted on Railway)
Railway (Deployment & Database)
Setup

Clone the repository:
git clone https://github.com/GV-Sruthi/AI_mentor_bot/ai-mentor-bot.git
cd ai-mentor-bot

Install dependencies:
pip install -r requirements.txt

Create a .env file and add:
TELEGRAM_BOT_TOKEN=your_telegram_token
TOGETHER_API_KEY=your_together_ai_key
DB_URL=your_railway_database_url

Run the bot:
python main.py

Deployment on Railway

Push the code to GitHub.
Connect the repo to Railway.
Add environment variables (TELEGRAM_BOT_TOKEN, TOGETHER_API_KEY, DB_URL).
Deploy and start the bot!
Database Structure
The bot uses two tables:

users: Stores user telegram_id and username.
conversations: Stores user messages and AI responses.
License
This project is open-source. Feel free to modify and improve it!