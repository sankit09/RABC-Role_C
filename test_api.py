# test_api.py
"""
Quick test script to verify all API endpoints are working
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

def test_endpoints():
    """Test all API endpoints"""
    
    print("=" * 50)
    print("RBAC Role Mining API Test")
    print("=" * 50)
    
    # 1. Test health endpoint
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API Status: {data.get('status')}")
            print(f"   ✅ Azure OpenAI: {'Connected' if data.get('azure_openai_connected') else 'Disconnected'}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Test clusters endpoint
    print("\n2. Testing Clusters Endpoint...")
    try:
        response = requests.get(f"{API_BASE}/clusters/")
        if response.status_code == 200:
            clusters = response.json()
            print(f"   ✅ Found {len(clusters)} clusters")
            if clusters:
                print(f"   📋 Cluster IDs: {[c.get('cluster_id', 'unknown') for c in clusters]}")
        else:
            print(f"   ❌ Clusters endpoint failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Test single role generation
    print("\n3. Testing Single Role Generation...")
    try:
        response = requests.post(
            f"{API_BASE}/roles/generate",
            json={"cluster_id": "C01"}
        )
        if response.status_code == 200:
            role = response.json()
            print(f"   ✅ Generated role: {role.get('role_name', 'Unknown')}")
            print(f"   📊 Risk Level: {role.get('risk_level', 'Unknown')}")
        else:
            print(f"   ❌ Role generation failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 4. Test multiple role generation (enhanced)
    print("\n4. Testing Multiple Role Generation...")
    try:
        response = requests.post(
            f"{API_BASE}/roles/generate-multiple",
            json={"cluster_id": "C01"}
        )
        if response.status_code == 200:
            data = response.json()
            options = data.get('role_options', [])
            print(f"   ✅ Generated {len(options)} role options")
            for opt in options:
                print(f"   Option {opt.get('option_number')}: {opt.get('role_name')}")
            print(f"   📊 Risk Level: {data.get('risk_level', 'Unknown')}")
            print(f"   ⭐ Recommended: Option {data.get('recommended_option')}")
        else:
            print(f"   ❌ Multiple role generation failed: {response.status_code}")
            print(f"   Falling back to single generation...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 5. Test batch generation
    print("\n5. Testing Batch Generation...")
    try:
        response = requests.post(
            f"{API_BASE}/roles/generate/batch",
            json={"cluster_ids": ["C01", "C02"], "concurrent_limit": 2}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Processed {data.get('successful', 0)} clusters successfully")
            print(f"   ⏱️ Processing time: {data.get('processing_time', 0):.2f} seconds")
        else:
            print(f"   ❌ Batch generation failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_endpoints()    