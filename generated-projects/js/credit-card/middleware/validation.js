/**
 * Validate credit card number (simple check for this example)
 * In a real app, you'd use a proper validation library and the Luhn algorithm
 * @param {string} cardNumber - Credit card number to validate
 * @returns {boolean} - Whether the card number is valid
 */
const isValidCreditCard = (cardNumber) => {
  // Simple validation for this example
  // Remove spaces and dashes
  const cleaned = cardNumber.replace(/[\s-]/g, '');
  
  // Check if it's all digits and has a valid length (13-19 digits)
  return /^\d{13,19}$/.test(cleaned);
};

/**
 * Validate phone number (simple check for this example)
 * In a real app, you'd use a proper phone validation library
 * @param {string} phoneNumber - Phone number to validate
 * @returns {boolean} - Whether the phone number is valid
 */
const isValidPhone = (phoneNumber) => {
  // Simple validation for this example
  // Allow digits, plus sign, parentheses, spaces, and dashes
  const cleaned = phoneNumber.replace(/[\s\-\(\)]/g, '');
  
  // Check if it starts with optional + and has 10-15 digits
  return /^\+?\d{10,15}$/.test(cleaned);
};

/**
 * Validate the associate card request
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
const validateAssociateCard = (req, res, next) => {
  const { credit_card, phone } = req.body;
  
  // Check if required fields are present
  if (!credit_card || !phone) {
    return res.status(400).json({ 
      error: 'Both credit_card and phone are required' 
    });
  }
  
  // Validate credit card format
  if (!isValidCreditCard(credit_card)) {
    return res.status(400).json({ 
      error: 'Invalid credit card format' 
    });
  }
  
  // Validate phone format
  if (!isValidPhone(phone)) {
    return res.status(400).json({ 
      error: 'Invalid phone number format' 
    });
  }
  
  next();
};

/**
 * Validate the retrieve cards request
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
const validateRetrieveCards = (req, res, next) => {
  const { phone_numbers } = req.body;
  
  // Check if phone_numbers array is present
  if (!phone_numbers) {
    return res.status(400).json({ 
      error: 'phone_numbers array is required' 
    });
  }
  
  // Check if phone_numbers is an array
  if (!Array.isArray(phone_numbers)) {
    return res.status(400).json({ 
      error: 'phone_numbers must be an array' 
    });
  }
  
  // Check if phone_numbers array is not empty
  if (phone_numbers.length === 0) {
    return res.status(400).json({ 
      error: 'phone_numbers array cannot be empty' 
    });
  }
  
  // Validate each phone number
  for (const phone of phone_numbers) {
    if (!isValidPhone(phone)) {
      return res.status(400).json({ 
        error: `Invalid phone number format: ${phone}` 
      });
    }
  }
  
  next();
};

module.exports = {
  validateAssociateCard,
  validateRetrieveCards
};