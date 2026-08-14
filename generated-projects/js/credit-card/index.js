// Main entry point for the Credit Card Phone Association Service
const express = require('express');
const dotenv = require('dotenv');
const { initDatabase } = require('./db/init');

// Import routes
const cardRoutes = require('./routes/cardRoutes');
const errorHandler = require('./middleware/errorHandler');

// Load environment variables
dotenv.config();

// Initialize the app
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());

// Initialize database
initDatabase();

// Routes
app.use('/', cardRoutes);

// Error handling middleware
app.use(errorHandler);

// Start the server
app.listen(PORT, () => {
  console.log(`Credit Card Phone Association Service running on http://localhost:${PORT}`);
});