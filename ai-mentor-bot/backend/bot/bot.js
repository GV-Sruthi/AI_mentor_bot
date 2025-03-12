import { Telegraf } from "telegraf";
import dotenv from "dotenv";
import { queryDatabase } from "./db.js";

dotenv.config();

const bot = new Telegraf(process.env.BOT_TOKEN);

bot.start((ctx) => ctx.reply("Welcome! This is your AI Mentor bot."));

bot.command("getdata", async (ctx) => {
  try {
    const results = await queryDatabase("SELECT * FROM users"); // Example query
    ctx.reply(`Database Results: ${JSON.stringify(results)}`);
  } catch (error) {
    ctx.reply("Error fetching data from MySQL.");
  }
});

export { bot };

