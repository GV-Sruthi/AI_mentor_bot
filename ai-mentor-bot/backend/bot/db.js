import mysql from "mysql2/promise";
import dotenv from "dotenv";

dotenv.config();

const pool = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
});

export async function queryDatabase(query, values = []) {
  try {
    const [rows] = await pool.execute(query, values);
    return rows;
  } catch (error) {
    console.error("Database query error:", error);
    throw error;
  }
}

export async function getUsers() {
  return queryDatabase("SELECT * FROM users");
}

export async function getMessages() {
  return queryDatabase("SELECT * FROM messages");
}

export async function getQuestions() {
  return queryDatabase("SELECT * FROM questions");
}
