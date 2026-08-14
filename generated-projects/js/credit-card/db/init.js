const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

// Ensure db directory exists
const dbDir = path.join(__dirname, '..');
if (!fs.existsSync(path.join(dbDir, 'db'))) {
  fs.mkdirSync(path.join(dbDir, 'db'));
}

// Path to the database file
const dbPath = path.join(dbDir, 'uptime_db');

// Initialize database with tables
function initDatabase() {
  const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
      console.error('Error connecting to database:', err.message);
      return;
    }
    console.log('Connected to the SQLite database.');
  });

  // Create tables with foreign key support
  db.serialize(() => {
    // Enable foreign keys
    db.run('PRAGMA foreign_keys = ON');

    // Create credit_cards table
    db.run(`
      CREATE TABLE IF NOT EXISTS credit_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_number TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create phones table
    db.run(`
      CREATE TABLE IF NOT EXISTS phones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create association table (junction table)
    db.run(`
      CREATE TABLE IF NOT EXISTS card_phone_associations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_id INTEGER NOT NULL,
        phone_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (card_id) REFERENCES credit_cards (id) ON DELETE CASCADE,
        FOREIGN KEY (phone_id) REFERENCES phones (id) ON DELETE CASCADE,
        UNIQUE(card_id, phone_id)
      )
    `);
  });

  db.close((err) => {
    if (err) {
      console.error('Error closing database connection:', err.message);
    } else {
      console.log('Database initialized successfully.');
    }
  });
}

// Get database connection
function getDbConnection() {
  return new sqlite3.Database(dbPath, sqlite3.OPEN_READWRITE, (err) => {
    if (err) {
      console.error('Error connecting to database:', err.message);
    }
  });
}

module.exports = {
  initDatabase,
  getDbConnection
};