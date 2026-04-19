#!/bin/bash
# API Testing Examples - Smart Energy Auth & Gateway
# These are curl commands you can run from the terminal

echo "================================================"
echo "Smart Energy Auth & Gateway - API Testing"
echo "================================================"
echo ""
echo "Prerequisites: Both services must be running"
echo "  - Auth Service on port 8001"
echo "  - API Gateway on port 8000"
echo ""

# ============================================
# HEALTH CHECKS
# ============================================
echo "=== 1. HEALTH CHECKS ==="

echo ""
echo "Auth Service Health:"
curl -X GET http://localhost:8001/health | python -m json.tool

echo ""
echo "Gateway Service Health:"
curl -X GET http://localhost:8000/health | python -m json.tool

# ============================================
# USER REGISTRATION
# ============================================
echo ""
echo "=== 2. USER REGISTRATION ==="

REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8001/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "SecurePassword123!",
    "allowed_storages": ["postgres", "mongodb"]
  }')

echo "Register Response:"
echo "$REGISTER_RESPONSE" | python -m json.tool

# Extract TOTP secret for use in login
TOTP_SECRET=$(echo "$REGISTER_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['totp_secret'])")
echo "TOTP Secret (save for backup): $TOTP_SECRET"

# ============================================
# USER LOGIN
# ============================================
echo ""
echo "=== 3. USER LOGIN WITH TOTP ==="

# Note: You need to generate a valid TOTP code
# For testing, use: python -c "import pyotp; print(pyotp.TOTP('$TOTP_SECRET').now())"
# Or scan the QR code in Google Authenticator

echo ""
echo "To login, first generate a TOTP code:"
echo "  python -c \"import pyotp; print(pyotp.TOTP('$TOTP_SECRET').now())\""
echo ""
echo "Then replace TOTP_CODE in the following command:"
echo "  curl -X POST http://localhost:8001/login \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{"
echo "      \"username\": \"alice\","
echo "      \"password\": \"SecurePassword123!\","
echo "      \"totp_code\": \"TOTP_CODE\""
echo "    }'"

# If running in automated test, you might do:
# TOTP_CODE=$(python -c "import pyotp; print(pyotp.TOTP('$TOTP_SECRET').now())")

# ============================================
# GATEWAY QUERIES
# ============================================
echo ""
echo "=== 4. GATEWAY QUERIES ==="
echo ""
echo "First, get a valid JWT token from login (copy access_token)"
echo "Then test queries with the token:"
echo ""

# Example with placeholder token
TOKEN="<YOUR_JWT_TOKEN_HERE>"

echo "Query Allowed Storage (postgres):"
echo "curl -X POST http://localhost:8000/query \\"
echo "  -H \"Authorization: Bearer $TOKEN\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"db_type\": \"postgres\","
echo "    \"query\": \"SELECT * FROM users\""
echo "  }'"

echo ""
echo "Query Another Allowed Storage (mongodb):"
echo "curl -X POST http://localhost:8000/query \\"
echo "  -H \"Authorization: Bearer $TOKEN\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"db_type\": \"mongodb\","
echo "    \"query\": \"db.users.find({})\""
echo "  }'"

echo ""
echo "Query DENIED Storage (redis - RBAC test):"
echo "curl -X POST http://localhost:8000/query \\"
echo "  -H \"Authorization: Bearer $TOKEN\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"db_type\": \"redis\","
echo "    \"query\": \"GET key\""
echo "  }'"
echo "(Should return 403 Forbidden)"

echo ""
echo "Query with Invalid Token (auth test):"
echo "curl -X POST http://localhost:8000/query \\"
echo "  -H \"Authorization: Bearer invalid.token.here\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"db_type\": \"postgres\","
echo "    \"query\": \"SELECT * FROM users\""
echo "  }'"
echo "(Should return 401 Unauthorized)"

echo ""
echo "Query without Authorization Header (auth test):"
echo "curl -X POST http://localhost:8000/query \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"db_type\": \"postgres\","
echo "    \"query\": \"SELECT * FROM users\""
echo "  }'"
echo "(Should return 401 Unauthorized)"

# ============================================
# USEFUL FUNCTIONS
# ============================================
echo ""
echo "=== USEFUL FUNCTIONS ==="
echo ""

echo "Generate TOTP code from secret:"
echo "  python -c \"import pyotp; print(pyotp.TOTP('<TOTP_SECRET>').now())\""

echo ""
echo "Decode JWT token to see claims:"
echo "  python -c \"import json, base64; token='<JWT_TOKEN>'; parts=token.split('.'); payload=json.loads(base64.b64decode(parts[1]+'====')); print(json.dumps(payload, indent=2))\""

echo ""
echo "Pretty print JSON response:"
echo "  curl ... | python -m json.tool"

echo ""
echo "Save response to file:"
echo "  curl ... > response.json"

echo ""
echo "================================================"
