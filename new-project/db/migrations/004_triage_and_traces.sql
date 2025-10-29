-- Migration: 004_triage_and_traces
-- Triage runs and agent execution traces

BEGIN;

CREATE TABLE triage_runs (
    id VARCHAR(36) PRIMARY KEY,  -- UUID v4
    alert_id VARCHAR(36) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ,        -- NULL until completed
    risk TEXT NOT NULL,          -- LOW, MEDIUM, HIGH
    reasons JSONB NOT NULL,      -- Array of reason objects
    fallback_used BOOLEAN NOT NULL DEFAULT FALSE,
    latency_ms INTEGER,          -- NULL until completed
    -- Foreign keys
    CONSTRAINT triage_runs_alert_id_fk FOREIGN KEY (alert_id) 
        REFERENCES alerts(id) ON DELETE CASCADE,
    -- Constraints
    CONSTRAINT triage_runs_risk_check CHECK (risk IN ('LOW', 'MEDIUM', 'HIGH')),
    CONSTRAINT triage_runs_latency_check CHECK (latency_ms IS NULL OR latency_ms >= 0)
);

CREATE INDEX idx_triage_runs_alert_id ON triage_runs(alert_id);
CREATE INDEX idx_triage_runs_started_at ON triage_runs(started_at DESC);

CREATE TABLE agent_traces (
    run_id VARCHAR(36) NOT NULL,
    seq INTEGER NOT NULL,        -- Order within the run
    step TEXT NOT NULL,         -- Name of the step/tool
    ok BOOLEAN NOT NULL,        -- Success/failure
    duration_ms INTEGER NOT NULL,
    detail_json JSONB,          -- Redacted response/error details
    -- Primary key
    PRIMARY KEY (run_id, seq),
    -- Foreign keys
    CONSTRAINT agent_traces_run_id_fk FOREIGN KEY (run_id) 
        REFERENCES triage_runs(id) ON DELETE CASCADE,
    -- Constraints
    CONSTRAINT agent_traces_duration_check CHECK (duration_ms >= 0)
);

CREATE INDEX idx_agent_traces_run_step ON agent_traces(run_id, step);

COMMIT;
