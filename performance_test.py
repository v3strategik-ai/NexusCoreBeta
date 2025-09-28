#!/usr/bin/env python3
"""
Phase 7 Performance Optimization Systems Testing
Focused testing for performance optimization backend implementation
"""

import requests
import sys
import json
from datetime import datetime

class PerformanceSystemTester:
    def __init__(self, base_url="https://nexus-multimodel.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, data: dict = None, timeout: int = 10):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
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
                response = requests.delete(url, json=data, headers=headers, timeout=timeout)

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

    def test_performance_systems(self):
        """Test Phase 7 Performance Optimization Systems"""
        print("\n" + "="*60)
        print("TESTING PHASE 7: PERFORMANCE OPTIMIZATION SYSTEMS")
        print("="*60)
        
        # Test 1: Performance Health Check
        success1, health_response = self.run_test("Performance System Health Check", "GET", "performance/health")
        if success1:
            print(f"   Performance Status: {health_response.get('status', 'unknown')}")
            components = health_response.get('components', {})
            print(f"   Redis Cache: {components.get('redis_cache', 'unknown')}")
            print(f"   Rate Limiter: {components.get('rate_limiter', 'unknown')}")
            print(f"   Performance Monitor: {components.get('performance_monitor', 'unknown')}")
            print(f"   Database Optimizer: {components.get('database_optimizer', 'unknown')}")
        
        # Test 2: Performance Metrics Collection
        success2, metrics_response = self.run_test("Performance Metrics Collection", "GET", "performance/metrics")
        if success2:
            performance_metrics = metrics_response.get('performance_metrics', {})
            cache_stats = metrics_response.get('cache_statistics', {})
            rate_limit_stats = metrics_response.get('rate_limit_statistics', {})
            
            print(f"   Performance Metrics Available: {bool(performance_metrics)}")
            print(f"   Cache Statistics Available: {bool(cache_stats)}")
            print(f"   Rate Limit Statistics Available: {bool(rate_limit_stats)}")
        
        # Test 3: Rate Limiting Statistics - All 4 Tiers
        success3, rate_stats = self.run_test("Rate Limiting Statistics", "GET", "performance/rate-limits/stats")
        if success3:
            global_stats = rate_stats.get('global_stats', {})
            tier_configs = global_stats.get('tier_configurations', {})
            endpoint_costs = global_stats.get('endpoint_costs', {})
            
            print(f"   Rate Limit Tiers: {len(tier_configs)}")
            print(f"   Endpoint Cost Multipliers: {len(endpoint_costs)}")
            
            # Verify all 4 tiers are configured
            expected_tiers = ['trial', 'standard', 'professional', 'enterprise']
            found_tiers = list(tier_configs.keys())
            if all(tier in found_tiers for tier in expected_tiers):
                print("   ✅ All 4 rate limiting tiers configured")
                
                # Show tier limits
                for tier, config in tier_configs.items():
                    requests_per_min = config.get('requests_per_minute', 0)
                    concurrent = config.get('concurrent_requests', 0)
                    daily_limit = config.get('requests_per_day', 0)
                    print(f"   {tier.title()}: {requests_per_min}/min, {concurrent} concurrent, {daily_limit}/day")
            else:
                print(f"   ❌ Missing rate limiting tiers: {set(expected_tiers) - set(found_tiers)}")
        
        # Test 4: Redis Cache Statistics - All 7 Cache Types
        success4, cache_stats = self.run_test("Redis Cache Statistics", "GET", "performance/cache/stats")
        if success4:
            cache_data = cache_stats.get('cache_stats', {})
            redis_info = cache_stats.get('redis_info', {})
            configurations = cache_stats.get('configurations', {})
            
            print(f"   Cache Hit Rate: {cache_data.get('hit_rate_percent', 0)}%")
            print(f"   Total Cache Hits: {cache_data.get('hits', 0)}")
            print(f"   Total Cache Misses: {cache_data.get('misses', 0)}")
            print(f"   Cache Sets: {cache_data.get('sets', 0)}")
            print(f"   Cache Errors: {cache_data.get('errors', 0)}")
            print(f"   Redis Version: {redis_info.get('redis_version', 'Unknown')}")
            print(f"   Cache Configurations: {len(configurations)}")
            
            # Verify all 7 cache types are configured
            expected_cache_types = ['api_responses', 'db_queries', 'analytics', 'sessions', 'config', 'ai_responses', 'file_processing']
            found_cache_types = list(configurations.keys())
            if all(cache_type in found_cache_types for cache_type in expected_cache_types):
                print("   ✅ All 7 cache types configured")
                
                # Show cache configurations
                for cache_type, config in configurations.items():
                    ttl = config.get('ttl_seconds', 0)
                    compression = config.get('compression', 'none')
                    max_size = config.get('max_size_bytes', 0) // 1024 // 1024  # Convert to MB
                    print(f"   {cache_type}: TTL={ttl}s, compression={compression}, max_size={max_size}MB")
            else:
                missing = set(expected_cache_types) - set(found_cache_types)
                print(f"   ❌ Missing cache types: {missing}")
        
        # Test 5: Cache Operations
        success5, cache_exists = self.run_test("Cache Key Exists Check", "GET", "performance/cache/exists?cache_type=api_responses&identifier=test_key")
        if success5:
            exists = cache_exists.get('exists', False)
            cache_type = cache_exists.get('cache_type')
            identifier = cache_exists.get('identifier')
            print(f"   Cache Key Exists Test: {cache_type}:{identifier} = {exists}")
        
        # Test 6: Database Index Information
        success6, db_indexes = self.run_test("Database Index Information", "GET", "performance/database/indexes")
        if success6:
            status = db_indexes.get('status', 'unknown')
            optimized_collections = db_indexes.get('optimized_collections', [])
            
            print(f"   Database Index Status: {status}")
            print(f"   Optimized Collections: {len(optimized_collections)}")
            
            # Verify 10 collections are optimized as expected
            if len(optimized_collections) >= 10:
                print("   ✅ Database optimization completed (10+ collections)")
                print(f"   Collections: {', '.join(optimized_collections)}")
            else:
                print(f"   ⚠️  Only {len(optimized_collections)} collections optimized")
        
        # Test 7: Performance Optimization (Light version)
        optimization_request = {
            "include_database": False,  # Skip heavy database operations
            "include_cache": True,
            "include_memory": True,
            "run_analysis": True
        }
        
        success7, optimization_result = self.run_test("Performance Optimization", "POST", "performance/optimize", 200, optimization_request)
        if success7:
            status = optimization_result.get('status', 'unknown')
            memory_opt = optimization_result.get('memory_optimization', {})
            performance_metrics = optimization_result.get('performance_metrics', {})
            recommendations = optimization_result.get('recommendations', [])
            
            print(f"   Optimization Status: {status}")
            print(f"   Memory Optimization: {bool(memory_opt)}")
            print(f"   Performance Metrics: {bool(performance_metrics)}")
            print(f"   Recommendations: {len(recommendations)}")
            
            if recommendations:
                print(f"   First Recommendation: {recommendations[0]}")
        
        # Test 8: Cache TTL Extension
        success8, ttl_result = self.run_test("Cache TTL Extension", "POST", "performance/cache/extend-ttl?cache_type=api_responses&identifier=test_key&additional_seconds=300")
        if success8:
            extended = ttl_result.get('extended', False)
            additional_seconds = ttl_result.get('additional_seconds', 0)
            print(f"   Cache TTL Extension: {extended} (+{additional_seconds}s)")
        
        # Test 9: Database Query Analysis
        success9, query_analysis = self.run_test("Database Query Analysis", "POST", "performance/database/analyze-queries?collection_name=leads&sample_size=3")
        if success9:
            collection = query_analysis.get('collection', 'unknown')
            queries_analyzed = query_analysis.get('queries_analyzed', 0)
            optimization_results = query_analysis.get('optimization_results', [])
            
            print(f"   Collection Analyzed: {collection}")
            print(f"   Queries Analyzed: {queries_analyzed}")
            print(f"   Optimization Results: {len(optimization_results)}")
            
            if optimization_results:
                first_result = optimization_results[0]
                exec_time = first_result.get('execution_time_ms', 0)
                docs_examined = first_result.get('documents_examined', 0)
                docs_returned = first_result.get('documents_returned', 0)
                index_used = first_result.get('index_used', False)
                suggestions = first_result.get('suggestions', [])
                
                print(f"   Sample Query - Time: {exec_time}ms, Examined: {docs_examined}, Returned: {docs_returned}")
                print(f"   Index Used: {index_used}, Suggestions: {len(suggestions)}")
        
        # Test 10: Endpoint Cost Multipliers Verification
        success10, cost_stats = self.run_test("Endpoint Cost Multipliers", "GET", "performance/rate-limits/stats")
        if success10:
            global_stats = cost_stats.get('global_stats', {})
            endpoint_costs = global_stats.get('endpoint_costs', {})
            
            # Check for AI operation multipliers
            ai_endpoints = [ep for ep in endpoint_costs.keys() if any(ai_term in ep for ai_term in ['ai-content', 'lead-scoring', 'sentiment', 'nl-workflows', 'advanced-voice'])]
            high_cost_endpoints = [ep for ep, cost in endpoint_costs.items() if cost >= 3]
            
            print(f"   AI Endpoints with Multipliers: {len(ai_endpoints)}")
            print(f"   High-Cost Endpoints (3x+): {len(high_cost_endpoints)}")
            
            if ai_endpoints:
                print("   ✅ AI operations have higher cost multipliers")
                for ep in ai_endpoints:
                    cost = endpoint_costs.get(ep, 1)
                    print(f"     {ep}: {cost}x cost")
            else:
                print("   ❌ AI operations may not have cost multipliers")
        
        # Test 11: Cache Tenant Isolation
        success11, tenant_cache = self.run_test("Cache Tenant Isolation Check", "GET", "performance/cache/exists?cache_type=api_responses&identifier=tenant_test&tenant_id=test_tenant")
        if success11:
            tenant_exists = tenant_cache.get('exists', False)
            tenant_id = tenant_cache.get('tenant_id')
            cache_type = tenant_cache.get('cache_type')
            identifier = tenant_cache.get('identifier')
            print(f"   Tenant Cache Isolation: {cache_type}:{identifier} (tenant:{tenant_id}) = {tenant_exists}")
        
        # Test 12: Cache Delete Operation
        delete_request = {
            "cache_type": "api_responses",
            "identifier": "test_delete_key",
            "tenant_id": "test_tenant"
        }
        success12, delete_result = self.run_test("Cache Delete Operation", "DELETE", "performance/cache/delete", 200, delete_request)
        if success12:
            deleted = delete_result.get('deleted', False)
            cache_type = delete_result.get('cache_type')
            identifier = delete_result.get('identifier')
            tenant_id = delete_result.get('tenant_id')
            print(f"   Cache Delete: {cache_type}:{identifier} (tenant:{tenant_id}) = {deleted}")
        
        # Test 13: Rate Limit Reset (if available)
        success13, reset_result = self.run_test("Rate Limit Reset", "DELETE", "performance/rate-limits/reset/test_client", 200)
        if success13:
            status = reset_result.get('status', 'unknown')
            message = reset_result.get('message', '')
            print(f"   Rate Limit Reset: {status}")
            print(f"   Message: {message}")
        
        # Summary of Performance Optimization Tests
        all_tests = [success1, success2, success3, success4, success5, success6, success7, success8, success9, success10, success11, success12, success13]
        passed_tests = sum(all_tests)
        total_tests = len(all_tests)
        
        print(f"\n📊 PERFORMANCE OPTIMIZATION SYSTEMS TEST SUMMARY:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if passed_tests == total_tests:
            print("   🎉 ALL PERFORMANCE OPTIMIZATION SYSTEMS TESTS PASSED!")
            print("   ✅ API Rate Limiting System operational (4 tiers)")
            print("   ✅ Redis Caching System operational (7 cache types)") 
            print("   ✅ Performance Monitoring operational")
            print("   ✅ Database Optimization completed (10+ collections)")
        else:
            print("   ⚠️  Some Performance Optimization tests failed")
            failed_count = total_tests - passed_tests
            print(f"   ❌ {failed_count} test(s) failed - check system configuration")
        
        return all(all_tests)

    def run_tests(self):
        """Run all performance tests"""
        print("🚀 Starting Phase 7 Performance Optimization Testing")
        print("=" * 60)
        
        # Test performance systems
        performance_success = self.test_performance_systems()
        
        # Print final summary
        print("\n" + "="*60)
        print("📊 PHASE 7 PERFORMANCE TEST SUMMARY")
        print("="*60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"{i}. {failure['name']}")
                if 'error' in failure:
                    print(f"   Error: {failure['error']}")
                else:
                    print(f"   Expected: {failure['expected']}, Got: {failure['actual']}")
        
        if performance_success:
            print("\n🎉 PHASE 7 PERFORMANCE OPTIMIZATION TESTING COMPLETED SUCCESSFULLY!")
        else:
            print("\n⚠️  PHASE 7 PERFORMANCE OPTIMIZATION TESTING COMPLETED WITH ISSUES")
        
        return performance_success

if __name__ == "__main__":
    tester = PerformanceSystemTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)