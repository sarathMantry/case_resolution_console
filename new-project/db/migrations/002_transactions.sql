-- Migration: 002_transactions
-- Transactions table with required indexes for performance

BEGIN;

CREATE TABLE transactions (
    id VARCHAR(36) PRIMARY KEY,  -- UUID v4
    customer_id VARCHAR(36) NOT NULL,
    card_id VARCHAR(36) NOT NULL,
    mcc VARCHAR(4) NOT NULL,           -- Merchant Category Code
    merchant VARCHAR(255) NOT NULL,
    amount_cents BIGINT NOT NULL,      -- Store amounts in cents
    currency CHAR(3) NOT NULL,         -- ISO 4217
    ts TIMESTAMPTZ NOT NULL,           -- Transaction timestamp
    device_id VARCHAR(64),             -- Optional device identifier
    country CHAR(2) NOT NULL,          -- ISO 3166-1 alpha-2
    city VARCHAR(100),                 -- Optional city name
    -- Foreign keys
    CONSTRAINT transactions_customer_id_fk FOREIGN KEY (customer_id) 
        REFERENCES customers(id) ON DELETE CASCADE,
    CONSTRAINT transactions_card_id_fk FOREIGN KEY (card_id) 
        REFERENCES cards(id) ON DELETE CASCADE,
    -- Constraints
    CONSTRAINT transactions_currency_check CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT transactions_country_check CHECK (country ~ '^[A-Z]{2}$'),
    CONSTRAINT transactions_mcc_check CHECK (mcc ~ '^\\d{4}$')
);

-- Required indexes from spec:
-- (customer_id, ts DESC)
CREATE INDEX idx_transactions_customer_timeline ON transactions(customer_id, ts DESC);

-- (merchant)
CREATE INDEX idx_transactions_merchant ON transactions(merchant);

-- (mcc)
CREATE INDEX idx_transactions_mcc ON transactions(mcc);

-- (customer_id, merchant)
CREATE INDEX idx_transactions_customer_merchant ON transactions(customer_id, merchant);

-- Additional useful indexes:
CREATE INDEX idx_transactions_card_id ON transactions(card_id);
CREATE INDEX idx_transactions_currency ON transactions(currency);
CREATE INDEX idx_transactions_ts ON transactions(ts DESC);  -- For global timeline queries

COMMIT;
