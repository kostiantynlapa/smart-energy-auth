#!/usr/bin/env python3
"""
Quick verification that admin interface is working.
Run this after starting the auth service.
"""
import requests
import json

API_BASE = "http://localhost:8001"

def test_admin_interface():
    print("="*60)
    print("Admin Interface Verification")
    print("="*60)
    
    # Step 1: Login as admin
    print("\n1. Testing admin login...")
    try:
        login_response = requests.post(
            f"{API_BASE}/login",
            json={
                "username": "admin",
                "password": "admin123",
                "totp_code": "000000"
            }
        )
        login_response.raise_for_status()
        data = login_response.json()
        token = data["access_token"]
        print("✅ Admin login successful")
        print(f"   Token: {token[:50]}...")
    except Exception as e:
        print(f"❌ Admin login failed: {e}")
        return
    
    # Step 2: List users
    print("\n2. Testing GET /admin/users...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/admin/users", headers=headers)
        response.raise_for_status()
        users = response.json()
        print(f"✅ Listed {len(users)} users:")
        for user in users:
            print(f"   - {user['username']} ({user['role']}) - Storages: {user['allowed_storages']}")
    except Exception as e:
        print(f"❌ List users failed: {e}")
        return
    
    # Step 3: Create a test user
    print("\n3. Testing POST /admin/users...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{API_BASE}/admin/users",
            headers=headers,
            json={
                "username": "testuser",
                "password": "TestPass123!",
                "role": "user",
                "allowed_storages": ["postgres", "mongodb"]
            }
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ User created: {result['username']} with role {result['role']}")
    except Exception as e:
        print(f"❌ Create user failed: {e}")
        return
    
    # Step 4: Update user storages
    print("\n4. Testing PATCH /admin/users/{username}/storages...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.patch(
            f"{API_BASE}/admin/users/testuser/storages",
            headers=headers,
            json={"allowed_storages": ["postgres", "s3", "hdfs"]}
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ Storages updated: {result['allowed_storages']}")
    except Exception as e:
        print(f"❌ Update storages failed: {e}")
        return
    
    # Step 5: Update user role
    print("\n5. Testing PATCH /admin/users/{username}/role...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.patch(
            f"{API_BASE}/admin/users/testuser/role",
            headers=headers,
            json={"role": "admin"}
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ Role updated: {result['username']} is now {result['role']}")
    except Exception as e:
        print(f"❌ Update role failed: {e}")
        return
    
    # Step 6: Test admin check (should fail for non-admin)
    print("\n6. Testing admin role enforcement...")
    try:
        # Create a regular user
        headers = {"Authorization": f"Bearer {token}"}
        requests.post(
            f"{API_BASE}/admin/users",
            headers=headers,
            json={
                "username": "regularuser",
                "password": "RegularPass123!",
                "role": "user",
                "allowed_storages": ["postgres"]
            }
        )
        
        # Try to login as regular user
        login_response = requests.post(
            f"{API_BASE}/login",
            json={
                "username": "regularuser",
                "password": "RegularPass123!",
                "totp_code": "000000"
            }
        )
        regular_token = login_response.json()["access_token"]
        
        # Try to access admin endpoint
        headers = {"Authorization": f"Bearer {regular_token}"}
        response = requests.get(f"{API_BASE}/admin/users", headers=headers)
        
        if response.status_code == 403:
            print("✅ Admin endpoint correctly blocked non-admin user (403)")
        else:
            print(f"❌ Expected 403, got {response.status_code}")
    except Exception as e:
        print(f"❌ Admin role enforcement test failed: {e}")
        return
    
    # Step 7: Test self-deletion prevention
    print("\n7. Testing self-deletion prevention...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(
            f"{API_BASE}/admin/users/admin",
            headers=headers
        )
        
        if response.status_code == 400:
            print("✅ Self-deletion correctly prevented (400)")
        else:
            print(f"❌ Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"❌ Self-deletion test failed: {e}")
        return
    
    # Step 8: Delete test user
    print("\n8. Testing DELETE /admin/users/{username}...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(
            f"{API_BASE}/admin/users/testuser",
            headers=headers
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ User deleted: {result['username']}")
    except Exception as e:
        print(f"❌ Delete user failed: {e}")
        return
    
    print("\n" + "="*60)
    print("✅ ALL ADMIN TESTS PASSED!")
    print("="*60)

if __name__ == "__main__":
    test_admin_interface()
