const cardModel = require('../models/card');

/**
 * Associate a credit card with a phone number
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
const associateCard = async (req, res, next) => {
  try {
    const { credit_card, phone } = req.body;
    
    const result = await cardModel.createCardPhoneAssociation(credit_card, phone);
    
    if (result.success) {
      return res.status(201).json({ message: 'Association created successfully' });
    } else {
      return res.status(400).json({ error: result.error });
    }
  } catch (error) {
    next(error);
  }
};

/**
 * Retrieve cards associated with all given phone numbers
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
const retrieveCards = async (req, res, next) => {
  try {
    const { phone_numbers } = req.body;
    
    if (!Array.isArray(phone_numbers) || phone_numbers.length === 0) {
      return res.status(400).json({ error: 'Phone numbers must be provided as a non-empty array' });
    }
    
    const result = await cardModel.getCardsByPhoneNumbers(phone_numbers);
    
    if (result.success) {
      return res.status(200).json({ card_numbers: result.cards });
    } else if (result.notFound) {
      return res.status(404).json({ error: 'No credit cards found associated with all specified phone numbers' });
    } else {
      return res.status(400).json({ error: result.error });
    }
  } catch (error) {
    next(error);
  }
};

module.exports = {
  associateCard,
  retrieveCards
};