-- Migration: 006_fix_mcc_check
-- Fix transactions.mcc check constraint to use a Postgres-compatible digit class

BEGIN;

ALTER TABLE transactions
  DROP CONSTRAINT IF EXISTS transactions_mcc_check;

ALTER TABLE transactions
  ADD CONSTRAINT transactions_mcc_check
  CHECK (mcc ~ '^[0-9]{4}$');

COMMIT;
