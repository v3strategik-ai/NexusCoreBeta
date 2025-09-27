#!/usr/bin/env python3
"""
Phase 6D: Advanced Intelligence & Voice Backend Testing
Tests the Advanced Voice Interface and Data Export & Backup Systems
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class Phase6DTester:
    def __init__(self, base_url="https://smartagent-nexus.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, data: Dict[Any, Any] = None, headers: Dict[str, str] = None, timeout: int = 30) -> tuple:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        if headers is None:
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

    def test_phase_6d_advanced_voice_interface(self):
        """Test Phase 6D-A: Advanced Voice Interface backend implementation"""
        print("\n" + "="*50)
        print("TESTING PHASE 6D-A: ADVANCED VOICE INTERFACE")
        print("="*50)
        
        # Test 1: Voice Service Health Check
        success1, health_response = self.run_test("Voice Service Health Check", "GET", "advanced-voice/health")
        if success1:
            print(f"   Voice Service Status: {health_response.get('status', 'unknown')}")
            services = health_response.get('services', {})
            features = health_response.get('features_available', {})
            api_key_status = health_response.get('api_key_status', 'unknown')
            
            print(f"   OpenAI Realtime: {services.get('openai_realtime', 'unknown')}")
            print(f"   Emergent Integration: {services.get('emergent_integration', 'unknown')}")
            print(f"   Voice Sessions: {services.get('voice_sessions', 'unknown')}")
            print(f"   Command Processing: {services.get('command_processing', 'unknown')}")
            print(f"   API Key Status: {api_key_status}")
            print(f"   Realtime Voice Chat: {features.get('realtime_voice_chat', False)}")
            print(f"   Enhanced Voice Commands: {features.get('enhanced_voice_commands', False)}")
            print(f"   Multi-tenant Support: {features.get('multi_tenant_support', False)}")
        
        # Test 2: Get Available Voice Commands
        success2, commands_response = self.run_test("Get Available Voice Commands", "GET", "advanced-voice/commands/available")
        if success2:
            enhanced_commands = commands_response.get('enhanced_commands', {})
            total_categories = commands_response.get('total_categories', 0)
            total_commands = commands_response.get('total_commands', 0)
            
            print(f"   Command Categories: {total_categories}")
            print(f"   Total Commands: {total_commands}")
            
            # Verify expected categories
            expected_categories = ['navigation', 'agent_management', 'crm_operations', 'workflow_automation', 'analytics_reporting', 'enterprise_management', 'system_commands']
            found_categories = list(enhanced_commands.keys())
            
            print(f"   Categories Found: {found_categories}")
            
            if all(cat in found_categories for cat in expected_categories):
                print("   ✅ All 7 expected command categories present")
            else:
                missing = [cat for cat in expected_categories if cat not in found_categories]
                print(f"   ❌ Missing categories: {missing}")
        
        # Test 3: Create Voice Session
        session_create_data = {
            "user_id": "test_user_voice_001",
            "tenant_id": "tenant_voice_test",
            "session_type": "assistant",
            "context": {
                "language": "en",
                "voice_mode": "realtime",
                "features": ["enhanced_commands", "conversation_memory"]
            }
        }
        
        success3, session_response = self.run_test("Create Voice Session", "POST", "advanced-voice/sessions", 200, session_create_data)
        session_id = None
        if success3:
            session_id = session_response.get('session_id')
            print(f"   Created Session ID: {session_id}")
            print(f"   Session Status: {session_response.get('status')}")
            print(f"   Session Type: {session_response.get('session_type')}")
            print(f"   User ID: {session_response.get('user_id')}")
            print(f"   Tenant ID: {session_response.get('tenant_id')}")
        
        # Test 4: Get Voice Session Details
        success4 = False
        if session_id:
            success4, session_detail = self.run_test("Get Voice Session Details", "GET", f"advanced-voice/sessions/{session_id}")
            if success4:
                print(f"   Retrieved Session: {session_detail.get('session_id')}")
                print(f"   Session Status: {session_detail.get('status')}")
                print(f"   Created At: {session_detail.get('created_at')}")
        
        # Test 5: Add Voice Message to Session
        success5 = False
        if session_id:
            message_data = {
                "session_id": session_id,
                "message_type": "text",
                "content": "Show me the dashboard",
                "metadata": {
                    "voice_command": True,
                    "confidence": 0.95
                }
            }
            
            success5, message_response = self.run_test("Add Voice Message", "POST", f"advanced-voice/sessions/{session_id}/messages", 200, message_data)
            if success5:
                print(f"   Message Added: {message_response.get('message')}")
                print(f"   Message ID: {message_response.get('message_id')}")
        
        # Test 6: Get Conversation History
        success6 = False
        if session_id:
            success6, history_response = self.run_test("Get Conversation History", "GET", f"advanced-voice/sessions/{session_id}/history")
            if success6:
                total_messages = history_response.get('total_messages', 0)
                messages = history_response.get('messages', [])
                print(f"   Total Messages in History: {total_messages}")
                print(f"   Messages Retrieved: {len(messages)}")
                
                if messages:
                    latest_message = messages[-1]
                    print(f"   Latest Message Type: {latest_message.get('message_type')}")
                    print(f"   Latest Message Content: {latest_message.get('content')}")
        
        # Test 7: Execute Voice Commands
        voice_commands_to_test = [
            {"command": "navigate to dashboard", "user_id": "test_user", "tenant_id": "test_tenant"},
            {"command": "show me the agents", "user_id": "test_user", "tenant_id": "test_tenant"},
            {"command": "create new agent", "user_id": "test_user", "tenant_id": "test_tenant"},
            {"command": "add new lead", "user_id": "test_user", "tenant_id": "test_tenant"},
            {"command": "switch to dark mode", "user_id": "test_user", "tenant_id": "test_tenant"}
        ]
        
        command_test_results = []
        for i, command_data in enumerate(voice_commands_to_test):
            success_cmd, cmd_response = self.run_test(f"Execute Voice Command {i+1}", "POST", "advanced-voice/commands/execute", 200, command_data)
            command_test_results.append(success_cmd)
            
            if success_cmd:
                executed = cmd_response.get('executed', False)
                action_taken = cmd_response.get('action_taken')
                response_text = cmd_response.get('response_text', '')
                
                print(f"   Command: '{command_data['command']}'")
                print(f"   Executed: {executed}")
                print(f"   Action: {action_taken}")
                print(f"   Response: {response_text[:100]}...")
        
        success7 = all(command_test_results)
        
        # Test 8: Voice Usage Analytics
        success8, analytics_response = self.run_test("Voice Usage Analytics", "GET", "advanced-voice/analytics/usage")
        if success8:
            total_sessions = analytics_response.get('total_sessions', 0)
            active_sessions = analytics_response.get('active_sessions', 0)
            total_messages = analytics_response.get('total_messages', 0)
            engagement_score = analytics_response.get('user_engagement_score', 0)
            voice_features = analytics_response.get('voice_feature_adoption', {})
            
            print(f"   Total Sessions: {total_sessions}")
            print(f"   Active Sessions: {active_sessions}")
            print(f"   Total Messages: {total_messages}")
            print(f"   Engagement Score: {engagement_score}")
            print(f"   Realtime Voice: {voice_features.get('realtime_voice', False)}")
            print(f"   Voice Commands: {voice_features.get('voice_commands', False)}")
            print(f"   Context Awareness: {voice_features.get('context_awareness', False)}")
        
        # Test 9: End Voice Session
        success9 = False
        if session_id:
            success9, end_response = self.run_test("End Voice Session", "DELETE", f"advanced-voice/sessions/{session_id}")
            if success9:
                print(f"   Session Ended: {end_response.get('message')}")
        
        # Summary of Advanced Voice Interface Tests
        all_voice_tests = [success1, success2, success3, success4, success5, success6, success7, success8, success9]
        passed_voice_tests = sum(all_voice_tests)
        total_voice_tests = len(all_voice_tests)
        
        print(f"\n📊 ADVANCED VOICE INTERFACE TEST SUMMARY:")
        print(f"   Tests Passed: {passed_voice_tests}/{total_voice_tests}")
        print(f"   Success Rate: {(passed_voice_tests/total_voice_tests*100):.1f}%")
        
        if passed_voice_tests == total_voice_tests:
            print("   🎉 ALL ADVANCED VOICE INTERFACE TESTS PASSED!")
        else:
            print("   ⚠️  Some Advanced Voice Interface tests failed")
        
        return all(all_voice_tests)

    def test_phase_6d_data_export_backup_systems(self):
        """Test Phase 6D-B: Data Export & Backup Systems backend implementation"""
        print("\n" + "="*50)
        print("TESTING PHASE 6D-B: DATA EXPORT & BACKUP SYSTEMS")
        print("="*50)
        
        # Test 1: Create Data Export Job - JSON Format
        export_request_json = {
            "tenant_id": "tenant_export_test",
            "export_type": "full",
            "format": "json",
            "date_range": {
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-12-31T23:59:59"
            },
            "include_metadata": True,
            "compress": True
        }
        
        success1, export_response = self.run_test("Create Export Job - JSON", "POST", "data-export/export", 200, export_request_json)
        export_id_json = None
        if success1:
            export_id_json = export_response.get('export_id')
            print(f"   Export Job Created: {export_id_json}")
            print(f"   Initial Status: {export_response.get('status')}")
            print(f"   Progress: {export_response.get('progress')}%")
            print(f"   Created At: {export_response.get('created_at')}")
        
        # Test 2: Create Data Export Job - CSV Format
        export_request_csv = {
            "tenant_id": "tenant_export_test",
            "export_type": "leads",
            "format": "csv",
            "include_metadata": False,
            "compress": True
        }
        
        success2, export_csv_response = self.run_test("Create Export Job - CSV", "POST", "data-export/export", 200, export_request_csv)
        export_id_csv = None
        if success2:
            export_id_csv = export_csv_response.get('export_id')
            print(f"   CSV Export Job Created: {export_id_csv}")
            print(f"   Initial Status: {export_csv_response.get('status')}")
        
        # Test 3: Create Backup Job - Full Backup
        backup_request_full = {
            "tenant_id": "tenant_backup_test",
            "backup_type": "full",
            "include_audit_logs": True,
            "retention_days": 90
        }
        
        success3, backup_response = self.run_test("Create Backup Job - Full", "POST", "data-export/backup", 200, backup_request_full)
        backup_id_full = None
        if success3:
            backup_id_full = backup_response.get('backup_id')
            print(f"   Full Backup Job Created: {backup_id_full}")
            print(f"   Initial Status: {backup_response.get('status')}")
            print(f"   Progress: {backup_response.get('progress')}%")
        
        # Test 4: Create Backup Job - Incremental Backup
        backup_request_incremental = {
            "tenant_id": "tenant_backup_test",
            "backup_type": "incremental",
            "include_audit_logs": False,
            "retention_days": 30
        }
        
        success4, backup_inc_response = self.run_test("Create Backup Job - Incremental", "POST", "data-export/backup", 200, backup_request_incremental)
        backup_id_inc = None
        if success4:
            backup_id_inc = backup_inc_response.get('backup_id')
            print(f"   Incremental Backup Job Created: {backup_id_inc}")
            print(f"   Initial Status: {backup_inc_response.get('status')}")
        
        # Test 5: Check Export Job Status
        success5 = False
        if export_id_json:
            success5, export_status = self.run_test("Check Export Status", "GET", f"data-export/export/{export_id_json}/status")
            if success5:
                print(f"   Export Status: {export_status.get('status')}")
                print(f"   Progress: {export_status.get('progress')}%")
                if export_status.get('completed_at'):
                    print(f"   Completed At: {export_status.get('completed_at')}")
                if export_status.get('file_size'):
                    print(f"   File Size: {export_status.get('file_size')} bytes")
        
        # Test 6: Check Backup Job Status
        success6 = False
        if backup_id_full:
            success6, backup_status = self.run_test("Check Backup Status", "GET", f"data-export/backup/{backup_id_full}/status")
            if success6:
                print(f"   Backup Status: {backup_status.get('status')}")
                print(f"   Progress: {backup_status.get('progress')}%")
                if backup_status.get('completed_at'):
                    print(f"   Completed At: {backup_status.get('completed_at')}")
                if backup_status.get('backup_size'):
                    print(f"   Backup Size: {backup_status.get('backup_size')} bytes")
        
        # Test 7: Get All Jobs
        success7, jobs_response = self.run_test("Get All Jobs", "GET", "data-export/jobs")
        if success7:
            export_jobs = jobs_response.get('export_jobs', [])
            backup_jobs = jobs_response.get('backup_jobs', [])
            
            print(f"   Total Export Jobs: {len(export_jobs)}")
            print(f"   Total Backup Jobs: {len(backup_jobs)}")
            
            # Show job statuses
            for job in export_jobs[:3]:  # Show first 3
                print(f"   Export Job: {job.get('export_id')} - {job.get('status')} ({job.get('progress')}%)")
            
            for job in backup_jobs[:3]:  # Show first 3
                print(f"   Backup Job: {job.get('backup_id')} - {job.get('status')} ({job.get('progress')}%)")
        
        # Test 8: Test Export Types
        export_types_to_test = ["agents", "workflows", "audit"]
        export_type_results = []
        
        for export_type in export_types_to_test:
            export_request = {
                "tenant_id": "tenant_export_test",
                "export_type": export_type,
                "format": "json",
                "include_metadata": True,
                "compress": False
            }
            
            success_type, type_response = self.run_test(f"Create {export_type.title()} Export", "POST", "data-export/export", 200, export_request)
            export_type_results.append(success_type)
            
            if success_type:
                print(f"   {export_type.title()} Export Created: {type_response.get('export_id')}")
        
        success8 = all(export_type_results)
        
        # Test 9: Test Multi-Format Support
        formats_to_test = ["json", "csv"]
        format_results = []
        
        for format_type in formats_to_test:
            format_request = {
                "tenant_id": "tenant_format_test",
                "export_type": "leads",
                "format": format_type,
                "include_metadata": True,
                "compress": True
            }
            
            success_format, format_response = self.run_test(f"Create {format_type.upper()} Export", "POST", "data-export/export", 200, format_request)
            format_results.append(success_format)
            
            if success_format:
                print(f"   {format_type.upper()} Export Created: {format_response.get('export_id')}")
        
        success9 = all(format_results)
        
        # Test 10: Test Cleanup Functionality
        success10, cleanup_response = self.run_test("Test Cleanup Old Files", "DELETE", "data-export/cleanup?days_to_keep=30")
        if success10:
            cleaned_exports = cleanup_response.get('cleaned_exports', 0)
            cleaned_backups = cleanup_response.get('cleaned_backups', 0)
            print(f"   Cleaned Export Files: {cleaned_exports}")
            print(f"   Cleaned Backup Files: {cleaned_backups}")
            print(f"   Cleanup Message: {cleanup_response.get('message')}")
        
        # Summary of Data Export & Backup Systems Tests
        all_export_tests = [success1, success2, success3, success4, success5, success6, success7, success8, success9, success10]
        passed_export_tests = sum(all_export_tests)
        total_export_tests = len(all_export_tests)
        
        print(f"\n📊 DATA EXPORT & BACKUP SYSTEMS TEST SUMMARY:")
        print(f"   Tests Passed: {passed_export_tests}/{total_export_tests}")
        print(f"   Success Rate: {(passed_export_tests/total_export_tests*100):.1f}%")
        
        if passed_export_tests == total_export_tests:
            print("   🎉 ALL DATA EXPORT & BACKUP SYSTEMS TESTS PASSED!")
        else:
            print("   ⚠️  Some Data Export & Backup Systems tests failed")
        
        return all(all_export_tests)

    def run_phase_6d_tests(self):
        """Run Phase 6D tests"""
        print("🚀 Starting Phase 6D: Advanced Intelligence & Voice Backend Testing...")
        print(f"🌐 Testing against: {self.base_url}")
        print("="*80)
        
        # Test categories
        test_results = []
        
        # Phase 6D: Advanced Intelligence & Voice Testing
        test_results.append(self.test_phase_6d_advanced_voice_interface())
        test_results.append(self.test_phase_6d_data_export_backup_systems())
        
        # Final summary
        print("\n" + "="*80)
        print("🏁 PHASE 6D TEST SUMMARY")
        print("="*80)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"📊 Overall Results:")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Individual Test Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print(f"   Test Categories Passed: {passed_tests}/{total_tests}")
        print(f"   Category Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests[:10], 1):  # Show first 10 failures
                print(f"   {i}. {failure.get('name', 'Unknown')}")
                if 'expected' in failure and 'actual' in failure:
                    print(f"      Expected: {failure['expected']}, Got: {failure['actual']}")
                elif 'error' in failure:
                    print(f"      Error: {failure['error']}")
        
        if success_rate >= 90:
            print("\n🎉 EXCELLENT! Phase 6D systems are working correctly!")
        elif success_rate >= 75:
            print("\n✅ GOOD! Most Phase 6D systems are working with minor issues.")
        elif success_rate >= 50:
            print("\n⚠️  MODERATE! Some Phase 6D systems need attention.")
        else:
            print("\n❌ CRITICAL! Major Phase 6D systems are failing and need immediate attention.")
        
        print(f"\n🔗 API Documentation: {self.base_url}/docs")
        print("="*80)
        
        return success_rate >= 75

if __name__ == "__main__":
    tester = Phase6DTester()
    success = tester.run_phase_6d_tests()
    sys.exit(0 if success else 1)