# Auth Service

Auth service with rotating refresh tokens and JWT access tokens.

## Architecture

- **JWT Middleware**: Access token validation is handled by `JWTAuthMiddleware` (from shared package). The middleware
  extracts
  the token from the Authorization header, validates it, and sets `request.state.user_id` for authenticated requests.
- **Protected Endpoints**: The `/auth/me` endpoint requires authentication (user_id must be present in request state).
- **Public Endpoints**: `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout` are accessible without a valid
  access token.
- **Token Management**: The service handles token creation (access + refresh) and refresh token rotation with revocation
  tracking.

## Endpoints

- `POST /auth/register` - Public
- `POST /auth/login` - Public
- `POST /auth/refresh` - Public
- `POST /auth/logout` - Public
- `GET /auth/me` - Requires authentication

## Environment

**Server**:

- `PORT` (default: 8003)

**Database**:

- `DB_HOST` (default: localhost)
- `DB_PORT` (default: 5432)
- `POSTGRES_DB` (default: auth_db)
- `POSTGRES_USER` (default: ml_user)
- `POSTGRES_PASSWORD` (default: change_me_in_local_dev)

**JWT & Authentication**:

- `JWT_ENABLED` (default: true) - Enable/disable JWT middleware
- `JWT_SECRET_KEY` (default: dev-secret) - Secret for signing and validating tokens
- `JWT_ALGORITHM` (default: HS256) - Algorithm for token operations
- `JWT_ISSUER` (optional) - Expected token issuer
- `JWT_AUDIENCE` (optional) - Expected token audience
- `JWT_USER_ID_CLAIM` (default: sub) - Claim name for user ID
- `JWT_LEEWAY_SECONDS` (default: 0) - Clock skew tolerance
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (default: 60) - Access token TTL
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` (default: 14) - Refresh token TTL
- `JWT_PUBLIC_PATHS` - Routes that don't require authentication (auto-configured)
