'''
BaseHTTPRequestHandler - gives us ability to handle http requests in a Python class
HTTPServer - server object that listens on a port. we're using 8000
requests - python library used to send http requests to backend servers
'''
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

# List of backend server URLs
backend_servers = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003"
]

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
        # cycles through our backend servers in order using modulo math aka round-robin logic
        backend_url = backend_servers[current_server]
        current_server = (current_server + 1) % len(backend_servers)

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
                response = requests.post(backend_url, data = post_data, headers={"Content-Type": self.headers["Content-Type"]})

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
    # starts server; waits for incoming http requests
    httpd.serve_forever()