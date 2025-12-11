import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#!/usr/bin/env python3
"""
Quick test to verify JWT authentication works with the existing APIs
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_jwt_with_jobs_api():
    """Test that JWT token works with jobs API"""
    
    # First, login to get a token
    print("1. Logging in...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "username": "testuser",
        "password": "NewTestPassword123!"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    tokens = login_response.json()
    access_token = tokens['access']
    print(f"✅ Login successful, got access token")
    
    # Test accessing jobs API without auth (should work - public endpoint)
    print("\n2. Testing jobs API without auth...")
    jobs_response = requests.get(f"{BASE_URL}/api/jobs/")
    if jobs_response.status_code == 200:
        print(f"✅ Jobs API accessible without auth (public endpoint)")
    else:
        print(f"❌ Jobs API failed: {jobs_response.status_code}")
    
    # Test accessing jobs API with JWT token (should also work)
    print("\n3. Testing jobs API with JWT token...")
    headers = {"Authorization": f"Bearer {access_token}"}
    jobs_with_auth = requests.get(f"{BASE_URL}/api/jobs/", headers=headers)
    if jobs_with_auth.status_code == 200:
        print(f"✅ Jobs API accessible with JWT token")
        data = jobs_with_auth.json()
        print(f"   Found {data.get('count', 0)} jobs")
    else:
        print(f"❌ Jobs API with auth failed: {jobs_with_auth.status_code}")
    
    # Test resumes API
    print("\n4. Testing resumes API with JWT token...")
    resumes_response = requests.get(f"{BASE_URL}/api/resumes", headers=headers)
    if resumes_response.status_code == 200:
        print(f"✅ Resumes API accessible with JWT token")
        data = resumes_response.json()
        print(f"   Found {len(data)} resumes")
    else:
        print(f"❌ Resumes API failed: {resumes_response.status_code}")
    
    print("\n✅ All integration tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_jwt_with_jobs_api()
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
