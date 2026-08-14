const express = require('express');
const router = express.Router();
const cardController = require('../controllers/cardController');
const { validateAssociateCard, validateRetrieveCards } = require('../middleware/validation');

/**
 * @route POST /associate_card
 * @description Create a new association of a credit card number with a phone number
 */
router.post('/associate_card', validateAssociateCard, cardController.associateCard);

/**
 * @route POST /retrieve_cards
 * @description Retrieve cards associated with a set of phone numbers
 */
router.post('/retrieve_cards', validateRetrieveCards, cardController.retrieveCards);

module.exports = router;