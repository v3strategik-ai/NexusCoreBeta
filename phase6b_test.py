#!/usr/bin/env python3
"""
Phase 6B Workflow Systems Testing - Focused test for the 3 new workflow systems
"""

import requests
import sys
import json
from datetime import datetime

class Phase6BWorkflowTester:
    def __init__(self, base_url="https://smartagent-nexus.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, data: dict = None, timeout: int = 30) -> tuple:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timeout")
            self.failed_tests.append({'name': name, 'error': 'Timeout'})
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': name, 'error': str(e)})
            return False, {}

    def test_conditional_logic_builder(self):
        """Test Phase 6B Conditional Logic Builder endpoints"""
        print("\n" + "="*60)
        print("TESTING CONDITIONAL LOGIC BUILDER")
        print("="*60)
        
        results = []
        
        # Test 1: Get Available Condition Operators
        success1, operators_response = self.run_test("Get Condition Operators", "GET", "workflow-engine/conditions/operators")
        if success1:
            operators = operators_response.get('operators', [])
            data_types = operators_response.get('data_types', [])
            print(f"   Available Operators: {len(operators)}")
            print(f"   Data Types: {data_types}")
        results.append(success1)
        
        # Test 2: Test Individual Condition Evaluation
        test_condition = {
            "field": "lead.score",
            "operator": "greater_than",
            "value": 75,
            "data_type": "number"
        }
        
        test_context = {
            "lead": {
                "score": 85,
                "status": "hot",
                "value": 50000
            }
        }
        
        success2, condition_result = self.run_test(
            "Test Condition Evaluation", "POST", "workflow-engine/conditions/test", 200, 
            {"condition": test_condition, "context_data": test_context}
        )
        
        if success2:
            result = condition_result.get('condition_result')
            field_value = condition_result.get('field_value')
            print(f"   Condition Result: {result} (85 > 75)")
            if result == True and field_value == 85:
                print("   ✅ Condition evaluation working correctly")
        results.append(success2)
        
        # Test 3: Create Advanced Workflow
        workflow_data = {
            "name": "High-Value Lead Automation",
            "description": "Automated workflow for high-value leads",
            "trigger": {
                "type": "event_based",
                "name": "Lead Score Updated",
                "parameters": {"event": "lead_score_changed"},
                "conditions": [
                    {
                        "field": "lead.score",
                        "operator": "greater_than",
                        "value": 80,
                        "data_type": "number"
                    }
                ]
            },
            "actions": [
                {
                    "type": "assign_agent",
                    "name": "Assign Senior Sales Rep",
                    "parameters": {"agent_criteria": "senior_sales"}
                },
                {
                    "type": "send_email",
                    "name": "Send Personalized Email",
                    "parameters": {"template": "high_value_lead"}
                }
            ],
            "created_by": "test_user",
            "category": "lead_management"
        }
        
        success3, workflow_response = self.run_test(
            "Create Advanced Workflow", "POST", "workflow-engine/workflows", 200, workflow_data
        )
        
        workflow_id = None
        if success3:
            workflow_id = workflow_response.get('workflow_id')
            print(f"   Created Workflow ID: {workflow_id}")
        results.append(success3)
        
        # Test 4: Validate Workflow Logic
        success4 = True
        if workflow_id:
            success4, validation_result = self.run_test(
                "Validate Workflow Logic", "GET", f"workflow-engine/workflows/{workflow_id}/validate"
            )
            
            if success4:
                is_valid = validation_result.get('valid')
                action_count = validation_result.get('action_count', 0)
                print(f"   Workflow Valid: {is_valid}, Actions: {action_count}")
        results.append(success4)
        
        # Test 5: Scheduler Status
        success5, scheduler_status = self.run_test("Get Scheduler Status", "GET", "workflow-engine/triggers/scheduler/status")
        if success5:
            running = scheduler_status.get('running')
            print(f"   Scheduler Running: {running}")
        results.append(success5)
        
        passed = sum(results)
        total = len(results)
        print(f"\n📊 CONDITIONAL LOGIC BUILDER: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        return all(results)

    def test_workflow_execution_engine(self):
        """Test Phase 6B Workflow Execution Engine endpoints"""
        print("\n" + "="*60)
        print("TESTING WORKFLOW EXECUTION ENGINE")
        print("="*60)
        
        results = []
        
        # Test 1: Get Execution Engine Status
        success1, engine_status = self.run_test("Get Engine Status", "GET", "workflow-execution/engine/status")
        if success1:
            running = engine_status.get('running')
            active_executions = engine_status.get('active_executions', 0)
            print(f"   Engine Running: {running}, Active: {active_executions}")
        results.append(success1)
        
        # Test 2: Start Execution Engine
        success2, start_result = self.run_test("Start Execution Engine", "POST", "workflow-execution/engine/start")
        if success2:
            status = start_result.get('status')
            print(f"   Engine Status: {status}")
        results.append(success2)
        
        # Test 3: Create a simple workflow for execution testing
        simple_workflow = {
            "name": "Test Execution Workflow",
            "description": "Simple workflow for testing execution",
            "status": "active",  # Make sure workflow is active
            "trigger": {
                "type": "manual",
                "name": "Manual Trigger",
                "parameters": {}
            },
            "actions": [
                {
                    "type": "notification",
                    "name": "Send Test Notification",
                    "parameters": {
                        "message": "Test workflow executed",
                        "type": "info"
                    }
                }
            ],
            "created_by": "test_user",
            "category": "testing",
            "enabled": True  # Make sure workflow is enabled
        }
        
        success_create, create_response = self.run_test(
            "Create Test Workflow", "POST", "workflow-engine/workflows", 200, simple_workflow
        )
        
        execution_id = None
        workflow_id = None
        success3 = False
        
        if success_create:
            workflow_id = create_response.get('workflow_id')
            print(f"   Test Workflow Created: {workflow_id}")
            
            # Execute the workflow
            execution_request = {
                "workflow_id": workflow_id,
                "context_data": {
                    "lead": {"name": "Test Lead", "score": 75},
                    "trigger_source": "api_test"
                },
                "triggered_by": "phase6b_test"
            }
            
            success3, execution_response = self.run_test(
                "Execute Workflow", "POST", "workflow-execution/execute", 200, execution_request
            )
            
            if success3:
                execution_id = execution_response.get('execution_id')
                status = execution_response.get('status')
                print(f"   Execution ID: {execution_id}, Status: {status}")
        results.append(success3)
        
        # Test 4: Get Execution Status
        success4 = False
        if execution_id:
            import time
            time.sleep(2)  # Wait for execution to process
            
            success4, status_response = self.run_test(
                "Get Execution Status", "GET", f"workflow-execution/status/{execution_id}"
            )
            
            if success4:
                exec_status = status_response.get('status')
                print(f"   Execution Status: {exec_status}")
        results.append(success4)
        
        passed = sum(results)
        total = len(results)
        print(f"\n📊 WORKFLOW EXECUTION ENGINE: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        return all(results)

    def test_natural_language_workflows(self):
        """Test Phase 6B Natural Language Workflow Creation endpoints"""
        print("\n" + "="*60)
        print("TESTING NATURAL LANGUAGE WORKFLOW CREATION")
        print("="*60)
        
        results = []
        
        # Test 1: Get Workflow Templates
        success1, templates_response = self.run_test("Get Workflow Templates", "GET", "nl-workflows/templates")
        if success1:
            templates = templates_response.get('templates', [])
            categories = templates_response.get('categories', [])
            print(f"   Templates: {len(templates)}, Categories: {len(categories)}")
        results.append(success1)
        
        # Test 2: Get NL Workflow Examples
        success2, examples_response = self.run_test("Get NL Examples", "GET", "nl-workflows/examples")
        if success2:
            examples = examples_response.get('examples', [])
            tips = examples_response.get('tips', [])
            print(f"   Example Categories: {len(examples)}, Tips: {len(tips)}")
        results.append(success2)
        
        # Test 3: Analyze Workflow Description
        test_description = "When a lead's score exceeds 80, assign them to our best sales rep and send a follow-up email"
        
        success3, analysis_response = self.run_test(
            "Analyze Workflow Description", "POST", "nl-workflows/analyze", 200,
            {"description": test_description, "context": "High-value enterprise leads"}
        )
        
        if success3:
            analysis = analysis_response.get('analysis', {})
            feasibility = analysis_response.get('feasibility')
            print(f"   Feasibility: {feasibility}")
            if analysis and 'workflow_name' in analysis:
                confidence = analysis.get('confidence', 0)
                actions_count = len(analysis.get('actions_analysis', []))
                print(f"   AI Confidence: {confidence}, Actions: {actions_count}")
        results.append(success3)
        
        # Test 4: Create Workflow from Natural Language (AI Integration Test)
        nl_request = {
            "description": "Send welcome email when new lead is created, wait 3 days, then send demo email if not converted",
            "context": "B2B SaaS leads from website",
            "creator_id": "test_user_nl"
        }
        
        success4, creation_response = self.run_test(
            "Create Workflow from NL", "POST", "nl-workflows/create", 200, nl_request, timeout=45
        )
        
        if success4:
            workflow = creation_response.get('workflow', {})
            confidence = creation_response.get('confidence', 0)
            print(f"   AI Confidence: {confidence}")
            
            if workflow:
                workflow_name = workflow.get('name')
                workflow_actions = workflow.get('actions', [])
                print(f"   Generated: {workflow_name}, Actions: {len(workflow_actions)}")
                
                if workflow_name and len(workflow_actions) >= 2:
                    print("   ✅ AI workflow generation successful")
                else:
                    print("   ⚠️  Generated workflow may be incomplete")
        else:
            print("   ❌ AI workflow creation failed - may be timeout or AI integration issue")
        results.append(success4)
        
        passed = sum(results)
        total = len(results)
        print(f"\n📊 NATURAL LANGUAGE WORKFLOWS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        # Special note about AI integration
        if success4:
            print("   🤖 AI Integration: WORKING - Emergent LLM key functional")
        else:
            print("   🤖 AI Integration: ISSUE - Check Emergent LLM key or timeout")
        
        return all(results)

    def run_phase6b_tests(self):
        """Run all Phase 6B workflow system tests"""
        print("🚀 Starting Phase 6B Workflow Systems Testing...")
        print(f"🌐 Base URL: {self.base_url}")
        print("="*80)
        
        # Run the three Phase 6B test suites
        test_results = {
            'conditional_logic': self.test_conditional_logic_builder(),
            'workflow_execution': self.test_workflow_execution_engine(),
            'nl_workflows': self.test_natural_language_workflows()
        }
        
        # Print final summary
        print("\n" + "="*80)
        print("🎯 PHASE 6B WORKFLOW SYSTEMS TEST RESULTS")
        print("="*80)
        
        for system, result in test_results.items():
            status = "✅ WORKING" if result else "❌ FAILED"
            print(f"   {system.upper().replace('_', ' ')}: {status}")
        
        passed_systems = sum(1 for result in test_results.values() if result)
        total_systems = len(test_results)
        
        print(f"\n📊 OVERALL PHASE 6B RESULTS:")
        print(f"   Systems Tested: {total_systems}")
        print(f"   Systems Working: {passed_systems}")
        print(f"   Systems Failed: {total_systems - passed_systems}")
        print(f"   Success Rate: {(passed_systems/total_systems*100):.1f}%")
        
        print(f"\n🔍 API CALL STATISTICS:")
        print(f"   Total API Calls: {self.tests_run}")
        print(f"   Successful Calls: {self.tests_passed}")
        print(f"   Failed Calls: {self.tests_run - self.tests_passed}")
        print(f"   API Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for i, failed_test in enumerate(self.failed_tests[:5], 1):
                print(f"   {i}. {failed_test.get('name', 'Unknown')}")
                if 'error' in failed_test:
                    print(f"      Error: {failed_test['error']}")
        
        # Final verdict
        if passed_systems == total_systems:
            print(f"\n🎉 ALL PHASE 6B WORKFLOW SYSTEMS WORKING!")
        elif passed_systems >= 2:
            print(f"\n✅ MOSTLY SUCCESSFUL! {passed_systems}/{total_systems} systems working.")
        else:
            print(f"\n⚠️  NEEDS ATTENTION! Only {passed_systems}/{total_systems} systems working.")
        
        print("="*80)
        return passed_systems == total_systems

def main():
    """Main test execution"""
    tester = Phase6BWorkflowTester()
    success = tester.run_phase6b_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())