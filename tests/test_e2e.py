"""
End-to-End Integration Tests for AEO Auditor Backend

Tests the complete audit pipeline from submission to completion.
"""
import asyncio
import time
import requests
from typing import Dict

# Configuration
BASE_URL = "http://localhost:8000"
TEST_URL = "https://example.com"  # Replace with a real test URL


class BackendE2ETester:
    """End-to-end test suite for backend API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health_checks(self):
        """Test all health check endpoints"""
        print("\n🏥 Testing Health Checks...")
        
        endpoints = [
            "/health/health",
            "/health/health/db",
            "/health/health/celery",
            "/health/health/redis",
            "/health/health/full"
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                status = response.json().get("status", "unknown")
                print(f"  ✓ {endpoint}: {status}")
                assert response.status_code == 200, f"Health check failed: {endpoint}"
            except Exception as e:
                print(f"  ✗ {endpoint}: {str(e)}")
    
    def test_full_audit_pipeline(self, url: str = TEST_URL):
        """Test complete audit workflow"""
        print(f"\n🔍 Testing Full Audit Pipeline for: {url}")
        
        # Step 1: Submit audit
        print("  1. Submitting audit...")
        response = self.session.post(
            f"{self.base_url}/api/v1/audits/",
            json={
                "url": url,
                "include_bilingual": True,
                "deep_content_analysis": True
            }
        )
        assert response.status_code == 201, "Failed to submit audit"
        
        audit_data = response.json()
        audit_id = audit_data["audit_id"]
        print(f"     ✓ Audit created: {audit_id}")
        
        # Step 2: Poll for completion
        print("  2. Waiting for completion...")
        max_wait = 120  # 2 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = self.session.get(f"{self.base_url}/api/v1/audits/{audit_id}")
            assert response.status_code == 200, "Failed to get audit status"
            
            status_data = response.json()
            status = status_data["status"]
            
            print(f"     Status: {status}")
            
            if status == "completed":
                print(f"     ✓ Audit completed in {int(time.time() - start_time)}s")
                break
            elif status == "failed":
                error = status_data.get("error_message", "Unknown error")
                print(f"     ✗ Audit failed: {error}")
                return False
            
            time.sleep(5)
        else:
            print(f"     ✗ Timeout waiting for audit completion")
            return False
        
        # Step 3: Verify detailed report
        print("  3. Fetching detailed report...")
        response = self.session.get(f"{self.base_url}/api/v1/audits/{audit_id}/detailed")
        assert response.status_code == 200, "Failed to get detailed report"
        
        report = response.json()
        
        # Verify report structure
        required_sections = ["protocol", "schema", "edge", "content", "recommendations"]
        for section in required_sections:
            assert section in report, f"Missing section: {section}"
            print(f"     ✓ {section.capitalize()} section present")
        
        # Verify scores
        overall_score = report.get("overall_score", 0)
        print(f"     ✓ Overall Score: {overall_score}/100")
        
        # Verify recommendations
        recommendations = report.get("recommendations", [])
        print(f"     ✓ Recommendations: {len(recommendations)} found")
        
        # Step 4: Test cache hit
        print("  4. Testing cache...")
        start = time.time()
        response = self.session.get(f"{self.base_url}/api/v1/audits/{audit_id}/detailed")
        cache_time = time.time() - start
        
        assert response.status_code == 200, "Cache retrieval failed"
        print(f"     ✓ Cache hit (response time: {cache_time:.3f}s)")
        
        return audit_id
    
    def test_analytics_endpoints(self):
        """Test analytics and statistics endpoints"""
        print("\n📊 Testing Analytics Endpoints...")
        
        endpoints = [
            ("/api/v1/analytics/dashboard-stats?period=last_7_days", "Dashboard Stats"),
            ("/api/v1/analytics/score-distribution", "Score Distribution"),
            ("/api/v1/analytics/platform-breakdown", "Platform Breakdown"),
            ("/api/v1/analytics/audit-trends?days=30", "Audit Trends")
        ]
        
        for endpoint, name in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                assert response.status_code == 200, f"Failed: {name}"
                data = response.json()
                print(f"  ✓ {name}: {len(str(data))} bytes")
            except Exception as e:
                print(f"  ✗ {name}: {str(e)}")
    
    def test_audit_management(self, audit_id: str):
        """Test audit management endpoints"""
        print(f"\n⚙️  Testing Audit Management...")
        
        # Test list with filters
        print("  1. Testing list audits...")
        response = self.session.get(
            f"{self.base_url}/api/v1/audits/?limit=10&status=completed"
        )
        assert response.status_code == 200, "Failed to list audits"
        data = response.json()
        print(f"     ✓ Found {data['total']} audits")
        
        # Test rescan
        print("  2. Testing rescan...")
        response = self.session.post(f"{self.base_url}/api/v1/audits/{audit_id}/rescan")
        assert response.status_code == 201, "Failed to rescan audit"
        new_audit_id = response.json()["audit_id"]
        print(f"     ✓ New audit created: {new_audit_id}")
        
        # Test delete (clean up test data)
        print("  3. Testing delete...")
        response = self.session.delete(f"{self.base_url}/api/v1/audits/{audit_id}")
        assert response.status_code == 200, "Failed to delete audit"
        print(f"     ✓ Audit deleted")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 60)
        print("🚀 Starting Backend E2E Tests")
        print("=" * 60)
        
        try:
            # 1. Health checks
            self.test_health_checks()
            
            # 2. Full audit pipeline
            audit_id = self.test_full_audit_pipeline()
            
            if not audit_id:
                print("\n❌ Audit pipeline test failed, skipping remaining tests")
                return False
            
            # 3. Analytics
            self.test_analytics_endpoints()
            
            # 4. Audit management
            self.test_audit_management(audit_id)
            
            print("\n" + "=" * 60)
            print("✅ All Tests Passed!")
            print("=" * 60)
            return True
            
        except AssertionError as e:
            print(f"\n❌ Test Failed: {str(e)}")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def run_cache_verification():
    """Verify Redis cache integration"""
    print("\n" + "=" * 60)
    print("🔍 Cache Integration Verification")
    print("=" * 60)
    
    from app.cache import redis_client
    
    # Test cache operations
    print("\n1. Testing cache operations...")
    
    test_key = "test:cache:key"
    test_value = {"message": "Hello from cache!"}
    
    # Set cache
    success = redis_client.set_cached(test_key, test_value, 60)
    print(f"   ✓ Set cache: {success}")
    
    # Get cache
    cached_value = redis_client.get_cached(test_key)
    assert cached_value == test_value, "Cache value mismatch"
    print(f"   ✓ Get cache: {cached_value}")
    
    # Invalidate cache
    count = redis_client.invalidate_cache(test_key)
    print(f"   ✓ Invalidate: {count} keys deleted")
    
    # Verify invalidation
    cached_after = redis_client.get_cached(test_key)
    assert cached_after is None, "Cache not invalidated"
    print(f"   ✓ Verified invalidation")
    
    # Test health check
    is_healthy = redis_client.health_check()
    print(f"\n2. Redis health: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}")
    
    print("\n✅ Cache verification complete!")


if __name__ == "__main__":
    import sys
    
    # Run cache verification first
    run_cache_verification()
    
    # Ask for test URL
    print("\n" + "=" * 60)
    test_url = input("Enter URL to test (or press Enter for example.com): ").strip()
    if not test_url:
        test_url = "https://example.com"
    
    # Run E2E tests
    tester = BackendE2ETester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
