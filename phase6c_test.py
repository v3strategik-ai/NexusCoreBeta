#!/usr/bin/env python3
"""
Phase 6C Enterprise Architecture Testing
Tests Multi-Tenant Architecture, RBAC, and Audit Logging
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class Phase6CEnterpriseTester:
    def __init__(self, base_url="https://smartagent-nexus.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, data: Dict[Any, Any] = None, headers: Dict[str, str] = None, timeout: int = 10) -> tuple:
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

    def test_multi_tenant_architecture(self):
        """Test Phase 6C Multi-Tenant Architecture endpoints"""
        print("\n" + "="*50)
        print("TESTING PHASE 6C: MULTI-TENANT ARCHITECTURE")
        print("="*50)
        
        # Store created tenant ID for subsequent tests
        created_tenant_id = None
        
        # Test 1: Create Tenant
        print("\n🔍 Testing Tenant Creation...")
        import time
        unique_suffix = str(int(time.time()))[-6:]  # Use timestamp for uniqueness
        tenant_create_data = {
            "name": "TechCorp Enterprise",
            "subdomain": f"techcorp-{unique_suffix}",
            "admin_email": f"admin-{unique_suffix}@techcorp.com",
            "admin_first_name": "John",
            "admin_last_name": "Smith",
            "plan_type": "enterprise",
            "max_users": 100,
            "max_agents": 50
        }
        
        success1, create_response = self.run_test(
            "Create Enterprise Tenant", "POST", "tenants/", 200, tenant_create_data
        )
        
        if success1:
            created_tenant_id = create_response.get('id')
            print(f"   ✅ Tenant Created: {create_response.get('name')}")
            print(f"   Tenant ID: {created_tenant_id}")
            print(f"   Subdomain: {create_response.get('subdomain')}")
            print(f"   Plan Type: {create_response.get('plan_type')}")
            print(f"   Max Users: {create_response.get('max_users')}")
            print(f"   Current Users: {create_response.get('current_users')}")
        
        # Test 2: Get All Tenants
        success2, tenants_response = self.run_test("Get All Tenants", "GET", "tenants/")
        if success2:
            tenant_count = len(tenants_response)
            print(f"   Total Tenants: {tenant_count}")
        
        # Test 3: Get Tenant by Subdomain (Routing Test)
        success3 = False
        if created_tenant_id:
            subdomain = tenant_create_data["subdomain"]  # Use the dynamic subdomain
            success3, subdomain_response = self.run_test(
                "Get Tenant by Subdomain", "GET", f"tenants/subdomain/{subdomain}"
            )
            
            if success3:
                subdomain_tenant_id = subdomain_response.get('id')
                print(f"   ✅ Subdomain Routing: Found tenant {subdomain_tenant_id}")
        
        # Test 4: Update Tenant (White-Label Branding)
        success4 = False
        if created_tenant_id:
            print("\n🔍 Testing White-Label Branding Update...")
            branding_update = {
                "branding": {
                    "company_name": "TechCorp Solutions",
                    "primary_color": "#ff6b35",
                    "secondary_color": "#004e89",
                    "logo_url": "https://techcorp.com/logo.png"
                }
            }
            
            success4, update_response = self.run_test(
                "Update Tenant Branding", "PUT", f"tenants/{created_tenant_id}", 200, branding_update
            )
            
            if success4:
                updated_branding = update_response.get('branding', {})
                print(f"   ✅ Branding Updated: {updated_branding.get('company_name')}")
        
        # Test 5: Usage Tracking Update
        success5 = False
        if created_tenant_id:
            print("\n🔍 Testing Usage Tracking...")
            success5, usage_response = self.run_test(
                "Update Tenant Usage", "POST", f"tenants/{created_tenant_id}/usage/update", 200, {}
            )
            
            if success5:
                print(f"   ✅ Usage tracking updated: {usage_response.get('message')}")
        
        return [success1, success2, success3, success4, success5]

    def test_role_based_access_control(self):
        """Test Phase 6C Role-Based Access Control (RBAC) endpoints"""
        print("\n" + "="*50)
        print("TESTING PHASE 6C: ROLE-BASED ACCESS CONTROL (RBAC)")
        print("="*50)
        
        # Test 1: Get Role Permissions Matrix
        print("\n🔍 Testing Role Permissions Matrix...")
        success1, permissions_response = self.run_test("Get Role Permissions", "GET", "users/roles/permissions")
        
        if success1:
            roles = list(permissions_response.keys())
            print(f"   Available Roles: {roles}")
            
            # Validate expected roles
            expected_roles = ['super_admin', 'tenant_admin', 'manager', 'employee']
            found_roles = [role for role in expected_roles if role in roles]
            print(f"   Expected Roles Found: {len(found_roles)}/{len(expected_roles)}")
        
        # Test 2: Get Tenants for User Creation
        success2, tenants_response = self.run_test("Get Tenants for RBAC", "GET", "tenants/")
        test_tenant_id = None
        
        if success2 and tenants_response:
            test_tenant_id = tenants_response[0].get('id')
            print(f"   Using Tenant ID: {test_tenant_id}")
        
        # Test 3: Create User with Role
        success3 = False
        created_user_id = None
        
        if test_tenant_id:
            print("\n🔍 Testing User Creation with Role Assignment...")
            user_data = {
                "tenant_id": test_tenant_id,
                "email": "manager@testcorp.com",
                "username": "manager.user",
                "first_name": "Manager",
                "last_name": "User",
                "password": "SecurePass123!",
                "role": "manager",
                "phone": "+1-555-0102"
            }
            
            success3, create_response = self.run_test(
                "Create Manager User", "POST", "users/", 200, user_data
            )
            
            if success3:
                created_user_id = create_response.get('id')
                print(f"   ✅ Manager User Created: {create_response.get('username')}")
                print(f"   User ID: {created_user_id}")
                print(f"   Role: {create_response.get('role')}")
        
        # Test 4: Get Tenant Users
        success4 = False
        if test_tenant_id:
            success4, tenant_users_response = self.run_test(
                "Get Tenant Users", "GET", f"users/tenant/{test_tenant_id}"
            )
            
            if success4:
                tenant_users = tenant_users_response
                print(f"   ✅ Tenant Users Retrieved: {len(tenant_users)}")
        
        # Test 5: Get User Permissions
        success5 = False
        if created_user_id:
            success5, permissions_response = self.run_test(
                "Get User Permissions", "GET", f"users/{created_user_id}/permissions"
            )
            
            if success5:
                user_permissions = permissions_response
                print(f"   User Permissions: {len(user_permissions)} permissions")
        
        return [success1, success2, success3, success4, success5]

    def test_audit_logging_system(self):
        """Test Phase 6C Audit Logging System endpoints"""
        print("\n" + "="*50)
        print("TESTING PHASE 6C: AUDIT LOGGING SYSTEM")
        print("="*50)
        
        # Test 1: Get Audit Logs
        print("\n🔍 Testing Basic Audit Log Retrieval...")
        success1, logs_response = self.run_test("Get Audit Logs", "GET", "audit/logs")
        
        if success1:
            logs = logs_response
            print(f"   ✅ Audit Logs Retrieved: {len(logs)} entries")
            
            if logs:
                first_log = logs[0]
                print(f"   Sample Log - Action: {first_log.get('action')}")
                print(f"   Resource Type: {first_log.get('resource_type')}")
                print(f"   Success: {first_log.get('success')}")
        
        # Test 2: Get Available Actions
        success2, actions_response = self.run_test("Get Available Actions", "GET", "audit/actions")
        
        if success2:
            actions = actions_response
            print(f"   ✅ Available Actions: {len(actions)} action types")
        
        # Test 3: Get Resource Types
        success3, resource_types_response = self.run_test("Get Resource Types", "GET", "audit/resource-types")
        
        if success3:
            resource_types = resource_types_response
            print(f"   ✅ Resource Types: {len(resource_types)} types")
        
        # Test 4: Audit Statistics
        print("\n🔍 Testing Audit Statistics...")
        success4, stats_response = self.run_test("Get Audit Statistics", "GET", "audit/stats")
        
        if success4:
            stats = stats_response
            total_actions = stats.get('total_actions', 0)
            successful_actions = stats.get('successful_actions', 0)
            failed_actions = stats.get('failed_actions', 0)
            unique_users = stats.get('unique_users', 0)
            
            print(f"   ✅ Audit Statistics Retrieved:")
            print(f"     Total Actions: {total_actions}")
            print(f"     Successful: {successful_actions}")
            print(f"     Failed: {failed_actions}")
            print(f"     Unique Users: {unique_users}")
        
        # Test 5: Export Audit Logs
        print("\n🔍 Testing Audit Log Export...")
        success5, export_response = self.run_test(
            "Export Audit Logs", "GET", "audit/export?format=json&limit=50"
        )
        
        if success5:
            export_logs = export_response.get('logs', [])
            export_count = export_response.get('count', 0)
            print(f"   ✅ Export Completed: {export_count} logs")
        
        return [success1, success2, success3, success4, success5]

    def run_phase6c_tests(self):
        """Run all Phase 6C enterprise architecture tests"""
        print("🚀 Starting Phase 6C Enterprise Architecture Testing")
        print("=" * 80)
        
        # Run test suites
        tenant_results = self.test_multi_tenant_architecture()
        rbac_results = self.test_role_based_access_control()
        audit_results = self.test_audit_logging_system()
        
        # Calculate results
        all_results = tenant_results + rbac_results + audit_results
        passed_tests = sum(all_results)
        total_tests = len(all_results)
        
        # Print summary
        print("\n" + "="*80)
        print("📊 PHASE 6C ENTERPRISE ARCHITECTURE TEST SUMMARY")
        print("="*80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        print(f"   Multi-Tenant Architecture: {sum(tenant_results)}/{len(tenant_results)} tests passed")
        print(f"   Role-Based Access Control: {sum(rbac_results)}/{len(rbac_results)} tests passed")
        print(f"   Audit Logging System: {sum(audit_results)}/{len(audit_results)} tests passed")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for i, failed_test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failed_test['name']}")
                if 'expected' in failed_test:
                    print(f"      Expected: {failed_test['expected']}, Got: {failed_test['actual']}")
                if 'error' in failed_test:
                    print(f"      Error: {failed_test['error']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = Phase6CEnterpriseTester()
    success = tester.run_phase6c_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())