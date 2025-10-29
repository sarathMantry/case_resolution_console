-- Migration: 001_core_tables
-- Core customer, card, and account tables

BEGIN;

CREATE TABLE customers (
    id VARCHAR(36) PRIMARY KEY,  -- UUID v4
    name VARCHAR(255) NOT NULL,
    email_masked VARCHAR(255) NOT NULL,
    kyc_level VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cards (
    id VARCHAR(36) PRIMARY KEY,  -- UUID v4
    customer_id VARCHAR(36) NOT NULL REFERENCES customers(id),
    last4 CHAR(4) NOT NULL,
    network VARCHAR(20) NOT NULL,  -- VISA, MASTERCARD, etc
    status VARCHAR(20) NOT NULL,   -- ACTIVE, FROZEN, CLOSED
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Indexes
    CONSTRAINT cards_customer_id_fk FOREIGN KEY (customer_id) 
        REFERENCES customers(id) ON DELETE CASCADE
);

CREATE INDEX idx_cards_customer_id ON cards(customer_id);
CREATE INDEX idx_cards_status ON cards(status);

CREATE TABLE accounts (
    id VARCHAR(36) PRIMARY KEY,  -- UUID v4
    customer_id VARCHAR(36) NOT NULL REFERENCES customers(id),
    balance_cents BIGINT NOT NULL,  -- Store amounts in cents to avoid float precision issues
    currency CHAR(3) NOT NULL,      -- ISO 4217 currency code
    -- Indexes and constraints
    CONSTRAINT accounts_customer_id_fk FOREIGN KEY (customer_id) 
        REFERENCES customers(id) ON DELETE CASCADE,
    CONSTRAINT accounts_currency_check CHECK (currency ~ '^[A-Z]{3}$')
);

CREATE INDEX idx_accounts_customer_id ON accounts(customer_id);
CREATE INDEX idx_accounts_currency ON accounts(currency);

COMMIT;
