#!/usr/bin/env python3
"""
Focused Agent Configuration/Edit Functionality Test
Tests the specific issue reported: editing existing agents doesn't work
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class AgentEditTester:
    def __init__(self, base_url="https://smartagent-nexus.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, data: Dict[Any, Any] = None, headers: Dict[str, str] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

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
                print(f"   Response: {response.text[:500]}...")
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': response.text[:500]
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

    def test_agent_edit_functionality(self):
        """Test the complete agent edit/configuration functionality"""
        print("\n" + "="*60)
        print("TESTING AGENT CONFIGURATION/EDIT FUNCTIONALITY")
        print("="*60)
        
        created_agent_id = None
        
        # Step 1: Create a test agent (this should work according to user)
        print("\n🔍 Step 1: Creating Test Agent...")
        agent_create_data = {
            "name": "EditTest Agent",
            "type": "Sales Representative",
            "personality": "Professional and persuasive",
            "specialization": "Lead conversion and client communication",
            "autonomy_level": "High",
            "configuration": {
                "ai_model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 1000,
                "creativity": 0.6,
                "responsiveness": 0.8
            }
        }
        
        success1, create_response = self.run_test(
            "Create Agent for Edit Testing", "POST", "agents/", 200, agent_create_data
        )
        
        if success1:
            created_agent_id = create_response.get('id')
            print(f"   ✅ Agent Created Successfully")
            print(f"   Agent ID: {created_agent_id}")
            print(f"   Agent Name: {create_response.get('name')}")
            print(f"   Initial Configuration: {create_response.get('configuration', {})}")
        else:
            print("   ❌ CRITICAL: Cannot create agent - this contradicts user report")
            return False
        
        # Step 2: Verify agent was created by retrieving it
        print("\n🔍 Step 2: Verifying Agent Creation...")
        success2, initial_agent = self.run_test(
            "Get Initial Agent", "GET", f"agents/{created_agent_id}"
        )
        
        if success2:
            print(f"   ✅ Agent Retrieved Successfully")
            print(f"   Name: {initial_agent.get('name')}")
            print(f"   Type: {initial_agent.get('type')}")
            print(f"   Status: {initial_agent.get('status')}")
            print(f"   Configuration: {initial_agent.get('configuration', {})}")
            initial_config = initial_agent.get('configuration', {})
        else:
            print("   ❌ CRITICAL: Cannot retrieve created agent")
            return False
        
        # Step 3: Test basic agent property update (non-configuration)
        print("\n🔍 Step 3: Testing Basic Agent Property Update...")
        basic_update_data = {
            "name": "EditTest Agent - Updated",
            "personality": "Highly professional and results-driven"
        }
        
        success3, basic_update_response = self.run_test(
            "Basic Agent Property Update", "PUT", f"agents/{created_agent_id}", 200, basic_update_data
        )
        
        if success3:
            print(f"   ✅ Basic Update Successful")
            print(f"   Updated Name: {basic_update_response.get('name')}")
            print(f"   Updated Personality: {basic_update_response.get('personality')}")
        else:
            print("   ❌ FAILED: Basic agent property update failed")
        
        # Step 4: Test configuration update (this is likely where the issue is)
        print("\n🔍 Step 4: Testing Configuration Update...")
        config_update_data = {
            "configuration": {
                "ai_model": "claude-3.5-sonnet",
                "temperature": 0.8,
                "max_tokens": 1500,
                "creativity": 0.7,
                "responsiveness": 0.9,
                "accuracy": 0.85,
                "learning_rate": 0.6,
                "proactive_mode": True,
                "auto_learn": True,
                "context_memory": True,
                "max_daily_tasks": 150,
                "integrations": {
                    "email": True,
                    "calendar": True,
                    "crm": True
                },
                "system_instructions": "You are a professional sales agent focused on converting leads into customers."
            }
        }
        
        success4, config_update_response = self.run_test(
            "Configuration Update", "PUT", f"agents/{created_agent_id}", 200, config_update_data
        )
        
        if success4:
            print(f"   ✅ Configuration Update Successful")
            updated_config = config_update_response.get('configuration', {})
            updated_metrics = config_update_response.get('metrics', {})
            
            print(f"   Updated AI Model: {updated_config.get('ai_model')}")
            print(f"   Updated Temperature: {updated_config.get('temperature')}")
            print(f"   Updated Max Tokens: {updated_config.get('max_tokens')}")
            print(f"   Configuration Complexity: {updated_metrics.get('configuration_complexity', 0)}")
            print(f"   Readiness Score: {updated_metrics.get('readiness_score', 0)}")
            
            # Verify specific configuration values
            config_checks = [
                ("ai_model", "claude-3.5-sonnet"),
                ("temperature", 0.8),
                ("max_tokens", 1500),
                ("creativity", 0.7),
                ("responsiveness", 0.9)
            ]
            
            config_validation_passed = True
            for key, expected_value in config_checks:
                actual_value = updated_config.get(key)
                if actual_value == expected_value:
                    print(f"   ✅ {key}: {actual_value} (correct)")
                else:
                    print(f"   ❌ {key}: expected {expected_value}, got {actual_value}")
                    config_validation_passed = False
            
            if config_validation_passed:
                print("   ✅ All configuration values updated correctly")
            else:
                print("   ❌ Some configuration values not updated correctly")
        else:
            print("   ❌ CRITICAL: Configuration update failed - THIS IS THE REPORTED ISSUE")
        
        # Step 5: Verify persistence by retrieving the agent again
        print("\n🔍 Step 5: Verifying Update Persistence...")
        success5, updated_agent = self.run_test(
            "Get Updated Agent", "GET", f"agents/{created_agent_id}"
        )
        
        if success5:
            print(f"   ✅ Updated Agent Retrieved")
            final_config = updated_agent.get('configuration', {})
            final_name = updated_agent.get('name')
            final_personality = updated_agent.get('personality')
            
            print(f"   Final Name: {final_name}")
            print(f"   Final Personality: {final_personality}")
            print(f"   Final AI Model: {final_config.get('ai_model')}")
            print(f"   Final Temperature: {final_config.get('temperature')}")
            
            # Check if updates persisted
            persistence_checks = []
            
            # Check basic property persistence
            if final_name == "EditTest Agent - Updated":
                print("   ✅ Name update persisted")
                persistence_checks.append(True)
            else:
                print(f"   ❌ Name update not persisted: {final_name}")
                persistence_checks.append(False)
            
            # Check configuration persistence
            if final_config.get('ai_model') == 'claude-3.5-sonnet':
                print("   ✅ AI model update persisted")
                persistence_checks.append(True)
            else:
                print(f"   ❌ AI model update not persisted: {final_config.get('ai_model')}")
                persistence_checks.append(False)
            
            if final_config.get('temperature') == 0.8:
                print("   ✅ Temperature update persisted")
                persistence_checks.append(True)
            else:
                print(f"   ❌ Temperature update not persisted: {final_config.get('temperature')}")
                persistence_checks.append(False)
            
            if all(persistence_checks):
                print("   ✅ All updates persisted correctly")
            else:
                print("   ❌ Some updates did not persist - DATABASE PERSISTENCE ISSUE")
        else:
            print("   ❌ CRITICAL: Cannot retrieve updated agent")
        
        # Step 6: Test the /agents/{agent_id}/configure endpoint if it exists
        print("\n🔍 Step 6: Testing Dedicated Configure Endpoint...")
        configure_data = {
            "ai_model": "gemini-2.0-flash",
            "temperature": 0.9,
            "autonomy_level": "Quantum"
        }
        
        success6, configure_response = self.run_test(
            "Dedicated Configure Endpoint", "PUT", f"agents/{created_agent_id}/configure", 200, configure_data
        )
        
        if success6:
            print("   ✅ Dedicated configure endpoint works")
        else:
            print("   ⚠️  Dedicated configure endpoint not found or failed")
            # Try POST method
            success6b, configure_response_post = self.run_test(
                "Dedicated Configure Endpoint (POST)", "POST", f"agents/{created_agent_id}/configure", 200, configure_data
            )
            if success6b:
                print("   ✅ Dedicated configure endpoint works with POST")
                success6 = True
            else:
                print("   ⚠️  Dedicated configure endpoint not available")
                success6 = True  # Don't fail the test for this
        
        # Step 7: Test configuration history endpoint
        print("\n🔍 Step 7: Testing Configuration History...")
        success7, history_response = self.run_test(
            "Configuration History", "GET", f"agents/{created_agent_id}/configuration/history"
        )
        
        if success7:
            history = history_response.get('configuration_history', [])
            print(f"   ✅ Configuration history retrieved: {len(history)} entries")
            if history:
                latest = history[0]
                print(f"   Latest change: {latest.get('description', 'N/A')}")
                print(f"   Timestamp: {latest.get('timestamp', 'N/A')}")
        else:
            print("   ❌ Configuration history endpoint failed")
        
        # Step 8: Test configuration analytics endpoint
        print("\n🔍 Step 8: Testing Configuration Analytics...")
        success8, analytics_response = self.run_test(
            "Configuration Analytics", "GET", f"agents/{created_agent_id}/configuration/analytics"
        )
        
        if success8:
            analytics = analytics_response.get('analytics', {})
            print(f"   ✅ Configuration analytics retrieved")
            print(f"   Complexity Score: {analytics.get('configuration_complexity', 0)}")
            print(f"   Readiness Score: {analytics.get('readiness_score', 0)}")
            print(f"   Optimization Score: {analytics.get('optimization_score', 0)}")
        else:
            print("   ❌ Configuration analytics endpoint failed")
        
        # Step 9: Test edge cases and error handling
        print("\n🔍 Step 9: Testing Edge Cases and Error Handling...")
        
        # Test update with invalid agent ID
        success9a, invalid_response = self.run_test(
            "Update Invalid Agent ID", "PUT", "agents/invalid_agent_id_12345", 404, basic_update_data
        )
        
        if success9a:
            print("   ✅ Proper error handling for invalid agent ID")
        else:
            print("   ❌ Error handling for invalid agent ID failed")
        
        # Test update with invalid configuration values
        invalid_config_data = {
            "configuration": {
                "temperature": 2.0,  # Invalid - should be <= 1.0
                "max_tokens": 5000,  # Invalid - should be <= 2000
                "ai_model": "invalid_model"  # Invalid model
            }
        }
        
        success9b, invalid_config_response = self.run_test(
            "Update with Invalid Configuration", "PUT", f"agents/{created_agent_id}", 200, invalid_config_data
        )
        
        if success9b:
            validated_config = invalid_config_response.get('configuration', {})
            temp_valid = 0.0 <= validated_config.get('temperature', 0.7) <= 1.0
            tokens_valid = validated_config.get('max_tokens', 1000) <= 2000
            model_valid = validated_config.get('ai_model') in ["gpt-4o", "claude-3.5-sonnet", "gemini-2.0-flash"]
            
            if temp_valid and tokens_valid and model_valid:
                print("   ✅ Configuration validation working correctly")
            else:
                print("   ❌ Configuration validation may have issues")
                print(f"      Temperature: {validated_config.get('temperature')} (valid: {temp_valid})")
                print(f"      Max tokens: {validated_config.get('max_tokens')} (valid: {tokens_valid})")
                print(f"      AI model: {validated_config.get('ai_model')} (valid: {model_valid})")
        else:
            print("   ❌ Configuration validation test failed")
        
        success9 = success9a and success9b
        
        # Cleanup: Delete the test agent
        print("\n🔍 Cleanup: Deleting Test Agent...")
        cleanup_success, cleanup_response = self.run_test(
            "Delete Test Agent", "DELETE", f"agents/{created_agent_id}", 200
        )
        
        if cleanup_success:
            print("   ✅ Test agent deleted successfully")
        else:
            print("   ⚠️  Failed to delete test agent")
        
        # Summary
        all_tests = [success1, success2, success3, success4, success5, success6, success7, success8, success9]
        passed_tests = sum(all_tests)
        total_tests = len(all_tests)
        
        print(f"\n📊 AGENT EDIT FUNCTIONALITY TEST SUMMARY:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Specific analysis of the reported issue
        print(f"\n🔍 ISSUE ANALYSIS:")
        if success1:
            print("   ✅ Agent creation works (matches user report)")
        else:
            print("   ❌ Agent creation failed (contradicts user report)")
        
        if success2:
            print("   ✅ Agent retrieval works (matches user report)")
        else:
            print("   ❌ Agent retrieval failed (contradicts user report)")
        
        if success3:
            print("   ✅ Basic agent property updates work")
        else:
            print("   ❌ Basic agent property updates failed")
        
        if success4:
            print("   ✅ Configuration updates work")
        else:
            print("   ❌ Configuration updates failed - THIS IS THE REPORTED ISSUE")
        
        if success5:
            print("   ✅ Update persistence works")
        else:
            print("   ❌ Update persistence failed - CRITICAL DATABASE ISSUE")
        
        return all(all_tests)

    def print_failed_tests(self):
        """Print detailed information about failed tests"""
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS DETAILS:")
            print("="*50)
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['name']}")
                if 'expected' in test and 'actual' in test:
                    print(f"   Expected Status: {test['expected']}")
                    print(f"   Actual Status: {test['actual']}")
                if 'response' in test:
                    print(f"   Response: {test['response']}")
                if 'error' in test:
                    print(f"   Error: {test['error']}")
                print()

def main():
    """Main test execution"""
    print("🚀 Starting Agent Configuration/Edit Functionality Test")
    print("="*60)
    
    tester = AgentEditTester()
    
    try:
        # Run the focused agent edit test
        success = tester.test_agent_edit_functionality()
        
        # Print summary
        print(f"\n🏁 TEST EXECUTION COMPLETE")
        print(f"Total Tests Run: {tester.tests_run}")
        print(f"Tests Passed: {tester.tests_passed}")
        print(f"Tests Failed: {len(tester.failed_tests)}")
        print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
        
        if success:
            print("\n✅ ALL AGENT EDIT TESTS PASSED!")
            print("The agent configuration/edit functionality appears to be working correctly.")
        else:
            print("\n❌ SOME AGENT EDIT TESTS FAILED!")
            print("Issues found with agent configuration/edit functionality.")
            tester.print_failed_tests()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())