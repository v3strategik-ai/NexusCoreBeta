#!/usr/bin/env python3
"""
Focused Agent Configuration Testing
"""

import requests
import json
from datetime import datetime

class AgentConfigTester:
    def __init__(self, base_url="https://smartagent-nexus.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.agent_id = None

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, data: dict = None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
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
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:500]}...")
                return False, {}

        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False, {}

    def test_agent_configuration(self):
        """Test comprehensive Agent Configuration functionality"""
        print("="*60)
        print("FOCUSED AGENT CONFIGURATION TESTING")
        print("="*60)
        
        # Step 1: Create test agent
        print("\n🔍 Step 1: Creating test agent...")
        agent_data = {
            "name": "ConfigTest Agent",
            "type": "Business Analyst",
            "personality": "Professional and analytical",
            "specialization": "Data Analysis and Reporting",
            "autonomy_level": "High",
            "configuration": {
                "ai_model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
        
        success, response = self.run_test("Create Agent", "POST", "agents/", 200, agent_data)
        if not success:
            return False
        
        self.agent_id = response.get('id')
        print(f"   Agent ID: {self.agent_id}")
        
        # Step 2: Test comprehensive configuration update
        print("\n🔍 Step 2: Testing comprehensive configuration update...")
        config_update = {
            "configuration": {
                # AI model settings
                "ai_model": "claude-3.5-sonnet",
                "temperature": 0.8,
                "max_tokens": 1500,
                
                # Performance tuning
                "creativity": 0.7,
                "responsiveness": 0.9,
                "accuracy": 0.85,
                "learning_rate": 0.6,
                
                # Behavior settings
                "proactive_mode": True,
                "auto_learn": True,
                "context_memory": True,
                "task_prioritization": True,
                
                # Security settings
                "max_daily_tasks": 150,
                "restricted_topics": ["confidential", "personal"],
                "allowed_actions": ["email", "document_generation", "data_analysis"],
                
                # Integration permissions
                "integrations": {
                    "email": True,
                    "calendar": True,
                    "crm": True,
                    "documents": True
                },
                
                # System instructions
                "system_instructions": "You are a professional business analyst focused on data-driven insights and strategic recommendations.",
                "autonomy_level": "Quantum"
            }
        }
        
        success, response = self.run_test("Configuration Update", "PUT", f"agents/{self.agent_id}", 200, config_update)
        if success:
            config = response.get('configuration', {})
            metrics = response.get('metrics', {})
            
            print(f"   AI Model: {config.get('ai_model')}")
            print(f"   Temperature: {config.get('temperature')}")
            print(f"   Max Tokens: {config.get('max_tokens')}")
            print(f"   Creativity: {config.get('creativity')}")
            print(f"   Integrations: {config.get('integrations')}")
            print(f"   Config Version: {config.get('config_version')}")
            print(f"   Last Processed: {config.get('last_processed')}")
            
            print(f"\n   Metrics:")
            print(f"   Complexity Score: {metrics.get('configuration_complexity', 0)}")
            print(f"   Readiness Score: {metrics.get('readiness_score', 0)}")
            print(f"   Integrations Count: {metrics.get('integrations_count', 0)}")
            print(f"   Security Settings Count: {metrics.get('security_settings_count', 0)}")
            print(f"   Performance Customizations: {metrics.get('performance_customizations', 0)}")
        
        # Step 3: Test validation with invalid values
        print("\n🔍 Step 3: Testing validation with invalid values...")
        invalid_config = {
            "configuration": {
                "temperature": 1.5,  # Invalid - should be <= 1.0
                "creativity": -0.2,  # Invalid - should be >= 0.0
                "max_daily_tasks": -10,  # Invalid - should be positive
                "max_tokens": 5000,  # Invalid - should be <= 2000
                "ai_model": "invalid_model"  # Invalid model
            }
        }
        
        success, response = self.run_test("Validation Test", "PUT", f"agents/{self.agent_id}", 200, invalid_config)
        if success:
            config = response.get('configuration', {})
            
            print(f"   Temperature after validation: {config.get('temperature')} (should be <= 1.0)")
            print(f"   Creativity after validation: {config.get('creativity')} (should be >= 0.0)")
            print(f"   Max Daily Tasks after validation: {config.get('max_daily_tasks')} (should be >= 10)")
            print(f"   Max Tokens after validation: {config.get('max_tokens')} (should be <= 2000)")
            print(f"   AI Model after validation: {config.get('ai_model')} (should be valid model)")
        
        # Step 4: Test configuration history
        print("\n🔍 Step 4: Testing configuration history...")
        success, response = self.run_test("Configuration History", "GET", f"agents/{self.agent_id}/configuration/history")
        if success:
            history = response.get('configuration_history', [])
            print(f"   History entries: {len(history)}")
            if history:
                latest = history[0]
                print(f"   Latest change: {latest.get('description')}")
                print(f"   Changes: {latest.get('changes')}")
        
        # Step 5: Test configuration analytics
        print("\n🔍 Step 5: Testing configuration analytics...")
        success, response = self.run_test("Configuration Analytics", "GET", f"agents/{self.agent_id}/configuration/analytics")
        if success:
            analytics = response.get('analytics', {})
            print(f"   Configuration Complexity: {analytics.get('configuration_complexity', 0)}")
            print(f"   Readiness Score: {analytics.get('readiness_score', 0)}")
            print(f"   Integrations Count: {analytics.get('integrations_count', 0)}")
            print(f"   Security Settings Count: {analytics.get('security_settings_count', 0)}")
            print(f"   Performance Customizations: {analytics.get('performance_customizations', 0)}")
            print(f"   Optimization Score: {analytics.get('optimization_score', 0)}")
        
        # Step 6: Test activity logging
        print("\n🔍 Step 6: Testing activity logging...")
        success, response = self.run_test("Agent Activities", "GET", f"agents/{self.agent_id}/activities")
        if success:
            activities = response.get('activities', [])
            config_activities = [a for a in activities if a.get('activity_type') == 'configuration_updated']
            print(f"   Total activities: {len(activities)}")
            print(f"   Configuration activities: {len(config_activities)}")
            if config_activities:
                latest = config_activities[0]
                print(f"   Latest config activity: {latest.get('description')}")
        
        # Cleanup
        print("\n🔍 Cleanup: Deleting test agent...")
        self.run_test("Delete Agent", "DELETE", f"agents/{self.agent_id}", 200)
        
        return True

def main():
    tester = AgentConfigTester()
    tester.test_agent_configuration()

if __name__ == "__main__":
    main()