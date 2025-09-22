#!/usr/bin/env python3
"""
Phase 6A AI Features Testing Only
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class Phase6ATester:
    def __init__(self, base_url="https://ai-workflow-hub-21.preview.emergentagent.com"):
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
                print(f"   Response: {response.text[:500]}...")
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': response.text[:500]
                })
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timeout ({timeout}s)")
            self.failed_tests.append({'name': name, 'error': f'Timeout ({timeout}s)'})
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': name, 'error': str(e)})
            return False, {}

    def test_phase_6a_ai_features(self):
        """Test comprehensive Phase 6A AI features: Lead Scoring, Content Generation, Sentiment Analysis"""
        print("\n" + "="*50)
        print("TESTING PHASE 6A AI FEATURES")
        print("="*50)
        
        # Test 1: Predictive Lead Scoring System
        print("\n🔍 Testing Predictive Lead Scoring System...")
        
        # First get available models
        success1, models_response = self.run_test("Get Available Scoring Models", "GET", "lead-scoring/models/available")
        
        if success1:
            models = models_response.get('models', [])
            print(f"   Available Models: {len(models)}")
            if models:
                model = models[0]
                print(f"   Model: {model.get('name')} - {model.get('accuracy')}")
                print(f"   Features: {len(model.get('features', []))}")
        
        # Get existing leads for scoring tests
        success_leads, leads_response = self.run_test("Get Leads for Scoring", "GET", "crm/leads")
        test_lead_ids = []
        
        if success_leads:
            leads = leads_response.get('leads', [])
            test_lead_ids = [lead.get('id') for lead in leads[:3]]  # Use first 3 leads
            print(f"   Found {len(leads)} leads for testing")
        
        # Create a test lead if none exist
        if not test_lead_ids:
            print("   Creating test lead for scoring...")
            test_lead_data = {
                "name": "AI Test Lead",
                "email": "aitest@example.com",
                "company": "AI Test Corp",
                "status": "warm",
                "value": 75000,
                "source": "AI Testing",
                "title": "CTO"
            }
            
            success_create, create_response = self.run_test(
                "Create Test Lead for AI Scoring", "POST", "crm/leads", 200, test_lead_data
            )
            
            if success_create:
                test_lead_ids = [create_response.get('id')]
                print(f"   Created test lead: {create_response.get('name')}")
        
        # Test single lead scoring
        scoring_success = False
        if test_lead_ids:
            scoring_data = {
                "lead_id": test_lead_ids[0],
                "force_refresh": True
            }
            
            success2, scoring_response = self.run_test(
                "Single Lead Scoring", "POST", "lead-scoring/score", 200, scoring_data, timeout=60
            )
            
            if success2:
                score = scoring_response.get('score', 0)
                confidence = scoring_response.get('confidence', 0)
                factors = scoring_response.get('factors', [])
                recommendations = scoring_response.get('recommendations', [])
                
                print(f"   ✅ Lead Scored Successfully")
                print(f"   Score: {score}/100")
                print(f"   Confidence: {confidence:.2f}")
                print(f"   Factors Analyzed: {len(factors)}")
                print(f"   Recommendations: {len(recommendations)}")
                
                scoring_success = True
            else:
                print("   ❌ Single lead scoring failed")
        
        # Test bulk lead scoring if we have multiple leads
        bulk_scoring_success = True
        if len(test_lead_ids) > 1:
            bulk_data = {
                "lead_ids": test_lead_ids[:2],
                "force_refresh": True
            }
            
            success3, bulk_response = self.run_test(
                "Bulk Lead Scoring", "POST", "lead-scoring/score/bulk", 200, bulk_data
            )
            
            if success3:
                batch_id = bulk_response.get('batch_id')
                total_leads = bulk_response.get('total_leads', 0)
                print(f"   ✅ Bulk Scoring Started: {batch_id}")
                print(f"   Total Leads: {total_leads}")
                bulk_scoring_success = True
            else:
                print("   ❌ Bulk lead scoring failed")
                bulk_scoring_success = False
        
        # Test 2: AI-Powered Content Generation
        print("\n🔍 Testing AI-Powered Content Generation...")
        
        # Get available content types
        success4, types_response = self.run_test("Get Content Types", "GET", "ai-content/types")
        
        if success4:
            content_types = types_response.get('content_types', [])
            tones = types_response.get('tones', [])
            lengths = types_response.get('lengths', [])
            
            print(f"   Available Content Types: {len(content_types)}")
            print(f"   Available Tones: {len(tones)}")
            print(f"   Available Lengths: {len(lengths)}")
        
        # Test content generation with different types
        content_generation_success = True
        test_content_types = ["email", "proposal"]
        
        for content_type in test_content_types:
            content_data = {
                "content_type": content_type,
                "target_audience": "Enterprise decision makers",
                "key_points": [
                    "AI-powered business automation",
                    "Increased efficiency and ROI",
                    "Seamless integration capabilities"
                ],
                "tone": "professional",
                "length": "medium",
                "personalization_data": {
                    "company": "TechCorp Solutions",
                    "name": "Sarah Johnson",
                    "title": "CTO"
                }
            }
            
            if test_lead_ids:
                content_data["lead_id"] = test_lead_ids[0]
            
            success_content, content_response = self.run_test(
                f"Generate {content_type.title()} Content", "POST", "ai-content/generate", 200, content_data, timeout=60
            )
            
            if success_content:
                title = content_response.get('title', '')
                content = content_response.get('content', '')
                word_count = content_response.get('word_count', 0)
                alternatives = content_response.get('alternatives', [])
                
                print(f"   ✅ {content_type.title()} Generated")
                print(f"   Title: {title[:50]}...")
                print(f"   Word Count: {word_count}")
                print(f"   Content Length: {len(content)} characters")
                print(f"   Alternatives: {len(alternatives)}")
                
                # Validate content quality
                if len(content) > 100 and word_count > 20:
                    print(f"   ✅ Content quality check passed")
                else:
                    print(f"   ⚠️  Content may be too short")
            else:
                print(f"   ❌ {content_type.title()} generation failed")
                content_generation_success = False
        
        # Test 3: Sentiment Analysis Integration
        print("\n🔍 Testing Sentiment Analysis Integration...")
        
        # Test sentiment analysis with different text samples
        sentiment_test_texts = [
            {
                "text": "I'm really excited about this new AI platform! It looks like exactly what we need to streamline our operations. When can we schedule a demo?",
                "expected_sentiment": "positive",
                "source_type": "email"
            },
            {
                "text": "I'm not sure this solution is right for us. The pricing seems high and I'm concerned about the implementation complexity.",
                "expected_sentiment": "negative", 
                "source_type": "chat"
            }
        ]
        
        sentiment_analysis_success = True
        sentiment_results = []
        
        for i, test_case in enumerate(sentiment_test_texts):
            sentiment_data = {
                "text": test_case["text"],
                "source_type": test_case["source_type"],
                "context": "Business communication analysis"
            }
            
            if test_lead_ids:
                sentiment_data["lead_id"] = test_lead_ids[0]
            
            success_sentiment, sentiment_response = self.run_test(
                f"Sentiment Analysis Test {i+1}", "POST", "sentiment/analyze", 200, sentiment_data, timeout=60
            )
            
            if success_sentiment:
                sentiment = sentiment_response.get('sentiment', 'unknown')
                confidence = sentiment_response.get('confidence', 0)
                emotions = sentiment_response.get('emotions', {})
                urgency = sentiment_response.get('urgency_level', 'unknown')
                recommendations = sentiment_response.get('recommendations', [])
                
                print(f"   ✅ Analysis {i+1}: {sentiment} ({confidence:.2f} confidence)")
                print(f"   Urgency: {urgency}")
                print(f"   Emotions: {len(emotions)} detected")
                print(f"   Recommendations: {len(recommendations)}")
                
                sentiment_results.append({
                    'sentiment': sentiment,
                    'expected': test_case['expected_sentiment'],
                    'confidence': confidence
                })
            else:
                print(f"   ❌ Sentiment analysis {i+1} failed")
                sentiment_analysis_success = False
        
        # Test sentiment dashboard
        success_dashboard, dashboard_response = self.run_test("Sentiment Dashboard", "GET", "sentiment/dashboard")
        
        if success_dashboard:
            summary = dashboard_response.get('summary', {})
            recent_analyses = dashboard_response.get('recent_analyses', [])
            
            print(f"   ✅ Dashboard Retrieved")
            print(f"   Total Analyses: {summary.get('total_analyses', 0)}")
            print(f"   Recent Analyses: {len(recent_analyses)}")
            
            distribution = summary.get('sentiment_distribution', {})
            print(f"   Sentiment Distribution: {distribution}")
        
        # Clean up test lead if we created one
        if test_lead_ids and not success_leads:  # Only if we created it
            cleanup_success, _ = self.run_test(
                "Delete AI Test Lead", "DELETE", f"crm/leads/{test_lead_ids[0]}", 200
            )
            if cleanup_success:
                print("   ✅ Test lead cleaned up")
        
        # Summary of Phase 6A AI Features Tests
        all_tests = [success1, scoring_success, bulk_scoring_success, success4, 
                    content_generation_success, sentiment_analysis_success, success_dashboard]
        passed_tests = sum(all_tests)
        total_tests = len(all_tests)
        
        print(f"\n📊 PHASE 6A AI FEATURES TEST SUMMARY:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Detailed results
        print(f"\n   🎯 Lead Scoring: {'✅' if scoring_success else '❌'}")
        print(f"   🎯 Content Generation: {'✅' if content_generation_success else '❌'}")
        print(f"   🎯 Sentiment Analysis: {'✅' if sentiment_analysis_success else '❌'}")
        
        if passed_tests == total_tests:
            print("   🎉 ALL PHASE 6A AI FEATURES TESTS PASSED!")
        else:
            print("   ⚠️  Some Phase 6A AI features tests failed")
        
        return all(all_tests)

if __name__ == "__main__":
    tester = Phase6ATester()
    success = tester.test_phase_6a_ai_features()
    
    print(f"\n📊 FINAL SUMMARY:")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {len(tester.failed_tests)}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.failed_tests:
        print("\n❌ FAILED TESTS:")
        for i, failure in enumerate(tester.failed_tests, 1):
            print(f"{i}. {failure['name']}")
            if 'expected' in failure and 'actual' in failure:
                print(f"   Expected: {failure['expected']}, Got: {failure['actual']}")
            if 'error' in failure:
                print(f"   Error: {failure['error']}")
            if 'response' in failure:
                print(f"   Response: {failure['response'][:200]}...")
    
    sys.exit(0 if success else 1)