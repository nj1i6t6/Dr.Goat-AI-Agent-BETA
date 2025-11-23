# ADR 0001: Choose Flask + SQLAlchemy for the backend stack

## Background
The project needs a Python-based web framework that integrates well with existing data science tooling, offers fine-grained control over request handling, and can be deployed within the current containerized infrastructure. Prior prototypes already used Flask blueprints, SQLAlchemy ORM models, and Alembic migrations.

## Decision
Continue building the backend with Flask 3, SQLAlchemy 2, and Alembic. Flask blueprints provide modular routing, SQLAlchemy manages persistence for PostgreSQL/SQLite targets, and Alembic supports repeatable schema evolution.

## Consequences
- **Positive**: Minimal learning curve for the team, compatibility with current code and tests, and straightforward integration with Redis-backed background workers.
- **Negative**: Requires disciplined structure to avoid monolithic views; lacks some batteries-included features found in opinionated frameworks, so conventions must be documented (see `AGENTS.md`).
