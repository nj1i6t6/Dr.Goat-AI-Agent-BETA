# ADR 0004: Support PostgreSQL in production and SQLite for local development

## Background
Developers need a lightweight database during local iterations, while production environments require a robust RDBMS with advanced features (JSONB, indexing, migrations). Existing CI pipelines already provision SQLite for speed, but staging/production run on managed PostgreSQL.

## Decision
Use SQLite for local development and automated tests to keep setup fast. Target PostgreSQL as the canonical production database, ensuring all migrations and queries remain compatible with PostgreSQL features.

## Consequences
- **Positive**: Enables quick onboarding with minimal dependencies locally while leveraging PostgreSQL reliability in production. Developers can run full test suites without container orchestration.
- **Negative**: Requires vigilance to avoid SQLite-specific SQL quirks. Critical migrations must be validated against PostgreSQL before release.
