# test_azure_connection.py
"""
Standalone script to test Azure OpenAI connection
Run this to verify your credentials work correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test Azure OpenAI connection with minimal setup"""
    
    # Get credentials
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    print("Configuration:")
    print(f"  Endpoint: {endpoint}")
    print(f"  API Version: {api_version}")
    print(f"  Deployment: {deployment}")
    print(f"  API Key: {'Set' if api_key else 'Not set'}")
    print()
    
    if not all([api_key, endpoint, api_version, deployment]):
        print("❌ Missing required environment variables!")
        return False
    
    # Method 1: Try with temporary proxy removal
    print("Method 1: Testing with proxy variables temporarily removed...")
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                  'NO_PROXY', 'no_proxy', 'ALL_PROXY', 'all_proxy']
    saved_proxies = {}
    for var in proxy_vars:
        if var in os.environ:
            saved_proxies[var] = os.environ.pop(var)
            print(f"  Temporarily removed {var}")
    
    try:
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        
        # Make a test call
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": "Say 'Hello, RBAC system is connected!'"}],
            max_tokens=20
        )
        
        print(f"✅ Success! Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Method 1 failed: {str(e)}")
        
    finally:
        # Restore proxy variables
        for var, value in saved_proxies.items():
            os.environ[var] = value
    
    # Method 2: Try with httpx client directly
    print("\nMethod 2: Testing with direct httpx client...")
    try:
        import httpx
        from openai import AzureOpenAI
        
        # Create custom httpx client without proxy
        http_client = httpx.Client(
            trust_env=False,  # Ignore proxy environment variables
        )
        
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint,
            http_client=http_client
        )
        
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": "Say 'Hello, RBAC system is connected!'"}],
            max_tokens=20
        )
        
        print(f"✅ Success! Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Method 2 failed: {str(e)}")
    
    # Method 3: Try with requests directly (bypass OpenAI SDK)
    print("\nMethod 3: Testing with direct API call...")
    try:
        import requests
        import json
        
        url = f"{endpoint}openai/deployments/{deployment}/chat/completions?api-version={api_version}"
        headers = {
            "Content-Type": "application/json",
            "api-key": api_key
        }
        data = {
            "messages": [{"role": "user", "content": "Say 'Hello, RBAC system is connected!'"}],
            "max_tokens": 20
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ API returned status {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Method 3 failed: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("Testing Azure OpenAI Connection")
    print("=" * 50)
    
    success = test_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Connection test PASSED!")
        print("\nYour Azure OpenAI credentials are working correctly.")
        print("The issue might be with the OpenAI library version or proxy settings.")
        print("\nTry updating the OpenAI library:")
        print("  pip install --upgrade openai")
    else:
        print("❌ Connection test FAILED!")
        print("\nPlease check:")
        print("1. Your .env file has the correct credentials")
        print("2. Your Azure OpenAI resource is active")
        print("3. Your API key is valid")
        print("4. The deployment name 'gpt-4o' exists in your resource")