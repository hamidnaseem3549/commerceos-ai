# Security Policy

## API Keys

CommerceOS AI requires a Groq API key for LLM access. This key must **never** be committed to the repository.

- Store keys in `.env` (gitignored by default)
- Copy `.env.example` to `.env` and fill in your values
- If you accidentally commit a key, rotate it immediately

## Admin Access

The admin dashboard is protected by `ADMIN_PASSWORD` environment variable.

- No hardcoded fallback exists
- Default credentials are never shipped
- Change the password regularly in production

## Reporting a Vulnerability

If you discover a security issue, please open a [GitHub Issue](https://github.com/yourusername/commerceos-ai/issues)
with the label `security`. Do not post the details in public forums.

## Dependencies

We keep dependencies up to date. Run `pip-audit` regularly:

```bash
pip install pip-audit
pip-audit
```

## Data

- Seed data uses fictional customers and orders — no real PII
- SQLite database is local only; not exposed over the network
- In production, use PostgreSQL with encrypted connections
