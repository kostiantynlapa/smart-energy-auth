# Smart Energy Authentication & Gateway System

Complete MVP implementation of authentication microservice + API Gateway for Smart Energy project.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Client Application                                          │
└──────────────┬──────────────────────────────────────────────┘
               │
               │ 1. POST /register (username, password, allowed_storages)
               │ Response: {qr_code_base64, totp_secret}
               ▼
    ┌──────────────────────────────┐
    │ AUTH SERVICE (port 8001)     │
    │ ├─ /register                 │
    │ ├─ /login                    │
    │ └─ /health                   │
    └──────────────┬───────────────┘
                   │ 2. POST /login (username, password, totp_code)
                   │ Response: {access_token, token_type, expires_in}
                   │
                   │ 3. Bearer token + POST /query request
                   ▼
    ┌──────────────────────────────┐
    │ API GATEWAY (port 8000)      │
    │ ├─ POST /query               │
    │ │  ├─ Validates JWT          │
    │ │  ├─ Checks RBAC            │
    │ │  └─ Routes to service      │
    │ ├─ /health                   │
    │ └─ /                          │
    └──────────────────────────────┘
                   │
                   ▼ Routes to actual services
    (PostgreSQL, MongoDB, etc.)
```

## Services

### 1. Authentication Service (Port 8001)

**Purpose**: User registration and JWT token generation with TOTP 2FA

**Endpoints**:

#### POST `/register`
Register a new user and setup TOTP for 2FA.

Request:
```json
{
  "username": "alice",
  "password": "SecurePass123!",
  "allowed_storages": ["postgres", "mongodb"]
}
```

Response:
```json
{
  "qr_code_base64": "iVBORw0KGgoAAAANSUhEUg...",
  "totp_secret": "JBSWY3DPEBLW64TMMQ======"
}
```

Steps:
1. User scans QR code with Google Authenticator app
2. Save the raw `totp_secret` as backup
3. User now has 2FA enabled

#### POST `/login`
Authenticate user with password + TOTP code to receive JWT.

Request:
```json
{
  "username": "alice",
  "password": "SecurePass123!",
  "totp_code": "123456"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**JWT Payload** (decoded):
```json
{
  "sub": "alice",
  "allowed_storages": ["postgres", "mongodb"],
  "exp": 1708367400
}
```

#### GET `/health`
Health check.

Response:
```json
{
  "status": "healthy"
}
```

---

### 2. API Gateway (Port 8000)

**Purpose**: Request routing with JWT validation and RBAC enforcement

**Endpoints**:

#### POST `/query`
Execute a query on a specific database with JWT authorization.

**Requirements**:
- Must include `Authorization: Bearer <JWT>` header
- Token must include `db_type` in `allowed_storages` claim

Request:
```bash
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "postgres",
    "query": "SELECT * FROM users"
  }'
```

Response (200 OK):
```json
{
  "result": "mock data from postgres",
  "source": "postgres",
  "message": "Query executed on postgres for user alice"
}
```

**Error Responses**:

1. **Missing Authorization Header** (401 Unauthorized):
```json
{
  "detail": "Missing Authorization header"
}
```

2. **Invalid Token Format** (401 Unauthorized):
```json
{
  "detail": "Invalid Authorization header format"
}
```

3. **Invalid/Expired Token** (401 Unauthorized):
```json
{
  "detail": "Invalid or expired token"
}
```

4. **User Not Allowed to Access Storage** (403 Forbidden):
```json
{
  "detail": "Access denied to storage: mongodb"
}
```

---

## Setup & Installation

### Prerequisites
- Python 3.12+
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt** includes:
- fastapi
- uvicorn
- passlib[bcrypt]
- pyotp
- python-jose[cryptography]
- qrcode[pil]
- python-dotenv
- pydantic
- pydantic-settings

### Configure Environment

Both services use `SECRET_KEY` from `.env` file:

**auth_service/.env**:
```env
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars-12345
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

**gateway/.env**:
```env
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars-12345
```

⚠️ **IMPORTANT**: Both must use the **same SECRET_KEY** for JWT validation!

---

## Running the Services

### Terminal 1: Start Auth Service (Port 8001)

```bash
cd smart-energy-auth
uvicorn auth_service.main:app --port 8001 --reload
```

Access Swagger UI: http://localhost:8001/docs

### Terminal 2: Start API Gateway (Port 8000)

```bash
cd smart-energy-auth
uvicorn gateway.main:app --port 8000 --reload
```

Access Swagger UI: http://localhost:8000/docs

---

## Complete Usage Example

### Step 1: Register User

```bash
curl -X POST http://localhost:8001/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "MySecurePass123!",
    "allowed_storages": ["postgres", "mongodb"]
  }'
```

**Response**:
```json
{
  "qr_code_base64": "iVBORw0KGgoAAAANSUhEUg...",
  "totp_secret": "JBSWY3DPEBLW64TMMQ======"
}
```

Save the `totp_secret` for backup. Scan QR code with Google Authenticator on your phone.

### Step 2: Get TOTP Code

In your authenticator app, you'll see a 6-digit code that refreshes every 30 seconds.

Example code: `123456`

### Step 3: Login to Get JWT

```bash
curl -X POST http://localhost:8001/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "MySecurePass123!",
    "totp_code": "123456"
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZSIsImFsbG93ZWRfc3RvcmFnZXMiOlsicG9zdGdyZXMiLCJtb25nb2RiIl0sImV4cCI6MTcwODM2NzQwMH0.vxX...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Step 4: Query via Gateway

Use the JWT token to make queries through the API Gateway:

```bash
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZSIsImFsbG93ZWRfc3RvcmFnZXMiOlsicG9zdGdyZXMiLCJtb25nb2RiIl0sImV4cCI6MTcwODM2NzQwMH0.vxX..." \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "postgres",
    "query": "SELECT * FROM users"
  }'
```

**Response**:
```json
{
  "result": "mock data from postgres",
  "source": "postgres",
  "message": "Query executed on postgres for user alice"
}
```

### Step 5: Test RBAC - Try Unauthorized Storage

User alice is only allowed `["postgres", "mongodb"]`. Try accessing `redis`:

```bash
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "redis"
  }'
```

**Response** (403 Forbidden):
```json
{
  "detail": "Access denied to storage: redis"
}
```

---

## Security Features

### Authentication
- ✅ Password hashing with bcrypt (salted, NIST-approved)
- ✅ TOTP 2FA with Google Authenticator support
- ✅ Time-based validation with ±30 second clock drift tolerance

### Authorization
- ✅ JWT-based stateless authentication
- ✅ Role-Based Access Control (RBAC) per storage system
- ✅ Token expiration (default 15 minutes)

### API Gateway
- ✅ Bearer token validation
- ✅ Generic error messages (no information leakage)
- ✅ Per-endpoint RBAC enforcement
- ✅ CORS enabled for MVP

### Best Practices
- ✅ Generic "Invalid credentials" message (prevents username enumeration)
- ✅ Secure token storage in JWT (no session state needed)
- ✅ Environment variable configuration (secrets not in code)

---

## File Structure

```
smart-energy-auth/
├── auth_service/
│   ├── __init__.py
│   ├── main.py                # Main FastAPI app
│   ├── models.py              # Pydantic schemas
│   ├── users_db.py            # In-memory storage
│   ├── config.py              # Settings
│   ├── .env                   # Environment config
│   └── utils/
│       ├── __init__.py
│       ├── password.py        # Bcrypt utilities
│       ├── totp.py            # TOTP generation/verification
│       └── jwt.py             # JWT creation/verification
│
├── gateway/
│   ├── __init__.py
│   ├── main.py                # API Gateway
│   └── .env                   # Environment config
│
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## Testing with Swagger UI

### Auth Service
Open http://localhost:8001/docs in your browser

1. Try `POST /register` with test data
2. Manually enter TOTP code from authenticator
3. Try `POST /login` with TOTP code
4. Copy the JWT token

### API Gateway
Open http://localhost:8000/docs in your browser

1. Click "Authorize" button (top right)
2. Enter JWT token as `Bearer <token>`
3. Try `POST /query` endpoint

---

## What's NOT Included (Next Phase)

- ❌ Real database (PostgreSQL, MongoDB)
- ❌ Refresh tokens
- ❌ Email verification
- ❌ Rate limiting
- ❌ Request logging/audit trail
- ❌ User profile endpoints
- ❌ Admin user management
- ❌ Multi-factor authentication beyond TOTP
- ❌ Token revocation (blacklist)

---

## Environment Variables Reference

### Auth Service (`auth_service/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| SECRET_KEY | (required) | Secret key for signing JWT tokens (min 32 chars) |
| ACCESS_TOKEN_EXPIRE_MINUTES | 15 | JWT expiration time in minutes |

### Gateway (`gateway/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| SECRET_KEY | (required) | Must match auth service for JWT validation |

---

## Troubleshooting

### "Port already in use"
The service is already running. Either:
1. Kill the existing process: `taskkill /PID <pid> /F` (Windows)
2. Use a different port: `uvicorn ... --port 8002`

### "Invalid or expired token"
- Token has expired (15 min default)
- SECRET_KEY mismatch between auth service and gateway
- Token was signed with different algorithm

### "Invalid credentials" on login
- Wrong username
- Wrong password
- Wrong TOTP code (check system time is synced)
- TOTP code expired (codes rotate every 30 seconds)

### "Access denied to storage"
- User's `allowed_storages` claim doesn't include requested `db_type`
- Register with the correct storages

---

## Production Deployment Checklist

- [ ] Use strong SECRET_KEY (generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] Set `ACCESS_TOKEN_EXPIRE_MINUTES` to appropriate value (5-60 min)
- [ ] Run without `--reload` flag
- [ ] Use production ASGI server (uvicorn with workers, Gunicorn)
- [ ] Enable HTTPS/TLS
- [ ] Replace in-memory storage with PostgreSQL
- [ ] Add request logging
- [ ] Enable rate limiting
- [ ] Set CORS origins to specific domains
- [ ] Add refresh token mechanism
- [ ] Implement token blacklist for logout
- [ ] Add audit logging for security events

---

## License

Part of Smart Energy project - MVP stage

---

## Support

For issues or questions, refer to the service endpoints documentation in Swagger UI:
- Auth Service: http://localhost:8001/docs
- API Gateway: http://localhost:8000/docs
