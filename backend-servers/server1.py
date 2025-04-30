from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)  # HTTP 200 OK
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response = {
            "server": "Backend Server 1"
        }
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
         # Get the length of the incoming POST request body (in bytes)
        # If the Content-Length header isn't present, default to 0
        content_length = int(self.headers.get("Content-Length", 0))
        # Read the actual body of the POST request using the content length
        # This gives you the raw byte data sent by the client
        post_data = self.rfile.read(content_length).decode()

        # Create a dictionary (to be converted to JSON) containing:
        # - which server handled the request
        # - a message saying a POST was received
        # - the raw data sent in the request body
        message = {
            "server": "Backend Server 1",
            "message": "POST request received",
            "data": post_data
        }
        
        # Respond to the client with HTTP status code 200 (OK)
        self.send_response(200)

        # Set the response content type to application/json
        # This tells the client the body will be JSON data
        self.send_header("Content-type", "application/json")

        # Finalize and send the response headers
        self.end_headers()

        # Convert the message dictionary to JSON, encode it into bytes,
        # and write it to the HTTP response body
        self.wfile.write(json.dumps(message).encode())

def run(server_class=HTTPServer, handler_class=SimpleHandler):
    server_address = ("", 8001)  # Listen on port 8001
    httpd = server_class(server_address, handler_class)
    print("✅ Backend Server 1 running at http://localhost:8001")
    httpd.serve_forever()

if __name__ == "__main__":
    run()