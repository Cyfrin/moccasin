import socketserver
import os
import http.server
import threading
import webbrowser
import time
import json

# Global flag to signal server shutdown
shutdown_flag = threading.Event()
# Global variable to store the transaction result received from the client
transaction_result = None
# Global variable to track the last time a heartbeat was received
last_heartbeat_time = time.time()

# Constants for heartbeat mechanism
HEARTBEAT_INTERVAL_CLIENT_MS = 5000  # Client sends heartbeat every 5 seconds
HEARTBEAT_TIMEOUT_SERVER_S = (
    15  # Server waits 15 seconds without heartbeat before shutting down
)


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    """
    A custom HTTP request handler that extends SimpleHTTPRequestHandler.
    It adds specific endpoints for transaction details, server shutdown, and heartbeat.
    """

    def do_GET(self):
        """
        Handles GET requests.
        Serves index.html, provides transaction details, or handles heartbeat.
        """
        global last_heartbeat_time
        if self.path == "/transaction_details":
            # Build a dummy transaction.
            dummy_to_address = "0x44586c5784a07Cc85ae9f33FCf6275Ea41636A87"
            transaction_data = {
                "to": dummy_to_address,
                "value": "0x0",  # 0 ETH in wei (hex format)
                "gasLimit": "0x5208",  # 21000 gas, common for simple transfers
                "gasPrice": "0x989680",  # 1 Gwei (1,000,000,000 wei) in hex
            }
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(transaction_data).encode("utf-8"))
        elif self.path == "/heartbeat":
            # Update the last heartbeat time
            last_heartbeat_time = time.time()
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            # For any other GET requests, serve files normally (e.g., index.html, main.js)
            super().do_GET()

    def do_POST(self):
        """
        Handles POST requests.
        Specifically listens for a POST request to '/shutdown' to receive transaction result
        and initiate server shutdown.
        """
        if self.path == "/shutdown":
            # Get the content length from the request headers
            content_length = int(self.headers["Content-Length"])
            # Read the body of the POST request, which contains the transaction status/hash
            post_body = self.rfile.read(content_length).decode("utf-8")
            global transaction_result
            transaction_result = post_body  # Store the result
            print(f"Received transaction result from browser: {post_body}")

            # Send a 200 OK response back to the client
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Server received result and is shutting down...")

            # Set the shutdown flag to signal the main server loop to terminate
            shutdown_flag.set()
        else:
            # For any other POST requests, defer to the default handler (though none are expected here)
            super().do_POST()


def open_browser_tab(port):
    """
    Opens a new web browser tab to the specified local server URL.
    This function is run in a separate thread to avoid blocking the server startup.
    """
    webbrowser.open(f"http://localhost:{port}/index.html")


def heartbeat_monitor():
    """
    Monitors the last heartbeat time. If no heartbeat is received for HEARTBEAT_TIMEOUT_SERVER_S,
    it sets the SHUTDOWN_FLAG to terminate the server.
    """
    global last_heartbeat_time
    while not shutdown_flag.is_set():
        if time.time() - last_heartbeat_time > HEARTBEAT_TIMEOUT_SERVER_S:
            print(
                f"\nNo heartbeat received for {HEARTBEAT_TIMEOUT_SERVER_S} seconds. Assuming browser closed. Shutting down server..."
            )
            shutdown_flag.set()
            break
        time.sleep(1)  # Check every second


def run_server():
    """
    Starts the HTTP server, opens a web browser, and waits for a shutdown signal.
    """
    PORT = 9000  # Define the port for the web server

    # Change the current working directory to the script's directory.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Create a custom TCPServer that allows address reuse.
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    # Create the TCP server with the custom handler
    httpd = ReusableTCPServer(("", PORT), CustomHandler)

    print(f"Serving at http://localhost:{PORT}")
    print(f"To view your index.html, go to http://localhost:{PORT}/index.html")

    # Start the HTTP server in a separate thread.
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = (
        True  # Allow the main program to exit even if this thread is running
    )
    server_thread.start()

    # Start the heartbeat monitor in a separate thread
    monitor_thread = threading.Thread(target=heartbeat_monitor)
    monitor_thread.daemon = (
        True  # Allow the main program to exit even if this thread is running
    )
    monitor_thread.start()

    # Open the web browser to the index.html page in a separate thread.
    browser_thread = threading.Thread(target=open_browser_tab, args=(PORT,))
    browser_thread.start()

    print("Waiting for transaction completion or browser closure signal...")
    # Wait until the SHUTDOWN_FLAG is set by the client (after transaction completion)
    # or by the heartbeat monitor (if browser closes unexpectedly).
    shutdown_flag.wait()
    print("Shutdown signal received. Stopping server...")

    # Shut down the server
    httpd.shutdown()
    httpd.server_close()
    print("Server closed.")

    # You can now access TRANSACTION_RESULT here if needed for further Python logic
    if transaction_result:
        print(f"Final Transaction Outcome: {transaction_result}")


if __name__ == "__main__":
    run_server()
