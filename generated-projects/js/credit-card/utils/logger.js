/**
 * Simple logger utility
 */
const logger = {
  /**
   * Log info message
   * @param {string} message - Message to log
   * @param {Object} [data] - Optional data to log
   */
  info: (message, data) => {
    console.log(`[INFO] ${message}`, data ? data : '');
  },
  
  /**
   * Log error message
   * @param {string} message - Message to log
   * @param {Error|Object} [error] - Optional error or data to log
   */
  error: (message, error) => {
    console.error(`[ERROR] ${message}`, error ? (error.stack || error) : '');
  },
  
  /**
   * Log warning message
   * @param {string} message - Message to log
   * @param {Object} [data] - Optional data to log
   */
  warn: (message, data) => {
    console.warn(`[WARN] ${message}`, data ? data : '');
  },
  
  /**
   * Log debug message (only in development)
   * @param {string} message - Message to log
   * @param {Object} [data] - Optional data to log
   */
  debug: (message, data) => {
    if (process.env.NODE_ENV === 'development') {
      console.debug(`[DEBUG] ${message}`, data ? data : '');
    }
  }
};

module.exports = logger;