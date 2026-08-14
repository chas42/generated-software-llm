const { getDbConnection } = require('../db/init');

/**
 * Create an association between a credit card and a phone number
 * @param {string} cardNumber - Credit card number
 * @param {string} phoneNumber - Phone number
 * @returns {Promise<Object>} - Result of the operation
 */
const createCardPhoneAssociation = (cardNumber, phoneNumber) => {
  return new Promise((resolve, reject) => {
    const db = getDbConnection();
    
    // Begin transaction
    db.serialize(() => {
      db.run('BEGIN TRANSACTION');
      
      // Insert or get credit card
      db.run(
        'INSERT OR IGNORE INTO credit_cards (card_number) VALUES (?)',
        [cardNumber],
        function(err) {
          if (err) {
            db.run('ROLLBACK');
            db.close();
            return reject(err);
          }
          
          // Get the card ID
          db.get(
            'SELECT id FROM credit_cards WHERE card_number = ?',
            [cardNumber],
            (err, cardRow) => {
              if (err) {
                db.run('ROLLBACK');
                db.close();
                return reject(err);
              }
              
              const cardId = cardRow.id;
              
              // Insert or get phone
              db.run(
                'INSERT OR IGNORE INTO phones (phone_number) VALUES (?)',
                [phoneNumber],
                function(err) {
                  if (err) {
                    db.run('ROLLBACK');
                    db.close();
                    return reject(err);
                  }
                  
                  // Get the phone ID
                  db.get(
                    'SELECT id FROM phones WHERE phone_number = ?',
                    [phoneNumber],
                    (err, phoneRow) => {
                      if (err) {
                        db.run('ROLLBACK');
                        db.close();
                        return reject(err);
                      }
                      
                      const phoneId = phoneRow.id;
                      
                      // Create association
                      db.run(
                        'INSERT OR IGNORE INTO card_phone_associations (card_id, phone_id) VALUES (?, ?)',
                        [cardId, phoneId],
                        function(err) {
                          if (err) {
                            db.run('ROLLBACK');
                            db.close();
                            return reject(err);
                          }
                          
                          // Commit transaction
                          db.run('COMMIT', (err) => {
                            db.close();
                            
                            if (err) {
                              return reject(err);
                            }
                            
                            resolve({ success: true });
                          });
                        }
                      );
                    }
                  );
                }
              );
            }
          );
        }
      );
    });
  });
};

/**
 * Get credit cards associated with all specified phone numbers
 * @param {string[]} phoneNumbers - Array of phone numbers
 * @returns {Promise<Object>} - Result containing array of card numbers
 */
const getCardsByPhoneNumbers = (phoneNumbers) => {
  return new Promise((resolve, reject) => {
    const db = getDbConnection();
    
    // Construct placeholders for the SQL query
    const placeholders = phoneNumbers.map(() => '?').join(',');
    
    // SQL query to find cards associated with ALL specified phone numbers
    // It counts how many of the specified phone numbers are associated with each card
    // and only returns cards where the count matches the number of phone numbers provided
    const query = `
      SELECT cc.card_number
      FROM credit_cards cc
      JOIN card_phone_associations cpa ON cc.id = cpa.card_id
      JOIN phones p ON cpa.phone_id = p.id
      WHERE p.phone_number IN (${placeholders})
      GROUP BY cc.id
      HAVING COUNT(DISTINCT p.id) = ?
    `;
    
    // Execute query with phone numbers as parameters, plus the count at the end
    db.all(query, [...phoneNumbers, phoneNumbers.length], (err, rows) => {
      db.close();
      
      if (err) {
        return reject(err);
      }
      
      if (rows.length === 0) {
        return resolve({ 
          success: true, 
          notFound: true, 
          cards: [] 
        });
      }
      
      const cardNumbers = rows.map(row => row.card_number);
      resolve({ 
        success: true, 
        cards: cardNumbers 
      });
    });
  });
};

module.exports = {
  createCardPhoneAssociation,
  getCardsByPhoneNumbers
};