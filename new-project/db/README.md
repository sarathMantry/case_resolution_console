Database migrations and seeding utilities

This directory contains SQL migrations and a sample-data generator used to populate
the development PostgreSQL database for the case-resolution console project.

Files
- migrations/: SQL migration files (001-005)
- migrate.sh: small script to apply migrations in order using psql
- generate_sample_data.py: script to insert realistic-looking data using Faker
- seed_requirements.txt: Python packages required to run the generator

Quickstart
1. Start Postgres (e.g. via docker-compose in the repo root).
2. Export DATABASE_URL or create a .env file with DATABASE_URL set to your postgres DSN.
3. Apply migrations:
   ./migrate.sh "$DATABASE_URL"
4. Install seed deps: pip install -r seed_requirements.txt
5. Run generator (example):
   python generate_sample_data.py --db "$DATABASE_URL" --customers 10000 --tx-per-customer 200

Notes
- The generator uses bulk COPY/execute_values patterns for performance; to reach
  1M+ transactions run with larger batch sizes and on a tuned Postgres instance.
- Migrations are plain SQL files and are intended for demo use. For production,
  adopt Alembic or Flyway and remove the SQLAlchemy create_all fallback in the backend.
# Database Schema & Migrations

This directory contains PostgreSQL migrations for the case resolution system.

## Structure

- `migrations/` - Numbered SQL migration files
  - `001_core_tables.sql` - Customers, cards, accounts
  - `002_transactions.sql` - Transactions with indexes
  - `003_alerts_and_cases.sql` - Alerts, cases, case events
  - `004_triage_and_traces.sql` - Triage runs and agent traces
  - `005_kb_and_policies.sql` - Knowledge base and policy docs

## Key Design Decisions

1. **IDs**: Using UUID v4 strings for all primary keys for:
   - Distribution-friendly (future sharding)
   - No sequence blocking
   - Predictable storage/index size

2. **Timestamps**: Using `timestamptz` for all dates to:
   - Preserve timezone information
   - Support global deployment
   - Consistent sorting

3. **Money**: Storing amounts in cents (integers) to:
   - Avoid floating point precision issues
   - Consistent calculations
   - Storage efficiency

4. **Indexing Strategy**:
   - Required indexes from spec
   - Additional indexes for foreign keys
   - Full text search indexes for KB/policies
   - Covering indexes for common queries

5. **Constraints**:
   - Foreign key constraints with CASCADE delete
   - CHECK constraints for enums
   - Currency/country code format validation

## Running Migrations

From the project root:

```bash
# Local development
psql -h localhost -U zr_user -d case_resolution -f db/migrations/001_core_tables.sql
psql -h localhost -U zr_user -d case_resolution -f db/migrations/002_transactions.sql
# ... etc

# Or use the migrate.sh script
./db/migrate.sh
```

## Common Queries

See `queries/` directory for optimized versions of:
- Customer timeline with risk signals
- Transaction search by merchant/MCC
- Case audit log with redacted details
- Full text KB/policy search
