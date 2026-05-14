# Auth Service

FastAPI auth service that issues JWT access and refresh tokens, rotates refresh tokens, and exposes a protected
`/auth/me` endpoint.

## What This Service Does

- User registration and login
- JWT access + refresh token issuance
- Refresh token rotation and logout
- Protected user profile endpoint

## API Endpoints

Public:

- `POST /auth/register` - Create a user
- `POST /auth/login` - Authenticate and receive access + refresh tokens
- `POST /auth/refresh` - Rotate refresh token and receive new pair
- `POST /auth/logout` - Revoke refresh token

Protected:

- `GET /auth/me` - Requires a valid access token

## Runtime Behavior (from `auth/main.py`)

- **Lifespan**: initializes a shared async DB engine and closes it on shutdown.
- **Middleware stack**:
    - `JWTAuthMiddleware` for access token validation
    - `LoggingContextMiddleware` for request context
    - `ResponseLogMiddleware` for structured response logs
    - CORS is enabled for all origins

## Configuration

These are read by `auth/core/config.py`. Defaults below reflect `auth/.env` (Docker Compose); override for local dev.

Server:

- `PORT` (default: 8002)

Database:

- `DB_HOST` (default: auth-db)
- `DB_PORT` (default: 5432)
- `POSTGRES_DB` (default: auth_db)
- `POSTGRES_USER` (default: ml_user)
- `POSTGRES_PASSWORD` (default: change_me_in_local_dev)

JWT:

- `JWT_ENABLED` (default: true)
- `JWT_SECRET_KEY` (default: change_me)
- `JWT_ALGORITHM` (default: HS256)
- `JWT_ISSUER` (optional)
- `JWT_AUDIENCE` (optional)
- `JWT_USER_ID_CLAIM` (default: sub)
- `JWT_LEEWAY_SECONDS` (default: 0)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (default: 60)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` (default: 14)
- `JWT_PUBLIC_PATHS` (auto-configured)

Derived:

- `DATABASE_URL` is constructed from the DB variables above.

## Running The Service

Docker Compose:

```powershell
docker compose up auth
```

Local development:

```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:POSTGRES_DB = "auth_db"
$env:POSTGRES_USER = "ml_user"
$env:POSTGRES_PASSWORD = "change_me_in_local_dev"
$env:PORT = "8002"
uv run python -m auth.main
```

## Startup Script Notes

The container entrypoint `auth/start.sh` waits for Postgres, runs Alembic migrations, then starts the service:

```text
uv run alembic -c auth/alembic.ini upgrade head
uv run python -m auth.main
```
