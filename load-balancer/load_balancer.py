'''
BaseHTTPRequestHandler - gives us ability to handle http requests in a Python class
HTTPServer - server object that listens on a port. we're using 8000
requests - python library used to send http requests to backend servers
threading - lets us run background tasks in parallel
time - gives us sleep(), which we will use to pause between checks
'''
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import threading
import time

# List of backend server URLs
backend_servers = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003"
]

# tracks health status of each backend server (default: healthy)
server_health = {url: True for url in backend_servers}

# Round-robin index we're starting at 0
current_server = 0

# class to handle all incoming http requests to load balancer
class LoadBalancerHandler(BaseHTTPRequestHandler):
    # runs every time we receive a get request
    def do_GET(self):
        self.forward_request(method = "GET")
    # runs every time we get a post request
    def do_POST(self):
        self.forward_request(method = "POST")

    def forward_request(self, method):
        # modifies a variable outside our class
        global current_server
        
        healthy_servers = [url for url in backend_servers if server_health.get(url, False)]
        # If no healthy servers are available, return a 503 error
        if not healthy_servers:
            self.send_response(503)  # Service Unavailable
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            error_msg = '{"error": "No healthy backend servers available"}'
            self.wfile.write(error_msg.encode())
            return
        
        
        # pick the next healthy server using round-robin logic
        backend_url = healthy_servers[current_server % len(healthy_servers)]
        current_server = (current_server + 1) % len(healthy_servers)

        try:
            if method == "GET":
                # sends a get request to selected backend
                response = requests.get(backend_url)
            elif method == "POST":
                # figures out how many bytes of data are in the request body
                content_length = int(self.headers.get("Content-Length", 0))
                #actually reads the body data
                post_data = self.rfile.read(content_length)
                # forwards the data to the backend with the content type as json
                response = requests.post(
                    backend_url, 
                    data = post_data, 
                    headers={"Content-Type": self.headers["Content-Type"]}
                )

            # sends back a http code (200, 500)
            self.send_response(response.status_code)
            # tells browser this is json instead of html
            self.send_header("Content-type", "application/json")
            # tells browser this is the end of the http response headers
            self.end_headers()
            # writes the json from the backend to the browser
            self.wfile.write(response.content)

        # catches and errors
        except Exception as e:
            # this status code means our load balancer cant reach our backend
            self.send_response(502)
            # tells browser this is json instead of html
            self.send_header("Content-type", "application/json")
            #response headers are done
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
                print(f"Health check: {url} is {'healthy' if healthy else 'unhealthy'}")
            except Exception:
                # If there's any error (timeout, connection refused, etc.), mark it as unhealthy (False)
                server_health[url] = False
                print(f"Health check: {url} is {'healthy' if healthy else 'unhealthy'}")
        # Wait 5 seconds before running the health checks again
        time.sleep(5)

# checks to see if file is being run directly
# If someone runs this file directly, create a web server on port 8000 that forwards requests using LoadBalancerHandler and never stop unless manually shut down
if __name__ == "__main__":
    # empty string means listen on all avail interfaces; ex. localhost, LAN IP
    # port number for incoming requests
    server_address = ("", 8000)
    # creates new http server instance
    # server address tells the server what port ot listen on
    # loadbalancer handler custom handler class that defines how to process each incoming request
    httpd = HTTPServer(server_address, LoadBalancerHandler)
    # helpful message telling you server is live
    print("Load Balancer running on port 8000...")
    
    # Start the health check loop in a background thread
    threading.Thread(target=health_check, daemon=True).start()
    
    # starts server; waits for incoming http requests
    httpd.serve_forever()