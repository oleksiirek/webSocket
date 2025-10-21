"""Simple test script to verify WebSocket server functionality."""

import asyncio
import json
import sys
from datetime import datetime

import aiohttp
import websockets


async def test_health_endpoint():
    """Test the health check endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data}")
                    return True
                else:
                    print(f"❌ Health check failed with status: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


async def test_websocket_connection():
    """Test WebSocket connection and message exchange."""
    print("🔍 Testing WebSocket connection...")
    try:
        uri = "ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Send a ping message
            ping_message = {"type": "ping", "timestamp": datetime.now().isoformat()}
            await websocket.send(json.dumps(ping_message))
            print(f"📤 Sent: {ping_message}")
            
            # Wait for a few messages (including periodic notifications)
            message_count = 0
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"📥 Received: {data}")
                    message_count += 1
                    
                    # Exit after receiving a few messages
                    if message_count >= 3:
                        break
                        
                except json.JSONDecodeError:
                    print(f"📥 Received non-JSON message: {message}")
                    
            print("✅ WebSocket communication test completed")
            return True
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False


async def test_notification_endpoint():
    """Test the notification broadcast endpoint."""
    print("🔍 Testing notification endpoint...")
    try:
        notification_data = {
            "message": "Test notification from test script",
            "type": "test",
            "data": {"source": "test_script", "timestamp": datetime.now().isoformat()}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/notify",
                json=notification_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Notification sent successfully: {data}")
                    return True
                else:
                    print(f"❌ Notification failed with status: {response.status}")
                    text = await response.text()
                    print(f"Response: {text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Notification test failed: {e}")
        return False


async def test_metrics_endpoint():
    """Test the metrics endpoint."""
    print("🔍 Testing metrics endpoint...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/metrics") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Metrics retrieved: {data}")
                    return True
                else:
                    print(f"❌ Metrics failed with status: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Metrics test failed: {e}")
        return False


async def test_prometheus_metrics_endpoint():
    """Test the Prometheus metrics endpoint."""
    print("🔍 Testing Prometheus metrics endpoint...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/metrics/prometheus") as response:
                if response.status == 200:
                    text = await response.text()
                    # Check for expected Prometheus format
                    if "# HELP websocket_active_connections" in text and "# TYPE websocket_active_connections gauge" in text:
                        print(f"✅ Prometheus metrics retrieved successfully")
                        print(f"   Sample: {text.split('websocket_active_connections')[1].split()[0]} active connections")
                        return True
                    else:
                        print(f"❌ Prometheus metrics format invalid")
                        return False
                else:
                    print(f"❌ Prometheus metrics failed with status: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Prometheus metrics test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting WebSocket Notification Server Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("WebSocket Connection", test_websocket_connection),
        ("Notification Endpoint", test_notification_endpoint),
        ("Metrics Endpoint", test_metrics_endpoint),
        ("Prometheus Metrics", test_prometheus_metrics_endpoint),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Tests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 All tests passed! Server is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the server configuration.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        sys.exit(1)