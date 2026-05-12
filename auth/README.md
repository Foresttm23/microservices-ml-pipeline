# Auth Service

Auth service with rotating refresh tokens and JWT access tokens.

## Endpoints

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`

## Environment

- `PORT`
- `DB_HOST`
- `DB_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ISSUER`
- `JWT_AUDIENCE`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS`
- `JWT_LEEWAY_SECONDS`
