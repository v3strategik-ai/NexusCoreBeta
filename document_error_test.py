#!/usr/bin/env python3
"""
Test document generation error handling and edge cases
"""

import requests
import json

def test_error_handling():
    base_url = "https://ai-workforce-hub.preview.emergentagent.com/api"
    
    print("🔍 Testing Error Handling & Edge Cases")
    print("=" * 50)
    
    # Test 1: Invalid document type
    print("\n1. Testing Invalid Document Type...")
    invalid_type_data = {
        "title": "Test Document",
        "type": "invalid_type",
        "client_name": "Test Client"
    }
    
    try:
        response = requests.post(
            f"{base_url}/documents/generate",
            json=invalid_type_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 422:
            print("   ✅ Correctly rejected invalid document type")
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Empty title
    print("\n2. Testing Empty Title...")
    empty_title_data = {
        "title": "",
        "type": "proposal",
        "client_name": "Test Client"
    }
    
    try:
        response = requests.post(
            f"{base_url}/documents/generate",
            json=empty_title_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 422:
            print("   ✅ Correctly rejected empty title")
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Missing required fields
    print("\n3. Testing Missing Required Fields...")
    missing_fields_data = {
        "client_name": "Test Client"
        # Missing title and type
    }
    
    try:
        response = requests.post(
            f"{base_url}/documents/generate",
            json=missing_fields_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 422:
            print("   ✅ Correctly rejected missing required fields")
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Get non-existent document
    print("\n4. Testing Non-existent Document Retrieval...")
    try:
        response = requests.get(
            f"{base_url}/documents/non-existent-id",
            timeout=10
        )
        
        if response.status_code == 404:
            print("   ✅ Correctly returned 404 for non-existent document")
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Large variables payload
    print("\n5. Testing Large Variables Payload...")
    large_variables = {
        f"variable_{i}": f"This is a very long variable content that tests the system's ability to handle large amounts of data in the variables field. Variable number {i}." * 10
        for i in range(20)
    }
    
    large_payload_data = {
        "title": "Large Payload Test Document",
        "type": "report",
        "client_name": "Test Client",
        "variables": large_variables
    }
    
    try:
        response = requests.post(
            f"{base_url}/documents/generate",
            json=large_payload_data,
            headers={'Content-Type': 'application/json'},
            timeout=60  # Longer timeout for large payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Successfully handled large payload - Content: {len(data.get('content', ''))} chars")
        else:
            print(f"   ⚠️ Large payload failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_error_handling()