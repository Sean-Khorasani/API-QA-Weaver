#!/usr/bin/env python3
"""
Test AI-powered testing tools against Mockoon mock backend services
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Mock backend configuration
MAIN_API_URL = "http://localhost:3001"
ANALYTICS_API_URL = "http://localhost:3002"
NOTIFICATION_API_URL = "http://localhost:3003"

async def test_backend_services():
    """Test all mock backend services are running"""
    print("=== Testing Mock Backend Services ===\n")
    
    services = [
        ("Main API", f"{MAIN_API_URL}/health"),
        ("Analytics", f"{ANALYTICS_API_URL}/realtime"),
        ("Notifications", f"{NOTIFICATION_API_URL}/notifications/test/status")
    ]
    
    async with aiohttp.ClientSession() as session:
        for name, url in services:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        print(f"✅ {name} is running at {url}")
                    else:
                        print(f"❌ {name} returned status {resp.status}")
            except Exception as e:
                print(f"❌ {name} failed: {str(e)}")
    
    print()

async def test_api_endpoints():
    """Test various API endpoints"""
    print("=== Testing API Endpoints ===\n")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Authentication
        print("1. Testing Authentication...")
        login_data = {"username": "testuser", "password": "password123"}
        async with session.post(f"{MAIN_API_URL}/auth/login", json=login_data) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✅ Login successful: token={data['token'][:20]}...")
            else:
                print(f"   ❌ Login failed with status {resp.status}")
        
        # Test 2: Get Products
        print("\n2. Testing Product Listing...")
        async with session.get(f"{MAIN_API_URL}/products?page=1&pageSize=5") as resp:
            data = await resp.json()
            print(f"   ✅ Retrieved {len(data['products'])} products")
            print(f"   Sample: {data['products'][0]['name']} - ${data['products'][0]['price']}")
        
        # Test 3: Create Order
        print("\n3. Testing Order Creation...")
        order_data = {
            "items": [
                {"productId": 1, "quantity": 2},
                {"productId": 3, "quantity": 1}
            ]
        }
        async with session.post(f"{MAIN_API_URL}/orders", json=order_data) as resp:
            if resp.status == 201:
                data = await resp.json()
                print(f"   ✅ Order created: {data['orderId']}")
                print(f"   Status: {data['status']}")
        
        # Test 4: Search
        print("\n4. Testing Search...")
        async with session.get(f"{MAIN_API_URL}/search?q=test") as resp:
            data = await resp.json()
            print(f"   ✅ Search returned {len(data['results'])} results")
            print(f"   Processing time: {data['processingTime']}ms")
        
        # Test 5: Analytics Event
        print("\n5. Testing Analytics Event Tracking...")
        event_data = {
            "event": "page_view",
            "properties": {
                "page": "/products",
                "user_id": "test123",
                "timestamp": datetime.now().isoformat()
            }
        }
        async with session.post(f"{ANALYTICS_API_URL}/events", json=event_data) as resp:
            if resp.status == 201:
                data = await resp.json()
                print(f"   ✅ Event tracked: {data['eventId']}")
        
        # Test 6: Get Metrics
        print("\n6. Testing Metrics Retrieval...")
        async with session.get(f"{ANALYTICS_API_URL}/metrics/page_views?period=24h") as resp:
            data = await resp.json()
            print(f"   ✅ Metric: {data['metric']}")
            print(f"   Total: {data['summary']['total']:,}")
            print(f"   Average: {data['summary']['average']:,}")
        
        # Test 7: Send Notification
        print("\n7. Testing Notification Service...")
        notification_data = {
            "recipient": "user@example.com",
            "channels": ["email", "push"],
            "message": {
                "title": "Test Notification",
                "body": "This is a test notification from our testing tools"
            }
        }
        async with session.post(f"{NOTIFICATION_API_URL}/notifications/send", json=notification_data) as resp:
            if resp.status == 202:
                data = await resp.json()
                print(f"   ✅ Notification queued: {data['notificationId']}")
                print(f"   Channels: {', '.join(data['channels'])}")

async def test_error_scenarios():
    """Test error handling and edge cases"""
    print("\n=== Testing Error Scenarios ===\n")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Invalid login
        print("1. Testing Failed Authentication...")
        bad_login = {"username": "baduser", "password": "wrongpass"}
        async with session.post(f"{MAIN_API_URL}/auth/login", json=bad_login) as resp:
            if resp.status == 401:
                data = await resp.json()
                print(f"   ✅ Correctly rejected: {data['error']}")
        
        # Test 2: Rate limiting
        print("\n2. Testing Rate Limiting...")
        for i in range(5):
            async with session.get(f"{MAIN_API_URL}/limited") as resp:
                if resp.status == 429:
                    data = await resp.json()
                    print(f"   ✅ Rate limited after {i} requests")
                    print(f"   Retry after: {data['retryAfter']}s")
                    break
                elif resp.status == 200:
                    data = await resp.json()
                    print(f"   Request {i+1}: Remaining: {data['remaining']}")
        
        # Test 3: Timeout scenario
        print("\n3. Testing Timeout Handling...")
        payment_data = {"amount": 100.50, "currency": "USD"}
        start_time = time.time()
        try:
            async with session.post(f"{MAIN_API_URL}/payments/process", 
                                  json=payment_data,
                                  timeout=aiohttp.ClientTimeout(total=3)) as resp:
                if resp.status == 504:
                    print(f"   ✅ Gateway timeout handled correctly")
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"   ✅ Client timeout after {elapsed:.1f}s")

async def test_load_patterns():
    """Simulate different load patterns"""
    print("\n=== Testing Load Patterns ===\n")
    
    async def make_request(session, endpoint):
        """Make a single request and measure response time"""
        start = time.time()
        try:
            async with session.get(f"{MAIN_API_URL}{endpoint}") as resp:
                await resp.read()
                return time.time() - start, resp.status
        except:
            return time.time() - start, 0
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Burst load
        print("1. Testing Burst Load (50 concurrent requests)...")
        tasks = [make_request(session, "/health") for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        successful = sum(1 for _, status in results if status == 200)
        avg_time = sum(time for time, _ in results) / len(results)
        
        print(f"   ✅ {successful}/50 successful")
        print(f"   Average response time: {avg_time*1000:.1f}ms")
        
        # Test 2: Sustained load
        print("\n2. Testing Sustained Load (10 req/s for 5 seconds)...")
        start_time = time.time()
        request_times = []
        
        while time.time() - start_time < 5:
            req_start = time.time()
            resp_time, status = await make_request(session, "/products")
            request_times.append(resp_time)
            
            # Wait to maintain 10 req/s rate
            elapsed = time.time() - req_start
            if elapsed < 0.1:
                await asyncio.sleep(0.1 - elapsed)
        
        print(f"   ✅ Completed {len(request_times)} requests")
        print(f"   Average response time: {sum(request_times)/len(request_times)*1000:.1f}ms")
        print(f"   Max response time: {max(request_times)*1000:.1f}ms")

def generate_report(start_time):
    """Generate a summary report"""
    elapsed = time.time() - start_time
    
    report = {
        "test_date": datetime.now().isoformat(),
        "duration_seconds": round(elapsed, 2),
        "services_tested": [
            "Main API (port 3001)",
            "Analytics Service (port 3002)",
            "Notification Service (port 3003)"
        ],
        "endpoints_tested": [
            "/auth/login",
            "/products",
            "/orders",
            "/search",
            "/events",
            "/metrics",
            "/notifications/send"
        ],
        "scenarios_tested": [
            "Authentication flow",
            "Product listing",
            "Order creation",
            "Search functionality",
            "Analytics tracking",
            "Notification delivery",
            "Error handling",
            "Rate limiting",
            "Timeout scenarios",
            "Load patterns"
        ]
    }
    
    # Save report
    report_file = f"mockoon_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_file}")
    
    return report

async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing AI-Powered QA Tools with Mock Backend Services")
    print("=" * 60)
    print()
    
    start_time = time.time()
    
    # Run all test suites
    await test_backend_services()
    await test_api_endpoints()
    await test_error_scenarios()
    await test_load_patterns()
    
    # Generate report
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    report = generate_report(start_time)
    
    print(f"\n✅ All tests completed in {report['duration_seconds']} seconds")
    print(f"📊 {len(report['endpoints_tested'])} endpoints tested")
    print(f"🔧 {len(report['scenarios_tested'])} test scenarios executed")
    
    print("\n📌 Next Steps:")
    print("1. Run CTGE to generate test cases from natural language")
    print("2. Use SETS to create self-evolving tests for these APIs")
    print("3. Run multiplayer game testing tools against mock services")
    
    return report

if __name__ == "__main__":
    asyncio.run(main())