"""
Example WebSocket client for the WebSocket Notification Server.

This script demonstrates how to connect to the server and handle messages.
"""

import asyncio
import json
import signal
import sys
from datetime import datetime

import websockets


class WebSocketClient:
    """Simple WebSocket client for demonstration."""

    def __init__(self, uri: str = "ws://localhost:8000/ws"):
        """Initialize the client with server URI."""
        self.uri = uri
        self.websocket = None
        self.running = False

    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            print(f"🔗 Connecting to {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            print("✅ Connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect from the server."""
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
            print("👋 Disconnected from server")
        self.running = False

    async def send_message(self, message: dict):
        """Send a message to the server."""
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.send(json.dumps(message))
                print(f"📤 Sent: {message}")
            except Exception as e:
                print(f"❌ Failed to send message: {e}")

    async def listen_for_messages(self):
        """Listen for incoming messages from the server."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(data)
                except json.JSONDecodeError:
                    print(f"📥 Received non-JSON message: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed by server")
        except Exception as e:
            print(f"❌ Error listening for messages: {e}")
        finally:
            self.running = False

    async def handle_message(self, data: dict):
        """Handle incoming messages from the server."""
        message_type = data.get("type", "unknown")
        
        if message_type == "welcome":
            print(f"🎉 Welcome message: {data.get('message')}")
            print(f"   Client ID: {data.get('client_id')}")
            print(f"   Server time: {data.get('server_time')}")
            
        elif message_type == "pong":
            print(f"🏓 Pong received: {data.get('timestamp')}")
            
        elif message_type == "test_notification":
            counter = data.get("data", {}).get("counter", "?")
            message = data.get("data", {}).get("message", "No message")
            print(f"🔔 Test notification #{counter}: {message}")
            
        elif message_type == "system":
            priority = data.get("data", {}).get("priority", "normal")
            message = data.get("data", {}).get("message", "No message")
            print(f"⚠️  System notification [{priority}]: {message}")
            
        elif message_type == "shutdown":
            print(f"🛑 Server shutdown: {data.get('message')}")
            await self.disconnect()
            
        else:
            print(f"📥 Received [{message_type}]: {data}")

    async def send_ping(self):
        """Send a ping message to the server."""
        ping_message = {
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }
        await self.send_message(ping_message)

    async def interactive_mode(self):
        """Run in interactive mode where user can send messages."""
        print("\n🎮 Interactive mode started!")
        print("Commands:")
        print("  'ping' - Send a ping to the server")
        print("  'quit' or 'exit' - Disconnect and exit")
        print("  Any other text - Send as a custom message")
        print()

        while self.running:
            try:
                # Use asyncio to handle input without blocking
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "💬 Enter command: "
                )
                
                if user_input.lower() in ['quit', 'exit']:
                    break
                elif user_input.lower() == 'ping':
                    await self.send_ping()
                elif user_input.strip():
                    custom_message = {
                        "type": "custom",
                        "message": user_input,
                        "timestamp": datetime.now().isoformat()
                    }
                    await self.send_message(custom_message)
                    
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                print(f"❌ Error in interactive mode: {e}")

        await self.disconnect()

    async def run(self, interactive: bool = False):
        """Run the client."""
        if not await self.connect():
            return

        try:
            if interactive:
                # Run interactive mode and message listener concurrently
                await asyncio.gather(
                    self.listen_for_messages(),
                    self.interactive_mode()
                )
            else:
                # Just listen for messages
                print("👂 Listening for messages... (Press Ctrl+C to exit)")
                await self.listen_for_messages()
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        finally:
            await self.disconnect()


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="WebSocket Notification Server Client")
    parser.add_argument(
        "--uri", 
        default="ws://localhost:8000/ws",
        help="WebSocket server URI (default: ws://localhost:8000/ws)"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    args = parser.parse_args()
    
    client = WebSocketClient(args.uri)
    
    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        print("\n🛑 Received interrupt signal")
        asyncio.create_task(client.disconnect())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    await client.run(interactive=args.interactive)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)