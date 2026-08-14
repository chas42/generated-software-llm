// Process Monitor API
// A service that accepts a filter criterion and returns a list of matching process IDs

const express = require('express');
const { exec } = require('child_process');
const app = express();
const PORT = 3000;

// Middleware to parse JSON request bodies
app.use(express.json());

/**
 * Utility function to execute system commands
 * @param {string} command - The command to execute
 * @returns {Promise<string>} - The command output
 */
function executeCommand(command) {
  return new Promise((resolve, reject) => {
    exec(command, (error, stdout, stderr) => {
      if (error) {
        reject(error);
        return;
      }
      if (stderr) {
        console.warn('Command stderr:', stderr);
      }
      resolve(stdout);
    });
  });
}

/**
 * Sanitize command input to prevent command injection
 * @param {string} input - The input to sanitize
 * @returns {string} - The sanitized input
 */
function sanitizeInput(input) {
  // Remove potentially dangerous characters
  return input.replace(/[;&|`$(){}[\]\\]/g, '');
}

/**
 * Main endpoint to retrieve processes matching a regex pattern
 */
app.post('/monitor/commands', async (req, res) => {
  try {
    const { filter_flags, command_regex } = req.body;
    
    // Validate required parameters
    if (!command_regex) {
      return res.status(400).json({
        code: 400,
        message: 'command_regex is required'
      });
    }
    
    // Sanitize inputs
    const sanitizedFlags = filter_flags ? sanitizeInput(filter_flags) : 'aux';
    let sanitizedRegex;
    
    try {
      // Validate the regex by creating a RegExp object
      sanitizedRegex = new RegExp(command_regex, 'i');
    } catch (e) {
      return res.status(400).json({
        code: 400,
        message: 'Invalid regular expression: ' + e.message
      });
    }
    
    // Execute the ps command with the provided flags
    console.log(`Executing: ps ${sanitizedFlags}`);
    const result = await executeCommand(`ps ${sanitizedFlags}`);
    
    // Parse the output
    const lines = result.split('\n').filter(line => line.trim() !== '');
    
    // Skip the header line(s)
    // The number of header lines can vary based on the flags used
    let headerLines = 1;
    if (sanitizedFlags.includes('f') || sanitizedFlags.includes('T')) {
      // Formats like 'f' or 'T' might have multiple header lines
      headerLines = lines.findIndex(line => /^\s*PID/.test(line)) + 1;
      headerLines = headerLines > 0 ? headerLines : 1;
    }
    
    const processLines = lines.slice(headerLines);
    
    // Filter processes by regex and map to the required format
    const processes = processLines
      .filter(line => sanitizedRegex.test(line))
      .map(line => {
        // Parse the PID from the line
        // The PID is typically the first or second column in ps output
        const parts = line.trim().split(/\s+/);
        let processId;
        
        // Different ps flags format the output differently
        // Try to intelligently extract the PID
        if (/^\d+$/.test(parts[0])) {
          processId = parseInt(parts[0], 10);
        } else if (/^\d+$/.test(parts[1])) {
          processId = parseInt(parts[1], 10);
        } else {
          // If we can't definitively identify the PID, make a best guess
          // Look for the first column that contains only digits
          processId = parseInt(parts.find(part => /^\d+$/.test(part)), 10);
        }
        
        return {
          processId,
          processString: line
        };
      })
      .filter(process => !isNaN(process.processId)); // Filter out any entries where we couldn't get a valid PID
    
    res.json(processes);
  } catch (err) {
    console.error('Error processing request:', err);
    res.status(500).json({
      code: 500,
      message: 'Internal server error: ' + err.message
    });
  }
});

// Basic root endpoint for API health check
app.get('/', (req, res) => {
  res.json({
    status: 'online',
    message: 'Process Monitor API is running',
    endpoints: [
      {
        path: '/monitor/commands',
        method: 'POST',
        description: 'Retrieve processes matching a regex pattern'
      }
    ]
  });
});

// 404 handler for undefined routes
app.use((req, res) => {
  res.status(404).json({
    code: 404,
    message: 'Endpoint not found'
  });
});

// Global error handler
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    code: 500,
    message: 'Internal server error'
  });
});

// Start the server
app.listen(PORT, () => {
  console.log(`
=======================================================
  Process Monitor API is running on port ${PORT}
  
  Available endpoints:
  
  POST /monitor/commands
    - Retrieve processes matching a regex pattern
    - Required body: { "command_regex": "your-regex" }
    - Optional body: { "filter_flags": "aux" }
    
  GET /
    - API health check
=======================================================
  `);
});