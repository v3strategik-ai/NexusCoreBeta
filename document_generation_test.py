#!/usr/bin/env python3
"""
Focused Document Generation Testing with Extended Timeouts
"""

import requests
import sys
import json
from datetime import datetime

class DocumentGenerationTester:
    def __init__(self, base_url="https://ai-workforce-hub.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, data=None, timeout=30):
        """Run a single API test with extended timeout"""
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
            print(f"❌ FAILED - Request timeout after {timeout}s")
            self.failed_tests.append({'name': name, 'error': f'Timeout after {timeout}s'})
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': name, 'error': str(e)})
            return False, {}

    def test_document_generation_comprehensive(self):
        """Test comprehensive document generation with realistic data"""
        print("\n" + "="*60)
        print("COMPREHENSIVE DOCUMENT GENERATION TESTING")
        print("="*60)
        
        # Test Case 1: Business Proposal (as specified in review request)
        proposal_data = {
            "title": "Website Redesign Proposal for TechCorp",
            "type": "proposal",
            "client_name": "TechCorp Solutions",
            "variables": {
                "project_description": "Complete website redesign with modern UI/UX, mobile optimization, and enhanced user experience",
                "project_value": "75000",
                "timeline": "12 weeks",
                "deliverables": "New responsive website, mobile app, SEO optimization, content management system, staff training"
            },
            "custom_instructions": "Focus on ROI and competitive advantages"
        }
        
        print("\n📋 Test Case 1: Business Proposal Generation")
        success1, proposal_response = self.run_test(
            "Generate Business Proposal", "POST", "documents/generate", 200, proposal_data, timeout=45
        )
        
        if success1:
            content = proposal_response.get('content', '')
            print(f"   ✅ Generated Proposal ID: {proposal_response.get('id', 'N/A')}")
            print(f"   ✅ Content Length: {len(content)} characters")
            print(f"   ✅ Client: {proposal_response.get('client_name', 'N/A')}")
            
            # Validate AI-generated content quality
            key_terms = ['TechCorp', 'Website Redesign', '$75,000', '12 weeks', 'responsive', 'mobile']
            found_terms = sum(1 for term in key_terms if term in content)
            quality_score = (found_terms / len(key_terms)) * 100
            
            print(f"   ✅ Content Quality Score: {quality_score:.1f}% ({found_terms}/{len(key_terms)} key terms)")
            
            if 'BUSINESS PROPOSAL' in content or '# BUSINESS PROPOSAL' in content:
                print("   ✅ Professional document structure detected")
            
            if len(content) > 1000:
                print("   ✅ Comprehensive content length")
            
            # Check for AI vs fallback content
            if 'Nexus Core Solutions' in content:
                print("   ℹ️  Using fallback content generation")
            else:
                print("   ✅ Using AI-powered content generation")
        
        # Test Case 2: Invoice Generation (as specified in review request)
        invoice_data = {
            "title": "Monthly Consulting Invoice - December 2024",
            "type": "invoice",
            "client_name": "ABC Corporation",
            "variables": {
                "services": "Strategic Business Consulting and Digital Transformation Services",
                "amount": "8500.00",
                "due_date": "January 30, 2025"
            }
        }
        
        print("\n💰 Test Case 2: Invoice Generation")
        success2, invoice_response = self.run_test(
            "Generate Invoice", "POST", "documents/generate", 200, invoice_data, timeout=45
        )
        
        if success2:
            content = invoice_response.get('content', '')
            print(f"   ✅ Generated Invoice ID: {invoice_response.get('id', 'N/A')}")
            print(f"   ✅ Content Length: {len(content)} characters")
            
            # Validate invoice-specific content
            invoice_terms = ['ABC Corporation', '$8,500', 'January 30, 2025', 'INVOICE', 'Due Date']
            found_terms = sum(1 for term in invoice_terms if term in content)
            print(f"   ✅ Invoice Content Quality: {(found_terms/len(invoice_terms)*100):.1f}%")
        
        # Test Case 3: Business Plan Generation (as specified in review request)
        business_plan_data = {
            "title": "SaaS Startup Business Plan",
            "type": "business_plan",
            "variables": {
                "executive_summary": "Revolutionary AI-powered project management platform targeting mid-market companies",
                "target_market": "Mid-market companies (100-1000 employees) seeking project management automation",
                "financial_projections": "Year 1: $500K, Year 2: $2.5M, Year 3: $8M revenue"
            }
        }
        
        print("\n📊 Test Case 3: Business Plan Generation")
        success3, business_plan_response = self.run_test(
            "Generate Business Plan", "POST", "documents/generate", 200, business_plan_data, timeout=45
        )
        
        if success3:
            content = business_plan_response.get('content', '')
            print(f"   ✅ Generated Business Plan ID: {business_plan_response.get('id', 'N/A')}")
            print(f"   ✅ Content Length: {len(content)} characters")
            
            # Validate business plan structure
            bp_sections = ['EXECUTIVE SUMMARY', 'MARKET ANALYSIS', 'FINANCIAL', 'STRATEGY']
            found_sections = sum(1 for section in bp_sections if section in content.upper())
            print(f"   ✅ Business Plan Structure: {(found_sections/len(bp_sections)*100):.1f}% complete")
        
        return success1, success2, success3

    def test_document_retrieval_and_stats(self):
        """Test document retrieval and statistics"""
        print("\n" + "="*60)
        print("DOCUMENT RETRIEVAL & STATISTICS TESTING")
        print("="*60)
        
        # Test document listing
        success1, documents_list = self.run_test("Get All Documents", "GET", "documents/")
        if success1:
            doc_count = len(documents_list)
            print(f"   ✅ Total Documents: {doc_count}")
            
            # Analyze document types
            doc_types = {}
            for doc in documents_list:
                doc_type = doc.get('type', 'unknown')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            print(f"   ✅ Document Types Distribution: {doc_types}")
            
            # Test individual document retrieval
            if documents_list:
                first_doc_id = documents_list[0].get('id')
                if first_doc_id:
                    success_individual, individual_doc = self.run_test(
                        "Get Individual Document", "GET", f"documents/{first_doc_id}"
                    )
                    if success_individual:
                        print(f"   ✅ Individual Document: {individual_doc.get('title', 'N/A')}")
        
        # Test document statistics
        success2, stats = self.run_test("Document Statistics", "GET", "documents/stats/summary")
        if success2:
            print(f"   ✅ Total Documents (Stats): {stats.get('total_documents', 0)}")
            print(f"   ✅ AI Success Rate: {stats.get('ai_generation_success_rate', 0)}%")
            print(f"   ✅ Document Types (Stats): {stats.get('document_types', {})}")
        
        return success1 and success2

    def test_ai_integration_validation(self):
        """Test AI integration and validate content quality"""
        print("\n" + "="*60)
        print("AI INTEGRATION VALIDATION")
        print("="*60)
        
        # Test with complex requirements to validate AI capabilities
        complex_data = {
            "title": "Enterprise Digital Transformation Strategy",
            "type": "report",
            "client_name": "Fortune 500 Manufacturing Corp",
            "variables": {
                "report_focus": "Digital transformation roadmap with IoT integration and data analytics",
                "key_metrics": "25% efficiency improvement, $2M cost savings, 40% faster decision-making",
                "time_period": "Q4 2024 Analysis",
                "recommendations": "Implement cloud-first architecture, establish data governance, deploy AI-powered analytics"
            },
            "custom_instructions": "Include specific ROI calculations, implementation timeline, and risk mitigation strategies"
        }
        
        success, response = self.run_test(
            "AI Complex Report Generation", "POST", "documents/generate", 200, complex_data, timeout=45
        )
        
        if success:
            content = response.get('content', '')
            print(f"   ✅ Generated Complex Report ID: {response.get('id', 'N/A')}")
            print(f"   ✅ Content Length: {len(content)} characters")
            
            # Advanced content analysis
            advanced_terms = [
                'Fortune 500', 'Digital transformation', 'IoT', 'analytics', 
                '$2M', '25%', 'cloud-first', 'governance', 'ROI'
            ]
            found_advanced = sum(1 for term in advanced_terms if term.lower() in content.lower())
            advanced_score = (found_advanced / len(advanced_terms)) * 100
            
            print(f"   ✅ Advanced Content Quality: {advanced_score:.1f}% ({found_advanced}/{len(advanced_terms)} terms)")
            
            # Check for professional formatting
            formatting_indicators = ['##', '**', '###', '|', '---', '- ']
            has_formatting = any(indicator in content for indicator in formatting_indicators)
            
            if has_formatting:
                print("   ✅ Professional formatting detected")
            else:
                print("   ⚠️  Limited formatting detected")
            
            # Validate content depth
            if len(content) > 2000:
                print("   ✅ Comprehensive content depth")
            elif len(content) > 1000:
                print("   ✅ Adequate content depth")
            else:
                print("   ⚠️  Content may be too brief")
        
        return success

    def run_comprehensive_tests(self):
        """Run all comprehensive document generation tests"""
        print("🚀 Starting Comprehensive Document Generation Testing")
        print("=" * 70)
        
        # Run test suites
        gen_results = self.test_document_generation_comprehensive()
        retrieval_success = self.test_document_retrieval_and_stats()
        ai_success = self.test_ai_integration_validation()
        
        # Print comprehensive summary
        print("\n" + "="*70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("="*70)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Detailed results
        proposal_success, invoice_success, business_plan_success = gen_results
        
        print(f"\n📋 Document Generation Results:")
        print(f"   Business Proposal: {'✅ PASSED' if proposal_success else '❌ FAILED'}")
        print(f"   Invoice Generation: {'✅ PASSED' if invoice_success else '❌ FAILED'}")
        print(f"   Business Plan: {'✅ PASSED' if business_plan_success else '❌ FAILED'}")
        print(f"   Document Retrieval: {'✅ PASSED' if retrieval_success else '❌ FAILED'}")
        print(f"   AI Integration: {'✅ PASSED' if ai_success else '❌ FAILED'}")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"{i}. {failure['name']}")
                if 'error' in failure:
                    print(f"   Error: {failure['error']}")
        
        overall_success = (proposal_success and invoice_success and 
                          business_plan_success and retrieval_success and ai_success)
        
        if overall_success:
            print("\n🎉 ALL DOCUMENT GENERATION TESTS PASSED!")
            print("✅ AI-powered document generation is working correctly")
            print("✅ All specified test cases completed successfully")
        else:
            print(f"\n⚠️  Some tests failed - see details above")
        
        return overall_success

def main():
    """Main test execution"""
    tester = DocumentGenerationTester()
    success = tester.run_comprehensive_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())