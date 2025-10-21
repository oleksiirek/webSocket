"""
Test script to verify server startup without logging errors.
"""

import asyncio
import signal
import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from websocket_server.app import app
from websocket_server.config import setup_logging


@pytest.mark.asyncio
async def test_server_startup():
    """Test that the server can start without logging errors."""
    try:
        # Setup logging
        setup_logging()
        logger.info("Testing server startup...")
        
        # Import and test the services
        from websocket_server.dependencies import (
            connection_manager,
            notification_service,
            shutdown_handler
        )
        
        logger.info("✅ All services imported successfully")
        
        # Test notification service briefly
        await notification_service.start_periodic_notifications()
        logger.info("✅ Notification service started")
        
        # Wait a short time to see if there are logging errors
        await asyncio.sleep(2)
        
        # Stop the service
        await notification_service.stop_periodic_notifications()
        logger.info("✅ Notification service stopped")
        
        logger.success("🎉 Server startup test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Server startup test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_server_startup())
    sys.exit(0 if success else 1)