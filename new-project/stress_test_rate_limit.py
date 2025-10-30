"""
Stress test for token bucket rate limiter - demonstrates 5 req/s limit.
This test makes 20 rapid requests to show how the token bucket handles bursts.
"""
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:3000"

def stress_test():
    """Make 20 rapid requests to demonstrate token bucket behavior."""
    print("=" * 90)
    print("STRESS TEST: Token Bucket Rate Limiter (5 req/s, burst capacity: 5)")
    print("=" * 90)
    print()
    print("Making 20 rapid-fire requests...")
    print("Expected behavior:")
    print("  • First 5 requests: IMMEDIATE SUCCESS (using initial bucket tokens)")
    print("  • Requests 6-20: GRADUAL SUCCESS as tokens refill at 5/second")
    print("  • Some 429 responses when bucket is empty")
    print()
    print("-" * 90)
    
    start_time = time.time()
    results = []
    
    for i in range(20):
        request_start = time.time()
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            elapsed = time.time() - start_time
            
            # Get rate limit headers
            remaining = response.headers.get('X-RateLimit-Remaining', 'N/A')
            limit = response.headers.get('X-RateLimit-Limit', 'N/A')
            retry_after = response.headers.get('Retry-After', 'N/A')
            
            if response.status_code == 200:
                print(f"✅ #{i+1:2d} | {elapsed:6.3f}s | 200 OK      | Tokens: {remaining}/{limit}")
                results.append(('success', elapsed))
            elif response.status_code == 429:
                print(f"❌ #{i+1:2d} | {elapsed:6.3f}s | 429 BLOCKED | Retry: {retry_after}s | Tokens: {remaining}/{limit}")
                results.append(('blocked', elapsed))
            else:
                print(f"⚠️  #{i+1:2d} | {elapsed:6.3f}s | {response.status_code} ERROR")
                results.append(('error', elapsed))
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ #{i+1:2d} | {elapsed:6.3f}s | EXCEPTION: {e}")
            results.append(('error', elapsed))
        
        # Very small delay to prevent connection issues
        time.sleep(0.05)
    
    total_time = time.time() - start_time
    
    print("-" * 90)
    print()
    print("📊 RESULTS SUMMARY")
    print("=" * 90)
    
    success_count = len([r for r in results if r[0] == 'success'])
    blocked_count = len([r for r in results if r[0] == 'blocked'])
    error_count = len([r for r in results if r[0] == 'error'])
    
    print(f"Total requests:    {len(results)}")
    print(f"✅ Successful:     {success_count}")
    print(f"❌ Rate limited:   {blocked_count}")
    print(f"⚠️  Errors:         {error_count}")
    print(f"⏱️  Total time:     {total_time:.2f}s")
    print(f"📈 Effective rate: {success_count/total_time:.2f} req/s")
    print()
    
    # Analyze token bucket behavior
    print("🪣 TOKEN BUCKET ANALYSIS")
    print("=" * 90)
    
    # Count successes in first 200ms (initial burst)
    initial_burst = len([r for r in results if r[0] == 'success' and r[1] < 0.3])
    print(f"Initial burst (first 300ms):  {initial_burst} successful (expected: ~5)")
    
    # Check if rate limiting is working
    if blocked_count > 0:
        print("✅ Rate limiting is ACTIVE (429 responses detected)")
        first_block_time = next((r[1] for r in results if r[0] == 'blocked'), None)
        if first_block_time:
            print(f"   First 429 at: {first_block_time:.3f}s")
    else:
        print("⚠️  Rate limiting NOT triggered (no 429 responses)")
    
    # Check refill behavior
    success_times = [r[1] for r in results if r[0] == 'success']
    if len(success_times) > 5:
        time_windows = []
        for i in range(5, len(success_times)):
            # Time between successful requests (after initial burst)
            time_diff = success_times[i] - success_times[i-1]
            time_windows.append(time_diff)
        
        if time_windows:
            avg_interval = sum(time_windows) / len(time_windows)
            print(f"Average interval between requests (after burst): {avg_interval:.3f}s")
            print(f"Expected refill interval: 0.200s (1 token per 0.2s = 5 tokens/s)")
    
    print()
    print("=" * 90)
    print("✅ Stress test complete!")
    print("=" * 90)


if __name__ == "__main__":
    print()
    print(f"🎯 Target: {BASE_URL}")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Check if backend is available
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            stress_test()
        else:
            print(f"❌ Backend returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {BASE_URL}")
        print("   Make sure the backend is running: docker-compose up -d")
    except Exception as e:
        print(f"❌ Error: {e}")
