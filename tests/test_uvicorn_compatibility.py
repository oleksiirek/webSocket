"""
Test script to verify uvicorn compatibility.

This script verifies that the application can be run with uvicorn as required.
"""

from loguru import logger


def test_uvicorn_import():
    """Test that the app can be imported for uvicorn."""
    # Test direct import (uvicorn main:app)
    from main import app as main_app
    logger.success("Successfully imported app from main module")

    # Test websocket_server.app import (uvicorn websocket_server.app:app)
    from websocket_server.app import app as ws_app
    logger.success("Successfully imported app from websocket_server.app module")

    # Verify they are the same app
    assert main_app is ws_app, "Apps should be the same instance"
    logger.success("Both imports reference the same FastAPI app instance")

    # Verify it's a FastAPI app
    from fastapi import FastAPI
    assert isinstance(ws_app, FastAPI), "App should be a FastAPI instance"
    logger.success("App is a valid FastAPI instance")

    # Check that WebSocket route exists
    routes = [route.path for route in ws_app.routes]
    assert "/ws" in routes, "WebSocket endpoint /ws should exist"
    logger.success("WebSocket endpoint /ws is registered")

    # Check that HTTP endpoints exist
    expected_endpoints = ["/health", "/notify", "/metrics", "/status"]
    for endpoint in expected_endpoints:
        assert endpoint in routes, f"Endpoint {endpoint} should exist"
    logger.success(f"All required HTTP endpoints exist: {expected_endpoints}")

    logger.success("🎉 All uvicorn compatibility tests passed!")
    logger.info("You can run the server with any of these commands:")
    logger.info("  uvicorn main:app")
    logger.info("  uvicorn websocket_server.app:app")
    logger.info("  python main.py")


def main():
    """Main function for standalone execution."""
    try:
        test_uvicorn_import()
        return True
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
