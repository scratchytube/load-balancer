'''
BaseHTTPRequestHandler - gives us ability to handle http requests in a Python class
HTTPServer - server object that listens on a port. we're using 8000
requests - python library used to send http requests to backend servers
threading - lets us run background tasks in parallel
time - gives us sleep(), which we will use to pause between checks
'''
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import requests
import threading
import time
import json

# List of backend server URLs
backend_servers = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003"
]

# tracks health status of each backend server (default: healthy)
server_health = {url: True for url in backend_servers}

# Round-robin index and a lock to protect it across threads
current_server = 0
round_robin_lock = threading.Lock()

# class to handle all incoming http requests to load balancer
class LoadBalancerHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/status":
            self._handle_status()
        else:
            self.forward_request(method="GET")

    def do_POST(self):
        self.forward_request(method="POST")

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _handle_status(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(server_health).encode())

    def forward_request(self, method):
        # modifies a variable outside our class
        global current_server
        
        healthy_servers = [url for url in backend_servers if server_health.get(url, False)]
        # If no healthy servers are available, return a 503 error
        if not healthy_servers:
            self.send_response(503)
            self.send_header("Content-type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            
            error_msg = '{"error": "No healthy backend servers available"}'
            self.wfile.write(error_msg.encode())
            return
        
        
        # pick the next healthy server using round-robin logic
        # lock ensures two concurrent requests can't read/write the index at the same time
        with round_robin_lock:
            backend_url = healthy_servers[current_server % len(healthy_servers)]
            current_server = (current_server + 1) % len(healthy_servers)

        try:
            target_url = backend_url + self.path
            if method == "GET":
                response = requests.get(target_url)
            elif method == "POST":
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length)
                response = requests.post(
                    target_url,
                    data=post_data,
                    headers={"Content-Type": self.headers["Content-Type"]}
                )

            self.send_response(response.status_code)
            self.send_header("Content-type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(response.content)

        except Exception as e:
            self.send_response(502)
            self.send_header("Content-type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            # give you a good error message
            error_msg = f'{{"error": "Could not reach backend server: {str(e)}"}}'
            # converts error message to http response body so we can see json error
            self.wfile.write(error_msg.encode())
def health_check():
    # Infinite loop to keep checking the servers repeatedly
    while True:
        # Loop through each backend server URL
        for url in backend_servers:
            try:
                # Try to send a GET request to the backend server with a 2 second timeout
                response = requests.get(url, timeout = 2)
                # If the server responds with HTTP 200, mark it as healthy (True)
                server_health[url] = response.status_code == 200
                print(f"Health check: {url} is {'healthy' if server_health[url] else 'unhealthy'}")
            except Exception:
                # If there's any error (timeout, connection refused, etc.), mark it as unhealthy (False)
                server_health[url] = False
                print(f"Health check: {url} is unhealthy")
        # Wait 5 seconds before running the health checks again
        time.sleep(5)

# checks to see if file is being run directly
# If someone runs this file directly, create a web server on port 8000 that forwards requests using LoadBalancerHandler and never stop unless manually shut down
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handles each request in a separate thread."""


if __name__ == "__main__":
    server_address = ("", 8000)
    httpd = ThreadedHTTPServer(server_address, LoadBalancerHandler)
    # helpful message telling you server is live
    print("Load Balancer running on port 8000...")
    
    # Start the health check loop in a background thread
    threading.Thread(target=health_check, daemon=True).start()
    
    # starts server; waits for incoming http requests
    httpd.serve_forever()