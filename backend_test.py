#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Nexus Core AI Business Automation Platform
Tests all API endpoints, data integration, and business logic
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class NexusCoreAPITester:
    def __init__(self, base_url="https://continue-work-24.preview.emergentagent.com"):
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

    def test_health_check(self):
        """Test API health check"""
        success, response = self.run_test("Health Check", "GET", "health")
        if success:
            print(f"   Database Status: {response.get('database', 'unknown')}")
            print(f"   API Status: {response.get('status', 'unknown')}")
        return success

    def test_root_endpoints(self):
        """Test root API endpoints"""
        print("\n" + "="*50)
        print("TESTING ROOT ENDPOINTS")
        print("="*50)
        
        # Test main root endpoint
        success1, _ = self.run_test("Root Endpoint", "GET", "", 200)
        
        # Test API root endpoint  
        success2, response = self.run_test("API Root", "GET", "/")
        if success2:
            print(f"   API Version: {response.get('version', 'unknown')}")
            print(f"   Features: {len(response.get('features', []))}")
        
        return success1 and success2

    def test_dashboard_endpoints(self):
        """Test dashboard API endpoints"""
        print("\n" + "="*50)
        print("TESTING DASHBOARD ENDPOINTS")
        print("="*50)
        
        # Test dashboard metrics
        success1, metrics = self.run_test("Dashboard Metrics", "GET", "dashboard/metrics")
        if success1:
            print(f"   Active Agents: {metrics.get('active_agents', 0)}")
            print(f"   Total Tasks: {metrics.get('total_tasks_completed', 0)}")
            print(f"   Revenue: ${metrics.get('total_revenue_generated', 0):,}")
            print(f"   Efficiency: {metrics.get('system_efficiency', 0)}%")
            
            # Validate expected metrics structure
            expected_fields = ['active_agents', 'total_tasks_completed', 'total_revenue_generated', 'system_efficiency']
            missing_fields = [field for field in expected_fields if field not in metrics]
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
        
        # Test dashboard activities
        success2, activities = self.run_test("Dashboard Activities", "GET", "dashboard/activities")
        if success2:
            activity_count = len(activities.get('activities', []))
            print(f"   Recent Activities: {activity_count}")
        
        # Test full dashboard
        success3, dashboard = self.run_test("Full Dashboard", "GET", "dashboard/")
        
        return success1 and success2 and success3

    def test_agents_endpoints(self):
        """Test agents/digital employees API endpoints"""
        print("\n" + "="*50)
        print("TESTING AGENTS ENDPOINTS")
        print("="*50)
        
        # Test get all agents
        success1, agents_response = self.run_test("Get All Agents", "GET", "agents/")
        agents_data = []
        if success1:
            agents_data = agents_response.get('agents', [])
            total_agents = agents_response.get('total', 0)
            print(f"   Total Agents: {total_agents}")
            print(f"   Agents Retrieved: {len(agents_data)}")
            
            if agents_data:
                # Show agent details
                for i, agent in enumerate(agents_data[:3]):  # Show first 3
                    print(f"   Agent {i+1}: {agent.get('name', 'Unknown')} - {agent.get('status', 'Unknown')} - {agent.get('efficiency', 0)}%")
        
        # Test individual agent if we have agents
        agent_test_success = True
        if agents_data:
            first_agent_id = agents_data[0].get('id')
            if first_agent_id:
                success2, agent_detail = self.run_test("Get Individual Agent", "GET", f"agents/{first_agent_id}")
                if success2:
                    print(f"   Agent Detail: {agent_detail.get('name')} - {agent_detail.get('type')}")
                agent_test_success = success2
        
        return success1 and agent_test_success

    def test_crm_endpoints(self):
        """Test CRM API endpoints"""
        print("\n" + "="*50)
        print("TESTING CRM ENDPOINTS")
        print("="*50)
        
        # Test get all leads
        success1, leads_response = self.run_test("Get All Leads", "GET", "crm/leads")
        leads_data = []
        if success1:
            leads_data = leads_response.get('leads', [])
            total_leads = leads_response.get('total', 0)
            print(f"   Total Leads: {total_leads}")
            print(f"   Leads Retrieved: {len(leads_data)}")
            
            if leads_data:
                # Calculate pipeline value
                total_pipeline = sum(lead.get('value', 0) for lead in leads_data)
                hot_leads = len([lead for lead in leads_data if lead.get('status') == 'hot'])
                converted_leads = len([lead for lead in leads_data if lead.get('status') == 'converted'])
                
                print(f"   Pipeline Value: ${total_pipeline:,}")
                print(f"   Hot Leads: {hot_leads}")
                print(f"   Converted Leads: {converted_leads}")
                
                # Show lead details
                for i, lead in enumerate(leads_data[:3]):  # Show first 3
                    print(f"   Lead {i+1}: {lead.get('name', 'Unknown')} - {lead.get('status', 'Unknown')} - ${lead.get('value', 0):,}")
        
        # Test CRM analytics
        success2, analytics = self.run_test("CRM Analytics", "GET", "crm/analytics/summary")
        if success2:
            print(f"   Analytics - Total Pipeline: ${analytics.get('total_pipeline_value', 0):,}")
            print(f"   Analytics - Conversion Rate: {analytics.get('conversion_rate', 0)}%")
        
        # Test individual lead if we have leads
        lead_test_success = True
        if leads_data:
            first_lead_id = leads_data[0].get('id')
            if first_lead_id:
                success3, lead_detail = self.run_test("Get Individual Lead", "GET", f"crm/leads/{first_lead_id}")
                if success3:
                    print(f"   Lead Detail: {lead_detail.get('name')} - {lead_detail.get('email')}")
                lead_test_success = success3
        
        return success1 and success2 and lead_test_success

    def test_business_logic(self):
        """Test business logic and data consistency"""
        print("\n" + "="*50)
        print("TESTING BUSINESS LOGIC & DATA CONSISTENCY")
        print("="*50)
        
        # Get dashboard metrics
        success1, metrics = self.run_test("Metrics for Logic Test", "GET", "dashboard/metrics")
        
        # Get agents data
        success2, agents_response = self.run_test("Agents for Logic Test", "GET", "agents/")
        
        # Get leads data
        success3, leads_response = self.run_test("Leads for Logic Test", "GET", "crm/leads")
        
        if success1 and success2 and success3:
            agents = agents_response.get('agents', [])
            leads = leads_response.get('leads', [])
            
            # Verify agent count consistency
            active_agents_from_metrics = metrics.get('active_agents', 0)
            active_agents_actual = len([a for a in agents if a.get('status') == 'active'])
            
            print(f"   Active Agents (Metrics): {active_agents_from_metrics}")
            print(f"   Active Agents (Actual): {active_agents_actual}")
            
            if active_agents_from_metrics == active_agents_actual:
                print("   ✅ Agent count consistency: PASSED")
            else:
                print("   ❌ Agent count consistency: FAILED")
                self.failed_tests.append({
                    'name': 'Agent Count Consistency',
                    'expected': active_agents_actual,
                    'actual': active_agents_from_metrics
                })
            
            # Verify revenue calculation
            converted_leads = [l for l in leads if l.get('status') == 'converted']
            calculated_revenue = sum(lead.get('value', 0) for lead in converted_leads)
            metrics_revenue = metrics.get('total_revenue_generated', 0)
            
            print(f"   Revenue (Calculated): ${calculated_revenue:,}")
            print(f"   Revenue (Metrics): ${metrics_revenue:,}")
            
            if abs(calculated_revenue - metrics_revenue) < 0.01:  # Allow for small floating point differences
                print("   ✅ Revenue calculation: PASSED")
            else:
                print("   ❌ Revenue calculation: FAILED")
                self.failed_tests.append({
                    'name': 'Revenue Calculation',
                    'expected': calculated_revenue,
                    'actual': metrics_revenue
                })
            
            # Verify lead assignment
            assigned_leads = [l for l in leads if l.get('assigned_agent_id')]
            print(f"   Assigned Leads: {len(assigned_leads)}/{len(leads)}")
            
            # Check if assigned agents exist
            agent_ids = [a.get('id') for a in agents]
            invalid_assignments = []
            for lead in assigned_leads:
                if lead.get('assigned_agent_id') not in agent_ids:
                    invalid_assignments.append(lead.get('name', 'Unknown'))
            
            if not invalid_assignments:
                print("   ✅ Lead assignment integrity: PASSED")
            else:
                print(f"   ❌ Lead assignment integrity: FAILED - {len(invalid_assignments)} invalid assignments")
                self.failed_tests.append({
                    'name': 'Lead Assignment Integrity',
                    'error': f'{len(invalid_assignments)} leads assigned to non-existent agents'
                })
        
        return success1 and success2 and success3

    def test_expected_data_values(self):
        """Test that the platform shows expected demo data values"""
        print("\n" + "="*50)
        print("TESTING EXPECTED DEMO DATA VALUES")
        print("="*50)
        
        success, metrics = self.run_test("Expected Values Check", "GET", "dashboard/metrics")
        if success:
            # Expected values from the review request
            expected_active_agents = 5  # Should be around 5 active agents
            expected_total_tasks = 134  # Should be around 134 total tasks
            expected_revenue = 35000  # Should be around $35,000 revenue
            expected_efficiency = 90  # Should be around 90% efficiency
            
            actual_agents = metrics.get('active_agents', 0)
            actual_tasks = metrics.get('total_tasks_completed', 0)
            actual_revenue = metrics.get('total_revenue_generated', 0)
            actual_efficiency = metrics.get('system_efficiency', 0)
            
            print(f"   Expected vs Actual:")
            print(f"   Active Agents: {expected_active_agents} vs {actual_agents}")
            print(f"   Total Tasks: {expected_total_tasks} vs {actual_tasks}")
            print(f"   Revenue: ${expected_revenue:,} vs ${actual_revenue:,}")
            print(f"   Efficiency: {expected_efficiency}% vs {actual_efficiency}%")
            
            # Check if values are in reasonable range (allowing some variance)
            agents_ok = abs(actual_agents - expected_active_agents) <= 2
            tasks_ok = abs(actual_tasks - expected_total_tasks) <= 20
            revenue_ok = abs(actual_revenue - expected_revenue) <= 10000
            efficiency_ok = abs(actual_efficiency - expected_efficiency) <= 10
            
            if agents_ok and tasks_ok and revenue_ok and efficiency_ok:
                print("   ✅ Demo data values are within expected ranges")
            else:
                print("   ⚠️  Some demo data values are outside expected ranges")
                if not agents_ok:
                    print(f"      - Active agents variance too high")
                if not tasks_ok:
                    print(f"      - Total tasks variance too high")
                if not revenue_ok:
                    print(f"      - Revenue variance too high")
                if not efficiency_ok:
                    print(f"      - Efficiency variance too high")
        
        return success

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Nexus Core Backend API Testing")
        print("=" * 60)
        
        # Test health first
        if not self.test_health_check():
            print("\n❌ Health check failed - stopping tests")
            return False
        
        # Run all test suites
        test_results = [
            self.test_root_endpoints(),
            self.test_dashboard_endpoints(),
            self.test_agents_endpoints(),
            self.test_crm_endpoints(),
            self.test_business_logic(),
            self.test_expected_data_values()
        ]
        
        # Print summary
        print("\n" + "="*60)
        print("📊 BACKEND API TEST SUMMARY")
        print("="*60)
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
            print("\n🎉 ALL BACKEND TESTS PASSED!")
        else:
            print(f"\n⚠️  {len([r for r in test_results if not r])} test suite(s) had failures")
        
        return all_passed

def main():
    """Main test execution"""
    tester = NexusCoreAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())