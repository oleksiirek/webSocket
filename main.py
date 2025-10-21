"""
WebSocket Notification Server - Main Entry Point

A production-ready WebSocket notification server built with FastAPI that provides
real-time communication capabilities with graceful shutdown mechanisms.
"""

import sys
from pathlib import Path

import uvicorn
from loguru import logger

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from websocket_server.app import app
from websocket_server.config import settings, setup_logging


def main() -> None:
    """
    Main application entry point.

    This function initializes the WebSocket notification server with proper
    configuration and starts the uvicorn server.
    """
    try:
        # Setup logging first
        setup_logging()

        logger.info(
            "Initializing WebSocket Notification Server",
            extra={
                "version": "0.1.0",
                "python_version": sys.version,
                "settings": {
                    "host": settings.host,
                    "port": settings.port,
                    "workers": settings.workers,
                    "debug": settings.debug,
                    "log_level": settings.log_level
                }
            }
        )

        # Get uvicorn configuration
        uvicorn_config = settings.get_uvicorn_config()

        # Add the FastAPI app to the config
        uvicorn_config["app"] = app

        # Additional uvicorn settings for production
        if not settings.debug:
            uvicorn_config.update({
                "access_log": False,  # We handle our own access logging
                "server_header": False,  # Don't expose server info
                "date_header": False,  # Don't add date header
            })

        logger.info(
            "Starting uvicorn server",
            extra={"uvicorn_config": {k: v for k, v in uvicorn_config.items() if k != "app"}}
        )

        # Start the server
        uvicorn.run(**uvicorn_config)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


def run_development_server() -> None:
    """
    Run the development server with debug settings.

    This is a convenience function for development that overrides some
    production settings for a better development experience.
    Note: Auto-reload is disabled to ensure proper graceful shutdown.
    """
    # Override settings for development
    dev_config = {
        "app": app,  # Use app instance for better shutdown handling
        "host": settings.host,
        "port": settings.port,
        "reload": False,  # Disabled for proper shutdown handling
        "log_level": "debug",
        "access_log": True,
        "workers": 1,  # Always use 1 worker in development
    }

    logger.info("Starting development server (reload disabled for proper shutdown)")
    uvicorn.run(**dev_config)


def run_production_server() -> None:
    """
    Run the production server with optimized settings.

    This function starts the server with production-optimized settings
    including multiple workers if configured.
    """
    # Production configuration
    prod_config = settings.get_uvicorn_config()
    prod_config.update({
        "app": app,
        "access_log": False,
        "server_header": False,
        "date_header": False,
    })

    logger.info(
        f"Starting production server with {settings.workers} workers",
        extra={"workers": settings.workers}
    )
    uvicorn.run(**prod_config)


def check_dependencies() -> bool:
    """
    Check if all required dependencies are available.

    Returns:
        True if all dependencies are available, False otherwise
    """
    required_modules = [
        "fastapi",
        "uvicorn",
        "websockets",
        "pydantic",
        "loguru",
        "dotenv"  # python-dotenv package imports as 'dotenv'
    ]

    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print(f"Error: Missing required dependencies: {', '.join(missing_modules)}")
        print("Please install them using: pip install -r requirements.txt")
        return False

    return True


def print_server_info() -> None:
    """Print server information and available endpoints."""
    print("\n" + "="*60)
    print("WebSocket Notification Server")
    print("="*60)
    print("Version: 0.1.0")
    print(f"Host: {settings.host}")
    print(f"Port: {settings.port}")
    print(f"Workers: {settings.workers}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Log Level: {settings.log_level}")
    print("\nAvailable Endpoints:")
    print(f"  WebSocket: ws://{settings.host}:{settings.port}/ws")
    print(f"  Health Check: http://{settings.host}:{settings.port}/health")
    print(f"  Notifications: http://{settings.host}:{settings.port}/notify")
    print(f"  Metrics: http://{settings.host}:{settings.port}/metrics")
    print(f"  Status: http://{settings.host}:{settings.port}/status")

    if settings.debug:
        print(f"  API Docs: http://{settings.host}:{settings.port}/docs")
        print(f"  ReDoc: http://{settings.host}:{settings.port}/redoc")

    print("="*60 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="WebSocket Notification Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start with default settings
  python main.py --dev              # Start development server
  python main.py --prod             # Start production server
  python main.py --host 0.0.0.0     # Bind to all interfaces
  python main.py --port 8080        # Use port 8080
  python main.py --workers 4        # Use 4 worker processes
        """
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in development mode with auto-reload"
    )

    parser.add_argument(
        "--prod",
        action="store_true",
        help="Run in production mode"
    )

    parser.add_argument(
        "--host",
        type=str,
        help=f"Host to bind to (default: {settings.host})"
    )

    parser.add_argument(
        "--port",
        type=int,
        help=f"Port to bind to (default: {settings.port})"
    )

    parser.add_argument(
        "--workers",
        type=int,
        help=f"Number of worker processes (default: {settings.workers})"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help=f"Log level (default: {settings.log_level})"
    )

    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check if all dependencies are installed"
    )

    parser.add_argument(
        "--info",
        action="store_true",
        help="Print server information and exit"
    )

    args = parser.parse_args()

    # Handle special commands
    if args.check_deps:
        if check_dependencies():
            print("All dependencies are available.")
            sys.exit(0)
        else:
            sys.exit(1)

    if args.info:
        print_server_info()
        sys.exit(0)

    # Override settings from command line arguments
    if args.host:
        settings.host = args.host
    if args.port:
        settings.port = args.port
    if args.workers:
        settings.workers = args.workers
    if args.log_level:
        settings.log_level = args.log_level

    # Check dependencies before starting
    if not check_dependencies():
        sys.exit(1)

    # Print server info
    print_server_info()

    # Start the appropriate server
    if args.dev:
        run_development_server()
    elif args.prod:
        run_production_server()
    else:
        main()
