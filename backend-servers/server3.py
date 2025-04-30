from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)  # HTTP 200 OK
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response = {
            "server": "Backend Server 3",
            "message": "we in server 3"
        }
        self.wfile.write(json.dumps(response).encode())

def run(server_class=HTTPServer, handler_class=SimpleHandler):
    server_address = ("", 8003)  # Listen on port 8003
    httpd = server_class(server_address, handler_class)
    print("✅ Backend Server 3 running at http://localhost:8003")
    httpd.serve_forever()

if __name__ == "__main__":
    run()