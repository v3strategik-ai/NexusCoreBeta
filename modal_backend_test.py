#!/usr/bin/env python3
"""
Modal Backend Integration Testing for Nexus Core
Tests the specific API endpoints used by the new modals:
1. Create Digital Employee Modal -> /api/agents/
2. Upload Knowledge Base Modal -> /api/knowledge/upload  
3. Add Lead Modal -> /api/crm/leads
"""

import requests
import sys
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, Any

class ModalBackendTester:
    def __init__(self, base_url="https://continue-work-24.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.created_agent_id = None
        self.created_lead_id = None

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, data: Dict[Any, Any] = None, headers: Dict[str, str] = None, files: Dict[str, Any] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        if headers is None:
            headers = {'Content-Type': 'application/json'} if not files else {}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, timeout=15)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=15)

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
                print(f"   Response: {response.text[:300]}...")
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': response.text[:300]
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

    def test_create_agent_modal_api(self):
        """Test Create Digital Employee Modal API Integration"""
        print("\n" + "="*60)
        print("TESTING CREATE DIGITAL EMPLOYEE MODAL API")
        print("="*60)
        
        # Test data matching the modal form
        agent_data = {
            "name": "Content Creator Test",
            "type": "Marketing Specialist",
            "personality": "Creative & Data-Driven",
            "specialization": "Content Creation, SEO, Social Media Marketing",
            "autonomy_level": "High",
            "configuration": {}
        }
        
        success, response = self.run_test(
            "Create Agent via Modal API",
            "POST",
            "agents/",
            201,
            data=agent_data
        )
        
        if success:
            self.created_agent_id = response.get('id')
            print(f"   ✅ Agent Created: {response.get('name')} (ID: {self.created_agent_id})")
            print(f"   Type: {response.get('type')}")
            print(f"   Status: {response.get('status')}")
            print(f"   Autonomy: {response.get('autonomy_level')}")
            
            # Verify agent appears in agents list
            success2, agents_response = self.run_test(
                "Verify Agent in List",
                "GET",
                "agents/"
            )
            
            if success2:
                agents = agents_response.get('agents', [])
                found_agent = any(agent.get('id') == self.created_agent_id for agent in agents)
                if found_agent:
                    print(f"   ✅ Agent appears in agents list")
                else:
                    print(f"   ❌ Agent NOT found in agents list")
                    self.failed_tests.append({
                        'name': 'Agent List Verification',
                        'error': 'Created agent not found in agents list'
                    })
            
            return success and success2
        
        return success

    def test_upload_knowledge_modal_api(self):
        """Test Upload Knowledge Base Modal API Integration"""
        print("\n" + "="*60)
        print("TESTING UPLOAD KNOWLEDGE BASE MODAL API")
        print("="*60)
        
        # Create a temporary test file
        test_content = """
        # Test Knowledge Document
        
        This is a test knowledge document for the Nexus Core platform.
        
        ## Key Information
        - Product features and benefits
        - Customer onboarding process
        - Technical specifications
        
        This document will help AI agents provide better customer support.
        """
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            # Prepare form data matching the modal
            form_data = {
                'title': 'Test Knowledge Document',
                'description': 'A test document for knowledge base testing',
                'category': 'Training Materials',
                'tags': 'test,training,customer-service',
                'agent_ids': self.created_agent_id if self.created_agent_id else ''
            }
            
            # Prepare file for upload
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_knowledge.md', f, 'text/markdown')}
                
                success, response = self.run_test(
                    "Upload Knowledge via Modal API",
                    "POST",
                    "knowledge/upload",
                    200,
                    data=form_data,
                    files=files
                )
            
            if success:
                print(f"   ✅ Knowledge Uploaded: {response.get('title')}")
                print(f"   Category: {response.get('category')}")
                print(f"   File Size: {response.get('file_size')} bytes")
                print(f"   Tags: {response.get('tags')}")
                
                # Verify knowledge appears in knowledge list
                success2, knowledge_response = self.run_test(
                    "Verify Knowledge in List",
                    "GET",
                    "knowledge/"
                )
                
                if success2:
                    knowledge_items = knowledge_response if isinstance(knowledge_response, list) else []
                    found_knowledge = any(kb.get('title') == 'Test Knowledge Document' for kb in knowledge_items)
                    if found_knowledge:
                        print(f"   ✅ Knowledge appears in knowledge list")
                    else:
                        print(f"   ❌ Knowledge NOT found in knowledge list")
                        self.failed_tests.append({
                            'name': 'Knowledge List Verification',
                            'error': 'Uploaded knowledge not found in knowledge list'
                        })
                
                return success and success2
            
            return success
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_add_lead_modal_api(self):
        """Test Add Lead Modal API Integration"""
        print("\n" + "="*60)
        print("TESTING ADD LEAD MODAL API")
        print("="*60)
        
        # Test data matching the modal form
        lead_data = {
            "name": "Test Company Lead",
            "email": f"test.lead.{datetime.now().strftime('%H%M%S')}@testcompany.com",
            "phone": "+1-555-TEST",
            "company": "Test Company Inc",
            "status": "hot",
            "value": 25000.0,
            "source": "Website Contact Form",
            "assigned_agent_id": self.created_agent_id if self.created_agent_id else None,
            "notes": ["Initial contact from website form. Very interested in our AI solutions."],
            "tags": []
        }
        
        success, response = self.run_test(
            "Create Lead via Modal API",
            "POST",
            "crm/leads",
            200,
            data=lead_data
        )
        
        if success:
            self.created_lead_id = response.get('id')
            print(f"   ✅ Lead Created: {response.get('name')} (ID: {self.created_lead_id})")
            print(f"   Email: {response.get('email')}")
            print(f"   Status: {response.get('status')}")
            print(f"   Value: ${response.get('value'):,}")
            print(f"   Assigned Agent: {response.get('assigned_agent_name', 'None')}")
            
            # Verify lead appears in leads list
            success2, leads_response = self.run_test(
                "Verify Lead in List",
                "GET",
                "crm/leads"
            )
            
            if success2:
                leads = leads_response.get('leads', [])
                found_lead = any(lead.get('id') == self.created_lead_id for lead in leads)
                if found_lead:
                    print(f"   ✅ Lead appears in leads list")
                else:
                    print(f"   ❌ Lead NOT found in leads list")
                    self.failed_tests.append({
                        'name': 'Lead List Verification',
                        'error': 'Created lead not found in leads list'
                    })
            
            return success and success2
        
        return success

    def test_modal_integration_flow(self):
        """Test complete modal integration flow"""
        print("\n" + "="*60)
        print("TESTING COMPLETE MODAL INTEGRATION FLOW")
        print("="*60)
        
        # Test that created agent can be assigned to leads
        if self.created_agent_id and self.created_lead_id:
            success, response = self.run_test(
                "Assign Created Agent to Created Lead",
                "POST",
                f"crm/leads/{self.created_lead_id}/assign-agent?agent_id={self.created_agent_id}",
                200
            )
            
            if success:
                print(f"   ✅ Agent successfully assigned to lead")
                
                # Verify assignment
                success2, lead_response = self.run_test(
                    "Verify Lead Assignment",
                    "GET",
                    f"crm/leads/{self.created_lead_id}"
                )
                
                if success2:
                    assigned_agent_id = lead_response.get('assigned_agent_id')
                    if assigned_agent_id == self.created_agent_id:
                        print(f"   ✅ Lead assignment verified")
                    else:
                        print(f"   ❌ Lead assignment verification failed")
                        self.failed_tests.append({
                            'name': 'Lead Assignment Verification',
                            'error': f'Expected agent {self.created_agent_id}, got {assigned_agent_id}'
                        })
                
                return success and success2
            
            return success
        else:
            print("   ⚠️  Skipping integration test - missing created agent or lead")
            return True

    def test_error_handling(self):
        """Test error handling for modal APIs"""
        print("\n" + "="*60)
        print("TESTING MODAL API ERROR HANDLING")
        print("="*60)
        
        # Test invalid agent creation
        invalid_agent_data = {
            "name": "",  # Empty name should fail
            "type": "Invalid Type",
            "autonomy_level": "Invalid Level"
        }
        
        success1, _ = self.run_test(
            "Invalid Agent Creation",
            "POST",
            "agents/",
            422,  # Validation error expected
            data=invalid_agent_data
        )
        
        # Test duplicate lead email
        if self.created_lead_id:
            # Get the email from created lead first
            success_get, lead_data = self.run_test(
                "Get Created Lead for Duplicate Test",
                "GET",
                f"crm/leads/{self.created_lead_id}"
            )
            
            if success_get:
                duplicate_lead_data = {
                    "name": "Duplicate Test",
                    "email": lead_data.get('email'),  # Use same email
                    "status": "cold",
                    "value": 1000
                }
                
                success2, _ = self.run_test(
                    "Duplicate Lead Email",
                    "POST",
                    "crm/leads",
                    400,  # Bad request expected
                    data=duplicate_lead_data
                )
            else:
                success2 = True  # Skip if we can't get the lead
        else:
            success2 = True  # Skip if no lead was created
        
        # Test invalid file upload
        invalid_form_data = {
            'title': '',  # Empty title should fail
            'category': 'Invalid Category'
        }
        
        # Create empty file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("")
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('empty.txt', f, 'text/plain')}
                
                success3, _ = self.run_test(
                    "Invalid Knowledge Upload",
                    "POST",
                    "knowledge/upload",
                    422,  # Validation error expected
                    data=invalid_form_data,
                    files=files
                )
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        return success1 and success2 and success3

    def run_all_tests(self):
        """Run all modal backend integration tests"""
        print("🚀 Starting Modal Backend Integration Testing")
        print("=" * 70)
        
        # Run all test suites in order
        test_results = [
            self.test_create_agent_modal_api(),
            self.test_upload_knowledge_modal_api(),
            self.test_add_lead_modal_api(),
            self.test_modal_integration_flow(),
            self.test_error_handling()
        ]
        
        # Print summary
        print("\n" + "="*70)
        print("📊 MODAL BACKEND INTEGRATION TEST SUMMARY")
        print("="*70)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"{i}. {failure['name']}")
                if 'expected' in failure and 'actual' in failure:
                    print(f"   Expected: {failure['expected']}, Got: {failure['actual']}")
                if 'error' in failure:
                    print(f"   Error: {failure['error']}")
                if 'response' in failure:
                    print(f"   Response: {failure['response']}")
        
        all_passed = all(test_results)
        if all_passed:
            print("\n🎉 ALL MODAL BACKEND INTEGRATION TESTS PASSED!")
            print("✅ Create Digital Employee Modal API: WORKING")
            print("✅ Upload Knowledge Base Modal API: WORKING") 
            print("✅ Add Lead Modal API: WORKING")
            print("✅ Modal Integration Flow: WORKING")
            print("✅ Error Handling: WORKING")
        else:
            failed_count = len([r for r in test_results if not r])
            print(f"\n⚠️  {failed_count} test suite(s) had failures")
        
        return all_passed

def main():
    """Main test execution"""
    tester = ModalBackendTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())