#!/usr/bin/env python3
"""
Final Phase 6B Testing - Comprehensive test with all fixes
"""

import requests
import json
import time
from urllib.parse import quote

class FinalPhase6BTester:
    def __init__(self):
        self.base_url = "https://nexus-multimodel.preview.emergentagent.com/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, test_func):
        """Run a test and track results"""
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            success = test_func()
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - {name}")
                return True
            else:
                print(f"❌ FAILED - {name}")
                self.failed_tests.append(name)
                return False
        except Exception as e:
            print(f"❌ ERROR - {name}: {str(e)}")
            self.failed_tests.append(f"{name} (Error: {str(e)})")
            return False

    def test_conditional_logic_builder(self):
        """Test Conditional Logic Builder system"""
        print("\n" + "="*60)
        print("TESTING CONDITIONAL LOGIC BUILDER")
        print("="*60)
        
        results = []
        
        # Test 1: Get operators
        def test_operators():
            response = requests.get(f"{self.base_url}/workflow-engine/conditions/operators")
            if response.status_code == 200:
                data = response.json()
                operators = data.get('operators', [])
                data_types = data.get('data_types', [])
                print(f"   Operators: {len(operators)}, Data Types: {len(data_types)}")
                return len(operators) >= 10 and len(data_types) >= 3
            return False
        
        results.append(self.run_test("Get Condition Operators", test_operators))
        
        # Test 2: Test condition evaluation
        def test_condition_eval():
            test_data = {
                "condition": {
                    "field": "lead.score",
                    "operator": "greater_than",
                    "value": 75,
                    "data_type": "number"
                },
                "context_data": {
                    "lead": {"score": 85, "status": "hot"}
                }
            }
            response = requests.post(f"{self.base_url}/workflow-engine/conditions/test", json=test_data)
            if response.status_code == 200:
                result = response.json().get('condition_result')
                field_value = response.json().get('field_value')
                print(f"   Condition: {field_value} > 75 = {result}")
                return result == True and field_value == 85
            return False
        
        results.append(self.run_test("Condition Evaluation", test_condition_eval))
        
        # Test 3: Create workflow with conditions
        def test_create_workflow():
            workflow_data = {
                "name": "Conditional Test Workflow",
                "description": "Workflow with conditional logic",
                "status": "active",
                "trigger": {
                    "type": "event_based",
                    "name": "Lead Score Change",
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
                        "name": "Assign Senior Rep",
                        "parameters": {"criteria": "senior_sales"},
                        "conditions": [
                            {
                                "field": "lead.value",
                                "operator": "greater_than",
                                "value": 25000,
                                "data_type": "number"
                            }
                        ]
                    }
                ],
                "created_by": "test_user",
                "category": "lead_management"
            }
            
            response = requests.post(f"{self.base_url}/workflow-engine/workflows", json=workflow_data)
            if response.status_code == 200:
                workflow_id = response.json().get('workflow_id')
                print(f"   Created Workflow: {workflow_id}")
                
                # Validate the workflow
                validate_response = requests.get(f"{self.base_url}/workflow-engine/workflows/{workflow_id}/validate")
                if validate_response.status_code == 200:
                    validation = validate_response.json()
                    is_valid = validation.get('valid')
                    condition_count = validation.get('condition_count', 0)
                    print(f"   Validation: Valid={is_valid}, Conditions={condition_count}")
                    return is_valid and condition_count >= 2
            return False
        
        results.append(self.run_test("Create Conditional Workflow", test_create_workflow))
        
        # Test 4: Scheduler status
        def test_scheduler():
            response = requests.get(f"{self.base_url}/workflow-engine/triggers/scheduler/status")
            if response.status_code == 200:
                data = response.json()
                running = data.get('running')
                schedules = data.get('supported_schedules', [])
                print(f"   Scheduler Running: {running}, Supported: {len(schedules)}")
                return isinstance(running, bool) and len(schedules) > 0
            return False
        
        results.append(self.run_test("Scheduler Status", test_scheduler))
        
        passed = sum(results)
        total = len(results)
        print(f"\n📊 CONDITIONAL LOGIC BUILDER: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        return all(results)

    def test_workflow_execution_engine(self):
        """Test Workflow Execution Engine system"""
        print("\n" + "="*60)
        print("TESTING WORKFLOW EXECUTION ENGINE")
        print("="*60)
        
        results = []
        
        # Test 1: Engine status
        def test_engine_status():
            response = requests.get(f"{self.base_url}/workflow-execution/engine/status")
            if response.status_code == 200:
                data = response.json()
                running = data.get('running')
                max_concurrent = data.get('max_concurrent', 0)
                print(f"   Engine Running: {running}, Max Concurrent: {max_concurrent}")
                return isinstance(running, bool) and max_concurrent > 0
            return False
        
        results.append(self.run_test("Engine Status", test_engine_status))
        
        # Test 2: Start engine
        def test_start_engine():
            response = requests.post(f"{self.base_url}/workflow-execution/engine/start")
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                print(f"   Engine Status: {status}")
                return status == "running"
            return False
        
        results.append(self.run_test("Start Engine", test_start_engine))
        
        # Test 3: Create and execute workflow
        def test_workflow_execution():
            # Create active workflow
            workflow_data = {
                "name": "Execution Test Workflow",
                "description": "Test workflow execution",
                "status": "active",  # Key: must be active
                "trigger": {
                    "type": "manual",
                    "name": "Manual Trigger"
                },
                "actions": [
                    {
                        "type": "notification",
                        "name": "Success Notification",
                        "parameters": {
                            "message": "Workflow executed: {{lead.name}}",
                            "type": "success"
                        }
                    },
                    {
                        "type": "wait_delay",
                        "name": "Short Wait",
                        "parameters": {"delay_minutes": 1}
                    }
                ],
                "created_by": "test_user",
                "enabled": True  # Key: must be enabled
            }
            
            create_response = requests.post(f"{self.base_url}/workflow-engine/workflows", json=workflow_data)
            if create_response.status_code != 200:
                return False
            
            workflow_id = create_response.json().get('workflow_id')
            print(f"   Created Active Workflow: {workflow_id}")
            
            # Execute workflow
            execution_request = {
                "workflow_id": workflow_id,
                "context_data": {
                    "lead": {
                        "name": "John Smith",
                        "email": "john@example.com",
                        "score": 85,
                        "value": 50000
                    },
                    "agent": {"id": "agent_123"},
                    "trigger_source": "final_test"
                },
                "triggered_by": "final_phase6b_test"
            }
            
            exec_response = requests.post(f"{self.base_url}/workflow-execution/execute", json=execution_request)
            if exec_response.status_code != 200:
                print(f"   Execution failed: {exec_response.text[:100]}")
                return False
            
            execution_id = exec_response.json().get('execution_id')
            status = exec_response.json().get('status')
            print(f"   Execution Started: {execution_id}, Status: {status}")
            
            # Check execution status
            time.sleep(3)  # Wait for processing
            status_response = requests.get(f"{self.base_url}/workflow-execution/status/{execution_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                exec_status = status_data.get('status')
                progress = status_data.get('progress', {})
                executed_actions = progress.get('executed_actions', 0)
                print(f"   Final Status: {exec_status}, Actions Executed: {executed_actions}")
                return exec_status in ['completed', 'running'] and execution_id is not None
            
            return False
        
        results.append(self.run_test("Workflow Execution", test_workflow_execution))
        
        # Test 4: Error handling
        def test_error_handling():
            # Try to execute non-existent workflow
            bad_request = {
                "workflow_id": "non-existent-workflow",
                "context_data": {},
                "triggered_by": "error_test"
            }
            
            response = requests.post(f"{self.base_url}/workflow-execution/execute", json=bad_request)
            # Should return error (500 or 404)
            if response.status_code in [404, 500]:
                print(f"   Error handling working: {response.status_code}")
                return True
            return False
        
        results.append(self.run_test("Error Handling", test_error_handling))
        
        passed = sum(results)
        total = len(results)
        print(f"\n📊 WORKFLOW EXECUTION ENGINE: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        return all(results)

    def test_natural_language_workflows(self):
        """Test Natural Language Workflow Creation system"""
        print("\n" + "="*60)
        print("TESTING NATURAL LANGUAGE WORKFLOW CREATION")
        print("="*60)
        
        results = []
        
        # Test 1: Get templates
        def test_templates():
            response = requests.get(f"{self.base_url}/nl-workflows/templates")
            if response.status_code == 200:
                data = response.json()
                templates = data.get('templates', [])
                categories = data.get('categories', [])
                print(f"   Templates: {len(templates)}, Categories: {len(categories)}")
                return len(templates) >= 3 and len(categories) >= 3
            return False
        
        results.append(self.run_test("Get Templates", test_templates))
        
        # Test 2: Get examples
        def test_examples():
            response = requests.get(f"{self.base_url}/nl-workflows/examples")
            if response.status_code == 200:
                data = response.json()
                examples = data.get('examples', [])
                tips = data.get('tips', [])
                common_triggers = data.get('common_triggers', [])
                print(f"   Examples: {len(examples)}, Tips: {len(tips)}, Triggers: {len(common_triggers)}")
                return len(examples) >= 3 and len(tips) >= 3
            return False
        
        results.append(self.run_test("Get Examples", test_examples))
        
        # Test 3: Analyze description (using query parameters)
        def test_analyze():
            description = "When lead score exceeds 80, assign to senior sales rep and send personalized email"
            context = "High-value enterprise leads"
            
            # Use query parameters as the endpoint expects
            url = f"{self.base_url}/nl-workflows/analyze?description={quote(description)}&context={quote(context)}"
            response = requests.post(url)
            
            if response.status_code == 200:
                data = response.json()
                analysis = data.get('analysis', {})
                feasibility = data.get('feasibility')
                print(f"   Feasibility: {feasibility}")
                
                if analysis:
                    confidence = analysis.get('confidence', 0)
                    workflow_name = analysis.get('workflow_name', 'Unknown')
                    actions_analysis = analysis.get('actions_analysis', [])
                    print(f"   AI Analysis: {confidence} confidence, {len(actions_analysis)} actions")
                    return confidence > 0.3 and len(actions_analysis) >= 1
            return False
        
        results.append(self.run_test("Analyze Description", test_analyze))
        
        # Test 4: Create workflow from NL (AI Integration)
        def test_nl_creation():
            nl_request = {
                "description": "Create a comprehensive lead nurturing workflow: when a new high-value lead (over $25,000) is created, immediately assign to senior sales representative, send personalized welcome email with company information, wait 2 business days, then send product demo invitation if lead hasn't responded, wait another 3 days, then send case study email if still no response, and finally create a follow-up task for the sales rep after 1 week",
                "context": "B2B SaaS platform targeting enterprise clients with complex sales cycles. Focus on high-touch, personalized approach for valuable prospects.",
                "creator_id": "final_test_user"
            }
            
            response = requests.post(f"{self.base_url}/nl-workflows/create", json=nl_request, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                workflow = data.get('workflow', {})
                confidence = data.get('confidence', 0)
                suggestions = data.get('suggestions', [])
                
                print(f"   AI Confidence: {confidence}")
                print(f"   Suggestions: {len(suggestions)}")
                
                if workflow:
                    name = workflow.get('name', 'Unknown')
                    actions = workflow.get('actions', [])
                    trigger = workflow.get('trigger', {})
                    
                    print(f"   Generated: '{name}' with {len(actions)} actions")
                    print(f"   Trigger: {trigger.get('type', 'unknown')}")
                    
                    # Check for quality indicators
                    action_types = [action.get('type') for action in actions]
                    has_email = any('email' in str(t).lower() for t in action_types)
                    has_wait = any('wait' in str(t).lower() for t in action_types)
                    has_assign = any('assign' in str(t).lower() for t in action_types)
                    
                    print(f"   Actions include: Email={has_email}, Wait={has_wait}, Assign={has_assign}")
                    
                    # Success criteria: reasonable confidence, multiple actions, expected action types
                    quality_score = 0
                    if confidence > 0.4: quality_score += 1
                    if len(actions) >= 3: quality_score += 1
                    if has_email: quality_score += 1
                    if has_wait: quality_score += 1
                    if len(name) > 10: quality_score += 1  # Meaningful name
                    
                    print(f"   Quality Score: {quality_score}/5")
                    
                    if quality_score >= 3:
                        print("   ✅ High-quality AI workflow generation!")
                        return True
                    elif quality_score >= 2:
                        print("   ✅ Acceptable AI workflow generation")
                        return True
                    else:
                        print("   ⚠️  AI workflow generation needs improvement")
                        return False
                else:
                    print("   ❌ No workflow generated")
                    return False
            else:
                print(f"   ❌ NL Creation failed: {response.status_code} - {response.text[:200]}")
                return False
        
        results.append(self.run_test("NL Workflow Creation (AI)", test_nl_creation))
        
        passed = sum(results)
        total = len(results)
        print(f"\n📊 NATURAL LANGUAGE WORKFLOWS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        # AI Integration status
        if results[-1]:  # If NL creation test passed
            print("   🤖 AI Integration: ✅ WORKING - Emergent LLM key functional")
        else:
            print("   🤖 AI Integration: ❌ ISSUE - Check Emergent LLM key or processing")
        
        return all(results)

    def run_comprehensive_test(self):
        """Run comprehensive Phase 6B testing"""
        print("🚀 COMPREHENSIVE PHASE 6B WORKFLOW SYSTEMS TESTING")
        print("="*80)
        
        # Run all three system tests
        system_results = {
            'Conditional Logic Builder': self.test_conditional_logic_builder(),
            'Workflow Execution Engine': self.test_workflow_execution_engine(),
            'Natural Language Workflows': self.test_natural_language_workflows()
        }
        
        # Final summary
        print("\n" + "="*80)
        print("🎯 FINAL PHASE 6B COMPREHENSIVE TEST RESULTS")
        print("="*80)
        
        for system, result in system_results.items():
            status = "✅ WORKING" if result else "❌ FAILED"
            print(f"   {system}: {status}")
        
        working_systems = sum(1 for result in system_results.values() if result)
        total_systems = len(system_results)
        
        print(f"\n📊 OVERALL PHASE 6B RESULTS:")
        print(f"   Systems Tested: {total_systems}")
        print(f"   Systems Working: {working_systems}")
        print(f"   Systems Failed: {total_systems - working_systems}")
        print(f"   Success Rate: {(working_systems/total_systems*100):.1f}%")
        
        print(f"\n🔍 DETAILED STATISTICS:")
        print(f"   Total Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Test Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for i, test in enumerate(self.failed_tests[:5], 1):
                print(f"   {i}. {test}")
            if len(self.failed_tests) > 5:
                print(f"   ... and {len(self.failed_tests) - 5} more")
        
        # Final verdict
        if working_systems == total_systems:
            print(f"\n🎉 ALL PHASE 6B WORKFLOW SYSTEMS WORKING PERFECTLY!")
            print("   ✅ Conditional Logic Builder: Advanced workflow conditions")
            print("   ✅ Workflow Execution Engine: Runtime management & monitoring")
            print("   ✅ Natural Language Workflows: AI-powered workflow creation")
        elif working_systems >= 2:
            print(f"\n✅ PHASE 6B MOSTLY SUCCESSFUL! {working_systems}/{total_systems} systems working.")
            print("   Most workflow automation features are operational.")
        else:
            print(f"\n⚠️  PHASE 6B NEEDS ATTENTION! Only {working_systems}/{total_systems} systems working.")
        
        print("="*80)
        return working_systems == total_systems

def main():
    """Main test execution"""
    tester = FinalPhase6BTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    main()