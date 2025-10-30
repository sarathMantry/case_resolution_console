"""Test script to verify token bucket rate limiting (5 req/s per client)."""
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:3000"

def test_rate_limit():
    """Test rate limiting by making rapid requests."""
    print("=" * 80)
    print("Testing Token Bucket Rate Limiter: 5 requests/second per client")
    print("=" * 80)
    print()
    
    # Get a valid alert ID first
    print("📍 Fetching a valid alert ID...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Backend is healthy")
            # Use a simple endpoint that doesn't need a specific alert
            test_endpoint = f"{BASE_URL}/health"
        else:
            print("⚠️  Backend returned non-200 status")
            return
    except Exception as e:
        print(f"❌ Failed to connect to backend: {e}")
        return
    
    print()
    
    # Test 1: Rapid burst of 10 requests
    print("Test 1: Sending 10 rapid requests (should allow 5, reject 5)")
    print("-" * 80)
    
    results = []
    start_time = time.time()
    
    for i in range(10):
        try:
            response = requests.get(test_endpoint, timeout=2)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                remaining = response.headers.get('X-RateLimit-Remaining', 'N/A')
                print(f"✅ Request {i+1:2d}: SUCCESS (200) - Remaining: {remaining} - Time: {elapsed:.3f}s")
                results.append('success')
            elif response.status_code == 429:
                retry_after = response.headers.get('Retry-After', 'N/A')
                print(f"❌ Request {i+1:2d}: BLOCKED (429) - Retry-After: {retry_after}s - Time: {elapsed:.3f}s")
                results.append('blocked')
            else:
                print(f"⚠️  Request {i+1:2d}: Status {response.status_code} - Time: {elapsed:.3f}s")
                results.append('error')
                
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            print(f"❌ Request {i+1:2d}: ERROR - {e} - Time: {elapsed:.3f}s")
            results.append('error')
        
        # Small delay to prevent connection issues
        time.sleep(0.05)
    
    total_time = time.time() - start_time
    success_count = results.count('success')
    blocked_count = results.count('blocked')
    
    print()
    print(f"Summary: {success_count} succeeded, {blocked_count} blocked in {total_time:.2f}s")
    print()
    
    # Test 2: Verify token bucket refills over time
    print("Test 2: Waiting 1 second for token bucket to refill...")
    print("-" * 80)
    time.sleep(1)
    
    print("Sending 5 more requests (should succeed after refill)")
    results2 = []
    start_time2 = time.time()
    
    for i in range(5):
        try:
            response = requests.get(test_endpoint, timeout=2)
            elapsed = time.time() - start_time2
            
            if response.status_code == 200:
                remaining = response.headers.get('X-RateLimit-Remaining', 'N/A')
                print(f"✅ Request {i+1}: SUCCESS (200) - Remaining: {remaining} - Time: {elapsed:.3f}s")
                results2.append('success')
            elif response.status_code == 429:
                retry_after = response.headers.get('Retry-After', 'N/A')
                print(f"❌ Request {i+1}: BLOCKED (429) - Retry-After: {retry_after}s - Time: {elapsed:.3f}s")
                results2.append('blocked')
            else:
                print(f"⚠️  Request {i+1}: Status {response.status_code}")
                results2.append('error')
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request {i+1}: ERROR - {e}")
            results2.append('error')
        
        time.sleep(0.05)
    
    success_count2 = results2.count('success')
    blocked_count2 = results2.count('blocked')
    
    print()
    print(f"Summary: {success_count2} succeeded, {blocked_count2} blocked")
    print()
    
    # Test 3: Check Retry-After header
    print("Test 3: Verifying Retry-After header in 429 response")
    print("-" * 80)
    
    # Make 6 rapid requests to trigger 429
    for i in range(6):
        try:
            response = requests.get(test_endpoint, timeout=2)
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                limit = response.headers.get('X-RateLimit-Limit')
                remaining = response.headers.get('X-RateLimit-Remaining')
                
                print(f"✅ Received 429 response with headers:")
                print(f"   - Retry-After: {retry_after}s")
                print(f"   - X-RateLimit-Limit: {limit}")
                print(f"   - X-RateLimit-Remaining: {remaining}")
                print()
                
                if response.headers.get('Content-Type') == 'application/json':
                    data = response.json()
                    print(f"   Response body: {data}")
                
                break
        except Exception as e:
            pass
        time.sleep(0.05)
    
    print()
    print("=" * 80)
    print("Rate Limiting Test Complete!")
    print("=" * 80)
    print()
    print("Expected behavior:")
    print("  • First 5 requests: ALLOWED (200)")
    print("  • Subsequent requests: BLOCKED (429) with Retry-After header")
    print("  • After waiting: Tokens refill, requests allowed again")
    print()


if __name__ == "__main__":
    try:
        print(f"\nTesting against: {BASE_URL}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        test_rate_limit()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
