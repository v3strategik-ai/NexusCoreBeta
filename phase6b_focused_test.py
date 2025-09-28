#!/usr/bin/env python3
"""
Phase 6B Focused Testing - Test specific issues found
"""

import requests
import json
import time
from urllib.parse import quote

def test_workflow_execution_fix():
    """Test workflow execution with proper workflow activation"""
    base_url = "https://nexus-multimodel.preview.emergentagent.com/api"
    
    print("🔧 Testing Workflow Execution Fix...")
    
    # Step 1: Create workflow with active status
    workflow_data = {
        "name": "Active Test Workflow",
        "description": "Workflow with active status for execution testing",
        "status": "active",  # Explicitly set to active
        "trigger": {
            "type": "manual",
            "name": "Manual Trigger",
            "parameters": {}
        },
        "actions": [
            {
                "type": "notification",
                "name": "Test Notification",
                "parameters": {
                    "message": "Workflow executed successfully",
                    "type": "info"
                }
            }
        ],
        "created_by": "test_user",
        "category": "testing",
        "enabled": True
    }
    
    # Create workflow
    response = requests.post(f"{base_url}/workflow-engine/workflows", json=workflow_data)
    print(f"Create Workflow: {response.status_code}")
    
    if response.status_code == 200:
        workflow_id = response.json().get('workflow_id')
        print(f"Workflow ID: {workflow_id}")
        
        # Step 2: Try to execute the workflow
        execution_request = {
            "workflow_id": workflow_id,
            "context_data": {
                "test": "data",
                "lead": {"name": "Test Lead", "score": 85}
            },
            "triggered_by": "focused_test"
        }
        
        exec_response = requests.post(f"{base_url}/workflow-execution/execute", json=execution_request)
        print(f"Execute Workflow: {exec_response.status_code}")
        print(f"Response: {exec_response.text[:200]}")
        
        if exec_response.status_code == 200:
            execution_id = exec_response.json().get('execution_id')
            print(f"✅ Execution started: {execution_id}")
            
            # Check status
            time.sleep(2)
            status_response = requests.get(f"{base_url}/workflow-execution/status/{execution_id}")
            print(f"Status Check: {status_response.status_code}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"Execution Status: {status_data.get('status')}")
                return True
        else:
            print(f"❌ Execution failed: {exec_response.text}")
    
    return False

def test_nl_workflow_analyze_fix():
    """Test NL workflow analyze endpoint with correct parameters"""
    base_url = "https://nexus-multimodel.preview.emergentagent.com/api"
    
    print("\n🔧 Testing NL Workflow Analyze Fix...")
    
    # Test with query parameters (GET method)
    description = "When lead score exceeds 80, assign to senior sales rep"
    context = "High value enterprise leads"
    
    # URL encode the parameters
    encoded_desc = quote(description)
    encoded_context = quote(context)
    
    url = f"{base_url}/nl-workflows/analyze?description={encoded_desc}&context={encoded_context}"
    
    response = requests.get(url)
    print(f"GET Analyze: {response.status_code}")
    
    if response.status_code != 200:
        # Try POST method
        post_data = {
            "description": description,
            "context": context
        }
        
        response = requests.post(f"{base_url}/nl-workflows/analyze", json=post_data)
        print(f"POST Analyze: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        analysis = data.get('analysis', {})
        feasibility = data.get('feasibility')
        print(f"✅ Analysis successful - Feasibility: {feasibility}")
        if analysis:
            confidence = analysis.get('confidence', 0)
            workflow_name = analysis.get('workflow_name', 'Unknown')
            print(f"   Confidence: {confidence}, Name: {workflow_name}")
        return True
    else:
        print(f"❌ Analysis failed: {response.text[:200]}")
    
    return False

def test_nl_workflow_creation():
    """Test NL workflow creation with detailed output"""
    base_url = "https://nexus-multimodel.preview.emergentagent.com/api"
    
    print("\n🔧 Testing NL Workflow Creation...")
    
    nl_request = {
        "description": "When a new lead is created with high value, immediately assign to senior sales rep, send welcome email, wait 2 days, then send follow-up if no response",
        "context": "B2B SaaS platform for enterprise clients with deals over $25,000",
        "creator_id": "test_user_detailed"
    }
    
    response = requests.post(f"{base_url}/nl-workflows/create", json=nl_request, timeout=60)
    print(f"Create NL Workflow: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        workflow = data.get('workflow', {})
        confidence = data.get('confidence', 0)
        suggestions = data.get('suggestions', [])
        warnings = data.get('warnings', [])
        
        print(f"✅ NL Workflow created successfully")
        print(f"   AI Confidence: {confidence}")
        print(f"   Suggestions: {len(suggestions)}")
        print(f"   Warnings: {len(warnings)}")
        
        if workflow:
            name = workflow.get('name', 'Unknown')
            actions = workflow.get('actions', [])
            trigger = workflow.get('trigger', {})
            
            print(f"   Workflow Name: {name}")
            print(f"   Actions Count: {len(actions)}")
            print(f"   Trigger Type: {trigger.get('type', 'Unknown')}")
            
            # Show action details
            for i, action in enumerate(actions[:3], 1):  # Show first 3 actions
                action_type = action.get('type', 'unknown')
                action_name = action.get('name', 'Unknown')
                print(f"   Action {i}: {action_type} - {action_name}")
            
            if len(actions) >= 3 and confidence > 0.6:
                print("   🎉 High-quality AI workflow generation!")
                return True
            elif len(actions) >= 2:
                print("   ✅ Acceptable AI workflow generation")
                return True
            else:
                print("   ⚠️  AI workflow generation needs improvement")
        
    else:
        print(f"❌ NL Workflow creation failed: {response.text[:300]}")
    
    return False

def main():
    """Run focused Phase 6B tests"""
    print("🎯 Phase 6B Focused Issue Testing")
    print("="*50)
    
    results = []
    
    # Test workflow execution fix
    results.append(test_workflow_execution_fix())
    
    # Test NL workflow analyze fix
    results.append(test_nl_workflow_analyze_fix())
    
    # Test NL workflow creation
    results.append(test_nl_workflow_creation())
    
    print("\n" + "="*50)
    print("📊 FOCUSED TEST RESULTS")
    print("="*50)
    
    test_names = [
        "Workflow Execution Engine",
        "NL Workflow Analysis", 
        "NL Workflow Creation"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ FIXED" if result else "❌ STILL FAILING"
        print(f"   {name}: {status}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📈 IMPROVEMENT SUMMARY:")
    print(f"   Tests Fixed: {passed}/{total}")
    print(f"   Success Rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n🎉 ALL ISSUES RESOLVED!")
    elif passed >= total * 0.67:
        print("\n✅ SIGNIFICANT IMPROVEMENT!")
    else:
        print("\n⚠️  MORE WORK NEEDED")

if __name__ == "__main__":
    main()