#!/usr/bin/env python3
"""
Integration test script for Smart Energy Auth & Gateway system.

Tests the complete flow:
1. Register a user with 2FA
2. Login with TOTP
3. Query through API Gateway
4. Test RBAC denial
"""
import requests
import json
import time
from typing import Optional

# Service URLs
AUTH_SERVICE = "http://localhost:8001"
GATEWAY_SERVICE = "http://localhost:8000"

# ANSI colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{Colors.ENDC}\n")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def print_json(data, title: str = ""):
    """Pretty print JSON data."""
    if title:
        print(f"{Colors.OKBLUE}{title}:{Colors.ENDC}")
    print(json.dumps(data, indent=2))


def test_health_checks():
    """Test health endpoints."""
    print_section("1. Health Checks")
    
    try:
        auth_health = requests.get(f"{AUTH_SERVICE}/health")
        auth_health.raise_for_status()
        print_success(f"Auth Service: {auth_health.json()}")
    except Exception as e:
        print_error(f"Auth Service health check failed: {e}")
        return False
    
    try:
        gateway_health = requests.get(f"{GATEWAY_SERVICE}/health")
        gateway_health.raise_for_status()
        print_success(f"API Gateway: {gateway_health.json()}")
    except Exception as e:
        print_error(f"API Gateway health check failed: {e}")
        return False
    
    return True


def test_register_user():
    """Test user registration with 2FA setup."""
    print_section("2. User Registration with 2FA Setup")
    
    register_data = {
        "username": "testuser",
        "password": "TestPass123!",
        "allowed_storages": ["postgres", "mongodb"]
    }
    
    print_info(f"Registering user: {register_data['username']}")
    print_info(f"Allowed storages: {register_data['allowed_storages']}")
    
    try:
        response = requests.post(
            f"{AUTH_SERVICE}/register",
            json=register_data
        )
        response.raise_for_status()
        data = response.json()
        
        print_success("Registration successful!")
        print_info(f"QR Code (first 50 chars): {data['qr_code_base64'][:50]}...")
        print_info(f"TOTP Secret (backup): {Colors.WARNING}{data['totp_secret']}{Colors.ENDC}")
        print_info("⚠️  Save this TOTP secret for backup access!")
        
        return data['totp_secret']
    except requests.exceptions.HTTPError as e:
        print_error(f"Registration failed: {e.response.json()}")
        return None
    except Exception as e:
        print_error(f"Registration failed: {e}")
        return None


def generate_totp_code(secret: str) -> str:
    """Generate TOTP code from secret."""
    try:
        import pyotp
        totp = pyotp.TOTP(secret)
        code = totp.now()
        return code
    except ImportError:
        print_info("pyotp not available. Using test code.")
        return "000000"


def test_login(username: str, password: str, totp_secret: str) -> Optional[str]:
    """Test user login with TOTP."""
    print_section("3. User Login with TOTP Verification")
    
    # Generate TOTP code
    totp_code = generate_totp_code(totp_secret)
    
    login_data = {
        "username": username,
        "password": password,
        "totp_code": totp_code
    }
    
    print_info(f"Logging in user: {username}")
    print_info(f"TOTP Code: {totp_code} (valid for ~30 seconds)")
    
    try:
        response = requests.post(
            f"{AUTH_SERVICE}/login",
            json=login_data
        )
        response.raise_for_status()
        data = response.json()
        
        print_success("Login successful!")
        print_info(f"Token Type: {data['token_type']}")
        print_info(f"Expires In: {data['expires_in']} seconds")
        print_info(f"Access Token (first 50 chars): {data['access_token'][:50]}...")
        
        return data['access_token']
    except requests.exceptions.HTTPError as e:
        print_error(f"Login failed: {e.response.json()}")
        return None
    except Exception as e:
        print_error(f"Login failed: {e}")
        return None


def test_query_allowed(token: str, db_type: str = "postgres"):
    """Test query on allowed storage."""
    print_section("4. Gateway Query - Allowed Storage")
    
    query_data = {
        "db_type": db_type,
        "query": "SELECT * FROM users"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print_info(f"Querying allowed storage: {Colors.OKGREEN}{db_type}{Colors.ENDC}")
    
    try:
        response = requests.post(
            f"{GATEWAY_SERVICE}/query",
            json=query_data,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        
        print_success("Query successful!")
        print_json(data, "Response")
        return True
    except requests.exceptions.HTTPError as e:
        print_error(f"Query failed: {e.response.json()}")
        return False
    except Exception as e:
        print_error(f"Query failed: {e}")
        return False


def test_query_denied(token: str, db_type: str = "redis"):
    """Test query on denied storage (RBAC)."""
    print_section("5. Gateway Query - Denied Storage (RBAC Test)")
    
    query_data = {
        "db_type": db_type,
        "query": "GET key"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print_info(f"Attempting to query unauthorized storage: {Colors.WARNING}{db_type}{Colors.ENDC}")
    
    try:
        response = requests.post(
            f"{GATEWAY_SERVICE}/query",
            json=query_data,
            headers=headers
        )
        
        if response.status_code == 403:
            print_success("✓ Access correctly denied (403 Forbidden)")
            print_json(response.json(), "Response")
            return True
        else:
            print_error(f"Expected 403, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Test failed: {e}")
        return False


def test_invalid_token():
    """Test query with invalid token."""
    print_section("6. Gateway Query - Invalid Token (Auth Test)")
    
    query_data = {
        "db_type": "postgres",
        "query": "SELECT * FROM users"
    }
    
    headers = {
        "Authorization": "Bearer invalid.token.here",
        "Content-Type": "application/json"
    }
    
    print_info("Attempting query with invalid token")
    
    try:
        response = requests.post(
            f"{GATEWAY_SERVICE}/query",
            json=query_data,
            headers=headers
        )
        
        if response.status_code == 401:
            print_success("✓ Invalid token correctly rejected (401 Unauthorized)")
            print_json(response.json(), "Response")
            return True
        else:
            print_error(f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Test failed: {e}")
        return False


def test_missing_auth_header():
    """Test query without authorization header."""
    print_section("7. Gateway Query - Missing Authorization Header")
    
    query_data = {
        "db_type": "postgres",
        "query": "SELECT * FROM users"
    }
    
    print_info("Attempting query without Authorization header")
    
    try:
        response = requests.post(
            f"{GATEWAY_SERVICE}/query",
            json=query_data
        )
        
        if response.status_code == 401:
            print_success("✓ Missing auth header correctly rejected (401 Unauthorized)")
            print_json(response.json(), "Response")
            return True
        else:
            print_error(f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Smart Energy Auth & Gateway - Integration Test Suite     ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    results = []
    
    # Test 1: Health checks
    if not test_health_checks():
        print_error("Services are not running. Start them with:")
        print(f"  Terminal 1: uvicorn auth_service.main:app --port 8001")
        print(f"  Terminal 2: uvicorn gateway.main:app --port 8000")
        return
    
    # Test 2: Register user
    totp_secret = test_register_user()
    results.append(("Register User", totp_secret is not None))
    
    if not totp_secret:
        print_error("Cannot continue without user registration")
        return
    
    # Test 3: Login
    token = test_login("testuser", "TestPass123!", totp_secret)
    results.append(("Login with TOTP", token is not None))
    
    if not token:
        print_error("Cannot continue without valid token")
        return
    
    # Test 4: Query allowed storage
    results.append(("Query Allowed Storage", test_query_allowed(token, "postgres")))
    
    # Test 5: Query another allowed storage
    results.append(("Query Another Allowed Storage", test_query_allowed(token, "mongodb")))
    
    # Test 6: Query denied storage (RBAC)
    results.append(("RBAC - Deny Unauthorized Storage", test_query_denied(token, "redis")))
    
    # Test 7: Invalid token
    results.append(("Auth - Invalid Token", test_invalid_token()))
    
    # Test 8: Missing auth header
    results.append(("Auth - Missing Header", test_missing_auth_header()))
    
    # Summary
    print_section("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.OKGREEN}PASS{Colors.ENDC}" if result else f"{Colors.FAIL}FAIL{Colors.ENDC}"
        print(f"{status} - {test_name}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print(f"{Colors.OKGREEN}✓ All tests passed!{Colors.ENDC}\n")
    else:
        print(f"{Colors.WARNING}⚠ Some tests failed{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
