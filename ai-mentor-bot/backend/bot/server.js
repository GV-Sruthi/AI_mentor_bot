import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import { bot } from "./bot.js";
import { queryDatabase } from "./db.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Route to fetch all users
app.get("/users", async (req, res) => {
  try {
    const users = await queryDatabase("SELECT * FROM users");
    res.json(users);
  } catch (error) {
    res.status(500).json({ error: "Error fetching users" });
  }
});

// Route to fetch all messages
app.get("/messages", async (req, res) => {
  try {
    const messages = await queryDatabase("SELECT * FROM messages");
    res.json(messages);
  } catch (error) {
    res.status(500).json({ error: "Error fetching messages" });
  }
});

// Route to fetch user questions
app.get("/questions", async (req, res) => {
  try {
    const questions = await queryDatabase("SELECT * FROM questions");
    res.json(questions);
  } catch (error) {
    res.status(500).json({ error: "Error fetching questions" });
  }
});

// Start the bot and server
bot.launch().then(() => console.log("🤖 Bot started"));
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));