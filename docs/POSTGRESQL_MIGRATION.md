# PostgreSQL migration readiness

SQLite remains the verified local demo database. SQLAlchemy models use portable scalar types, JSON, foreign keys and named identifiers. Timestamps are currently ISO strings; migrating them to PostgreSQL `timestamptz` requires an explicit data migration. This is a reviewed migration plan, not a tested production PostgreSQL deployment.

## Driver and configuration

In a separate deployment environment install and pin `psycopg[binary]` for SQLAlchemy's synchronous psycopg driver. Use an ignored environment value such as `DATABASE_URL=postgresql+psycopg://jalayatra_user:REPLACE_PASSWORD@localhost:5432/jalayatra`. Use a secret manager, TLS where required, and a non-superuser application role. Do not put a real URL/password in Git. Add connection-pool sizing and health probes for the deployment's worker count.

## Migration sequence

1. Stop writes, back up SQLite including a consistent WAL checkpoint, and verify restoration. Export a synthetic copy for rehearsal; preserve IDs and foreign-key relationships.
2. Introduce Alembic in an isolated branch/environment. Import `backend.models` before assigning `Base.metadata` as target metadata. Generate and manually review an initial migration, indexes, FK delete policies and every unique constraint. `create_all` is not a versioned migration system.
3. Apply the reviewed migration to an empty PostgreSQL database. Import organizations/roles/users and network resources before dependent cargo, service, booking and execution records. Reset sequence values if numeric IDs are introduced. Convert JSON and timestamps explicitly; preserve nulls.
4. Compare row counts, ownership, references, booking snapshots, invoice sums, per-segment usage, contract holds, resource reservations and impact aggregates. Run all tests against a PostgreSQL test URL and rehearse the flagship workflow.
5. Add rollback/restore runbooks, backup retention, storage encryption, HTTPS, production identity, monitoring, audit retention and worker isolation before moving any real data.

## Concurrency boundary

SQLite reservations serialize with `BEGIN IMMEDIATE`. Existing PostgreSQL booking code locks cargo and vessel rows; this alone does **not** establish safe concurrent recurring contracts, fleet approvals, resources, OTP requests or imports. Before production, lock the relevant service/segment/contract/resource/preview rows in a consistent order. Use database-enforced uniqueness and exclusion constraints where appropriate; handle serialization/deadlock retries idempotently. Add simultaneous distinct-cargo resource/segment tests, concurrent contract draw tests, duplicate fleet approval tests and rollback tests against real PostgreSQL. Cross-worker application locks do not replace database isolation.

Alembic was intentionally not added to the working demo without a database rehearsal. No migration or switch of the hero database was performed.
