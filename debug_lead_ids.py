#!/usr/bin/env python3
"""
Debug Lead IDs to understand the ObjectId conversion issue
"""

import requests
import json

def debug_lead_ids():
    base_url = "https://smartagent-nexus.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Get leads
    print("🔍 Getting leads from CRM...")
    response = requests.get(f"{api_url}/crm/leads")
    
    if response.status_code == 200:
        leads_data = response.json()
        leads = leads_data.get('leads', [])
        
        print(f"Found {len(leads)} leads")
        
        for i, lead in enumerate(leads[:3]):
            lead_id = lead.get('id')
            lead_name = lead.get('name', 'Unknown')
            
            print(f"\nLead {i+1}: {lead_name}")
            print(f"  ID: {lead_id}")
            print(f"  ID Type: {type(lead_id)}")
            print(f"  ID Length: {len(str(lead_id))}")
            
            # Try to score this lead
            print(f"  Testing lead scoring...")
            scoring_data = {
                "lead_id": lead_id,
                "force_refresh": True
            }
            
            score_response = requests.post(
                f"{api_url}/lead-scoring/score", 
                json=scoring_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"  Scoring Status: {score_response.status_code}")
            if score_response.status_code != 200:
                print(f"  Error: {score_response.text[:200]}")
            else:
                score_data = score_response.json()
                print(f"  Score: {score_data.get('score', 'N/A')}")
    else:
        print(f"Failed to get leads: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    debug_lead_ids()