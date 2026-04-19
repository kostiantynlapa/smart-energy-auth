import requests
import pyotp
import json

# Register and login flow
print("=" * 60)
print("Testing Smart Energy Auth & Gateway")
print("=" * 60)

# Step 1: Register user
print("\n1. Registering user 'testuser2'...")
register_response = requests.post(
    "http://localhost:8001/register",
    json={
        "username": "testuser2",
        "password": "Test123!",
        "allowed_storages": ["postgres", "mongodb"]
    }
)
if register_response.status_code == 200:
    register_data = register_response.json()
    totp_secret = register_data["totp_secret"]
    print(f"✓ User registered!")
    print(f"  TOTP Secret: {totp_secret}")
else:
    print(f"✗ Registration failed: {register_response.text}")
    exit(1)

# Step 2: Get TOTP code
print("\n2. Generating TOTP code...")
totp = pyotp.TOTP(totp_secret)
totp_code = totp.now()
print(f"✓ TOTP code generated: {totp_code}")

# Step 3: Login
print("\n3. Logging in...")
login_response = requests.post(
    "http://localhost:8001/login",
    json={
        "username": "testuser2",
        "password": "Test123!",
        "totp_code": totp_code
    }
)
if login_response.status_code == 200:
    login_data = login_response.json()
    token = login_data["access_token"]
    print(f"✓ Login successful!")
    print(f"  Token: {token}")
else:
    print(f"✗ Login failed: {login_response.text}")
    exit(1)

# Step 4: Query via Gateway
print("\n4. Testing gateway /query endpoint...")
gateway_response = requests.post(
    "http://localhost:8000/query",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={
        "db_type": "postgres",
        "query": "SELECT * FROM users"
    }
)
if gateway_response.status_code == 200:
    query_data = gateway_response.json()
    print(f"✓ Query successful!")
    print(f"  Response: {json.dumps(query_data, indent=2)}")
else:
    print(f"✗ Query failed: {gateway_response.text}")
    print(f"  Status code: {gateway_response.status_code}")
    exit(1)

print("\n" + "=" * 60)
print("✓ All tests passed! Services are working correctly.")
print("=" * 60)
