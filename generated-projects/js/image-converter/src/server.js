const express = require('express');
const multer = require('multer');
const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const os = require('os');

// Initialize Express app
const app = express();
const port = 3000;

// Configure multer for handling file uploads
const upload = multer({
  dest: os.tmpdir(),
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB limit per file
  }
});

// Helper function to validate target size format
function validateTargetSize(size) {
  const pattern = /^\d+x\d+$/;
  if (!pattern.test(size)) {
    throw new Error('Invalid target size format. Expected format: widthxheight (e.g., 500x500)');
  }
  return true;
}

// Helper function to clean up temporary files
async function cleanupFiles(files) {
  for (const file of files) {
    try {
      await fs.unlink(file.path);
    } catch (error) {
      console.error(`Error cleaning up file ${file.path}:`, error);
    }
  }
}

// Create GIF endpoint
app.post('/create-gif', upload.array('images'), async (req, res) => {
  try {
    // Validate required parameters
    if (!req.files || req.files.length === 0) {
      return res.status(400).json({ error: 'No images provided' });
    }

    const targetSize = req.body.targetSize;
    if (!targetSize) {
      return res.status(400).json({ error: 'Target size is required' });
    }

    try {
      validateTargetSize(targetSize);
    } catch (error) {
      return res.status(400).json({ error: error.message });
    }

    // Get optional parameters with defaults
    const delay = parseInt(req.body.delay) || 10;
    const appendReverted = req.body.appendReverted === 'true';

    // Create temporary output file path
    const outputPath = path.join(os.tmpdir(), `output-${Date.now()}.gif`);

    // Prepare ImageMagick command
    let files = req.files.map(file => file.path);
    if (appendReverted) {
      files = [...files, ...files.slice().reverse()];
    }

    const convertCommand = [
      'convert',
      `-delay ${delay}`,
      `-resize ${targetSize}`,
      files.join(' '),
      outputPath
    ].join(' ');

    // Execute ImageMagick command
    exec(convertCommand, async (error) => {
      try {
        if (error) {
          throw new Error(`ImageMagick error: ${error.message}`);
        }

        // Read the generated GIF
        const gifBuffer = await fs.readFile(outputPath);

        // Set response headers
        res.setHeader('Content-Type', 'image/gif');
        res.setHeader('Content-Disposition', 'attachment; filename="output.gif"');

        // Send the GIF
        res.send(gifBuffer);

        // Clean up
        await cleanupFiles(req.files);
        await fs.unlink(outputPath);
      } catch (err) {
        res.status(500).json({ error: 'Error processing images: ' + err.message });
      }
    });
  } catch (error) {
    // Clean up on error
    if (req.files) {
      await cleanupFiles(req.files);
    }
    res.status(500).json({ error: 'Server error: ' + error.message });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something broke!' });
});

// Start server
app.listen(port, () => {
  console.log(`GIF converter server running at http://localhost:${port}`);
});