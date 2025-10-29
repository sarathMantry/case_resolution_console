-- Migration: 003_alerts_and_cases
-- Alerts, cases, and case events for fraud/dispute tracking

BEGIN;

CREATE TABLE alerts (
    id VARCHAR(36) PRIMARY KEY,  -- UUID v4
    customer_id VARCHAR(36) NOT NULL,
    suspect_txn_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    risk TEXT NOT NULL,          -- LOW, MEDIUM, HIGH
    status TEXT NOT NULL,        -- OPEN, IN_REVIEW, CLOSED etc
    -- Foreign keys
    CONSTRAINT alerts_customer_id_fk FOREIGN KEY (customer_id) 
        REFERENCES customers(id) ON DELETE CASCADE,
    CONSTRAINT alerts_suspect_txn_id_fk FOREIGN KEY (suspect_txn_id) 
        REFERENCES transactions(id) ON DELETE CASCADE,
    -- Constraints
    CONSTRAINT alerts_risk_check CHECK (risk IN ('LOW', 'MEDIUM', 'HIGH')),
    CONSTRAINT alerts_status_check CHECK (status IN ('OPEN', 'IN_REVIEW', 'CLOSED'))
);

CREATE INDEX idx_alerts_customer_id ON alerts(customer_id);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);

CREATE TABLE cases (
    id VARCHAR(36) PRIMARY KEY,  -- UUID v4
    customer_id VARCHAR(36) NOT NULL,
    txn_id VARCHAR(36),         -- Optional: might be general case not tied to txn
    type TEXT NOT NULL,         -- FRAUD, DISPUTE, CHARGEBACK etc
    status TEXT NOT NULL,       -- OPEN, IN_PROGRESS, RESOLVED etc
    reason_code TEXT NOT NULL,  -- Standardized reason codes
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Foreign keys
    CONSTRAINT cases_customer_id_fk FOREIGN KEY (customer_id) 
        REFERENCES customers(id) ON DELETE CASCADE,
    CONSTRAINT cases_txn_id_fk FOREIGN KEY (txn_id) 
        REFERENCES transactions(id) ON DELETE CASCADE
);

CREATE INDEX idx_cases_customer_id ON cases(customer_id);
CREATE INDEX idx_cases_txn_id ON cases(txn_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_created_at ON cases(created_at DESC);

CREATE TABLE case_events (
    id VARCHAR(36) PRIMARY KEY,  -- UUID v4
    case_id VARCHAR(36) NOT NULL,
    ts TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actor VARCHAR(255) NOT NULL,  -- user_id or system_id that performed action
    action TEXT NOT NULL,         -- FREEZE_CARD, OPEN_DISPUTE etc
    payload_json JSONB,           -- Redacted event details
    -- Foreign keys
    CONSTRAINT case_events_case_id_fk FOREIGN KEY (case_id) 
        REFERENCES cases(id) ON DELETE CASCADE
);

CREATE INDEX idx_case_events_case_id ON case_events(case_id);
CREATE INDEX idx_case_events_ts ON case_events(ts DESC);

COMMIT;
