import express from 'express';
import sqlite3 from 'sqlite3';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
app.use(express.json());

const __dirname = dirname(fileURLToPath(import.meta.url));
const dbPath = join(__dirname, '..', 'uptime_db');

// Initialize database
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Error opening database:', err);
    process.exit(1);
  }
  console.log('Connected to SQLite database');
  
  // Create services table if it doesn't exist
  db.run(`
    CREATE TABLE IF NOT EXISTS services (
      serviceId TEXT PRIMARY KEY,
      token TEXT NOT NULL,
      lastNotification DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);
});

// Register heartbeat endpoint
app.post('/heartbeat', (req, res) => {
  const { serviceId, token } = req.body;

  if (!serviceId || !token) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  db.run(
    `INSERT INTO services (serviceId, token, lastNotification) 
     VALUES (?, ?, CURRENT_TIMESTAMP)
     ON CONFLICT(serviceId) DO UPDATE SET 
     lastNotification = CURRENT_TIMESTAMP,
     token = ? 
     WHERE token = ?`,
    [serviceId, token, token, token],
    function(err) {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Internal server error' });
      }
      
      if (this.changes === 0) {
        return res.status(400).json({ error: 'Invalid token for existing service' });
      }
      
      res.status(200).json({ message: 'Heartbeat registered successfully' });
    }
  );
});

// Get services overview endpoint
app.post('/services', (req, res) => {
  const { token } = req.body;

  if (!token) {
    return res.status(400).json({ error: 'Token is required' });
  }

  db.all(
    `SELECT serviceId, lastNotification 
     FROM services 
     WHERE token = ?`,
    [token],
    (err, rows) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Internal server error' });
      }
      
      res.status(200).json(rows);
    }
  );
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});