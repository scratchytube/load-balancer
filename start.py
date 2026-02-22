import subprocess
import sys
import os
import time
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

root = os.path.dirname(os.path.abspath(__file__))
backends_dir = os.path.join(root, "backend-servers")
lb_path = os.path.join(root, "load-balancer", "load_balancer.py")

# Each entry: {"label": str, "path": str, "port": int, "process": Popen | None}
servers = [
    {"label": "Backend 1", "path": os.path.join(backends_dir, "server1.py"), "port": 8001, "process": None},
    {"label": "Backend 2", "path": os.path.join(backends_dir, "server2.py"), "port": 8002, "process": None},
    {"label": "Backend 3", "path": os.path.join(backends_dir, "server3.py"), "port": 8003, "process": None},
    {"label": "Load Balancer", "path": lb_path, "port": 8000, "process": None},
]

def start_server(s):
    if s["process"] and s["process"].poll() is None:
        print(f"  {s['label']} is already running.")
        return
    s["process"] = subprocess.Popen(
        [sys.executable, s["path"]],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"  Started {s['label']} (pid {s['process'].pid})")

def kill_server(s):
    if not s["process"] or s["process"].poll() is not None:
        print(f"  {s['label']} is not running.")
        return
    s["process"].terminate()
    s["process"].wait()
    print(f"  Stopped {s['label']}")

def status(s):
    if s["process"] and s["process"].poll() is None:
        return f"RUNNING (pid {s['process'].pid})"
    return "STOPPED"

def print_status():
    print()
    for i, s in enumerate(servers):
        key = "lb" if i == 3 else str(i + 1)
        print(f"  [{key}] {s['label']} (port {s['port']}) — {status(s)}")
    print()

def shutdown_all():
    for s in servers:
        if s["process"] and s["process"].poll() is None:
            s["process"].terminate()
    for s in servers:
        if s["process"]:
            s["process"].wait()

def resolve(key):
    """Map a user key ('1','2','3','lb') to a server entry."""
    if key == "lb":
        return servers[3]
    if key in ("1", "2", "3"):
        return servers[int(key) - 1]
    return None

class ManagementHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silence request logs

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/status":
            payload = [
                {"label": s["label"], "port": s["port"], "running": s["process"] is not None and s["process"].poll() is None}
                for s in servers
            ]
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parts = self.path.strip("/").split("/")  # e.g. ["kill", "2"]
        if len(parts) == 2 and parts[0] in ("kill", "start") and parts[1] in ("1", "2", "3"):
            s = servers[int(parts[1]) - 1]
            if parts[0] == "kill":
                kill_server(s)
            else:
                start_server(s)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
        else:
            self.send_response(404)
            self.end_headers()


def main():
    # Start backends first, then load balancer
    for s in servers[:3]:
        start_server(s)
    time.sleep(1)
    start_server(servers[3])

    mgmt = HTTPServer(("", 8004), ManagementHandler)
    threading.Thread(target=mgmt.serve_forever, daemon=True).start()
    print("Management API running on port 8004")

    print_status()
    print("Commands: kill <n|lb>, start <n|lb>, status, quit")

    while True:
        try:
            raw = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0]

        if cmd == "quit":
            break
        elif cmd == "status":
            print_status()
        elif cmd in ("kill", "start") and len(parts) == 2:
            s = resolve(parts[1])
            if s is None:
                print("  Unknown server. Use 1, 2, 3, or lb.")
                continue
            if cmd == "kill":
                kill_server(s)
            else:
                start_server(s)
        else:
            print("  Usage: kill <n|lb>, start <n|lb>, status, quit")

    print("Shutting down all servers...")
    shutdown_all()

if __name__ == "__main__":
    main()
