# Credit Card Phone Association Service

A simple service for associating credit card numbers with phone numbers, following the OpenAPI specification.

## Features

- Associate credit cards with phone numbers
- Retrieve credit cards associated with multiple phone numbers
- Persistent storage with SQLite3
- Input validation for all API requests
- RESTful API endpoints

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)

### Installation

1. Clone the repository
2. Install dependencies
```bash
npm install
```
3. Create a `.env` file based on `.env.example`
```bash
cp .env.example .env
```

### Running the Service

Start the server:
```bash
npm start
```

For development (with auto-restart):
```bash
npm run dev
```

## API Documentation

### Associate Card

Associates a credit card with a phone number.

- **URL**: `/associate_card`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "credit_card": "4111111111111111",
    "phone": "+15551234567"
  }
  ```
- **Success Response**: `201 Created`
- **Error Response**: `400 Bad Request`

### Retrieve Cards

Retrieves all credit cards associated with ALL specified phone numbers.

- **URL**: `/retrieve_cards`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "phone_numbers": ["+15551234567", "+15557654321"]
  }
  ```
- **Success Response**:
  ```json
  {
    "card_numbers": ["4111111111111111"]
  }
  ```
- **Error Responses**:
  - `400 Bad Request`
  - `404 Not Found` (when no cards are associated with all phone numbers)

## Database Schema

- **credit_cards**: Stores credit card information
  - `id`: Primary key
  - `card_number`: Credit card number (unique)
  - `created_at`: Timestamp of creation

- **phones**: Stores phone number information
  - `id`: Primary key
  - `phone_number`: Phone number (unique)
  - `created_at`: Timestamp of creation

- **card_phone_associations**: Junction table for card-phone associations
  - `id`: Primary key
  - `card_id`: Foreign key to credit_cards
  - `phone_id`: Foreign key to phones
  - `created_at`: Timestamp of creation