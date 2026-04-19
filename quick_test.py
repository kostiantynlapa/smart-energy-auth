#!/usr/bin/env python3
import sys
sys.path.insert(0, r'c:\d\kpi\4th course\2sem\диплом\smart-energy-auth')

import time
import urllib.request
import json

time.sleep(2)

try:
    # Test admin login
    data = json.dumps({
        "username": "admin",
        "password": "admin123",
        "totp_code": "000000"
    }).encode()
    
    req = urllib.request.Request(
        'http://localhost:8001/login',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())
        print(f"✅ LOGIN SUCCESS (status: {response.status})")
        print(f"   Token type: {result.get('token_type')}")
        print(f"   User: {result.get('user')}")
        token = result.get('access_token')
        
        # Test listing users
        req2 = urllib.request.Request(
            'http://localhost:8001/admin/users',
            headers={'Authorization': f'Bearer {token}'}
        )
        with urllib.request.urlopen(req2) as response2:
            users = json.loads(response2.read())
            print(f"✅ GET /admin/users SUCCESS - {len(users)} users found:")
            for user in users:
                print(f"   - {user['username']} (role: {user['role']})")
                
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
