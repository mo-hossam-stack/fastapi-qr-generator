# QR Code Generator API (Backend)

## Setup

### Environment Variables

This project uses `pydantic-settings` for configuration. You **must** set sensitive environment variables; there are no hardcoded defaults for secrets in the codebase.

1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
2.  Edit `.env` and fill in your local credentials.
    - `POSTGRES_PASSWORD`: Check your local Docker or Postgres setup.
    - `JWT_SECRET_KEY`: Generate a secure random string (e.g., `openssl rand -hex 32`).

### Docker Compose

The `docker-compose.yml` retrieves configuration from your shell environment or `.env` file.

To start services:
```bash
# Ensure .env exists and is populated
docker-compose up -d
```

### Running Locally with uv

```bash
uv sync
uv run fastapi dev app/main.py
```
