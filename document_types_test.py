#!/usr/bin/env python3
"""
Test all document types for comprehensive coverage
"""

import requests
import json

def test_all_document_types():
    base_url = "https://smartnexus-1.preview.emergentagent.com/api"
    
    document_types = [
        {
            "type": "contract",
            "title": "Software Development Contract",
            "client_name": "TechStart Inc",
            "variables": {
                "project_scope": "Custom web application development with React and Node.js",
                "contract_value": "150000",
                "duration": "6 months",
                "deliverables": "Web application, mobile app, API documentation, testing"
            }
        },
        {
            "type": "marketing",
            "title": "Product Launch Marketing Campaign",
            "client_name": "InnovateNow Corp",
            "variables": {
                "product_name": "AI-Powered Analytics Platform",
                "target_audience": "Mid-market businesses and enterprise clients",
                "campaign_budget": "75000",
                "campaign_duration": "3 months"
            }
        },
        {
            "type": "report",
            "title": "Q4 Performance Analysis Report",
            "client_name": "Global Enterprises Ltd",
            "variables": {
                "report_focus": "Quarterly performance metrics and growth analysis",
                "key_metrics": "Revenue growth 23%, customer acquisition up 45%, efficiency improved 18%",
                "time_period": "Q4 2024"
            }
        }
    ]
    
    print("🔍 Testing All Document Types")
    print("=" * 50)
    
    results = []
    
    for doc_config in document_types:
        print(f"\n📄 Testing {doc_config['type'].title()} Generation...")
        
        try:
            response = requests.post(
                f"{base_url}/documents/generate",
                json=doc_config,
                headers={'Content-Type': 'application/json'},
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                content_length = len(data.get('content', ''))
                print(f"   ✅ SUCCESS - ID: {data.get('id', 'N/A')}")
                print(f"   ✅ Content Length: {content_length} characters")
                print(f"   ✅ Client: {data.get('client_name', 'N/A')}")
                results.append(True)
            else:
                print(f"   ❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results.append(False)
    
    print(f"\n📊 Summary: {sum(results)}/{len(results)} document types working")
    return all(results)

if __name__ == "__main__":
    success = test_all_document_types()
    print(f"\n{'🎉 ALL DOCUMENT TYPES WORKING!' if success else '⚠️ Some document types failed'}")