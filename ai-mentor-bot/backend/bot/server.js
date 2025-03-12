import express from "express";
import dotenv from "dotenv";
import { bot } from "./bot.js";

dotenv.config();
const app = express();

app.use(express.json());

const PORT = process.env.PORT || 5000;

// Start Express Server
app.listen(PORT, () => {
  console.log(`✅ Server running on port ${PORT}`);
});

// Start Telegram Bot
bot.launch().then(() => {
  console.log("✅ Telegram bot is running");
});
