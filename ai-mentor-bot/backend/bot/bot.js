import { Telegraf } from "telegraf";
import dotenv from "dotenv";
import { queryDatabase } from "./db.js";

dotenv.config();

const bot = new Telegraf(process.env.BOT_TOKEN);

// Function to save user info in the database
const saveUser = async (ctx) => {
  const { id: telegram_id, first_name, last_name, username } = ctx.from;
  const query = `INSERT INTO users (telegram_id, first_name, last_name, username) 
                 VALUES (?, ?, ?, ?) 
                 ON DUPLICATE KEY UPDATE first_name=VALUES(first_name), last_name=VALUES(last_name), username=VALUES(username)`;
  await queryDatabase(query, [telegram_id, first_name, last_name, username]);
};

// Function to log messages
const logMessage = async (user_id, message_text, response_text) => {
  const query = `INSERT INTO messages (user_id, message_text, response_text) VALUES (?, ?, ?)`;
  await queryDatabase(query, [user_id, message_text, response_text]);
};

// Bot start command
bot.start(async (ctx) => {
  await saveUser(ctx);
  ctx.reply("Welcome! This is your AI Mentor bot.");
});

// Fetch all users from the database
bot.command("getdata", async (ctx) => {
  try {
    const results = await queryDatabase("SELECT * FROM users");
    ctx.reply(`Database Results: ${JSON.stringify(results)}`);
  } catch (error) {
    ctx.reply("Error fetching data from MySQL.");
  }
});

// Handle user messages and log them
bot.on("text", async (ctx) => {
  const userMessage = ctx.message.text;
  const botResponse = `You said: ${userMessage}`; // Placeholder response
  
  await saveUser(ctx);
  await logMessage(ctx.from.id, userMessage, botResponse);
  
  ctx.reply(botResponse);
});

export { bot };
