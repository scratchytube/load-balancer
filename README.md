# Load Balancer

A Python HTTP load balancer with a real-time monitoring dashboard. Distributes requests across three backend servers using round-robin routing, with automatic health checks and failover.

<!-- Replace with your demo gif once recorded -->
![Demo](demo.gif)

## Features

- **Round-robin load balancing** — requests are distributed evenly across all healthy backends
- **Health checks** — each backend is pinged every 5 seconds; unhealthy servers are automatically removed from rotation
- **Automatic failover** — if a backend goes down mid-rotation, traffic instantly routes to the remaining healthy servers
- **Live dashboard** — real-time UI showing server health, kill/start controls, and a request log

## How it works

```
Client → Load Balancer (port 8000) → Backend 1 (port 8001)
                                    → Backend 2 (port 8002)
                                    → Backend 3 (port 8003)
```

A background thread continuously health checks each backend. When a request comes in, the load balancer picks the next healthy server using a round-robin index protected by a threading lock to handle concurrent requests safely.

## Getting started

**Requirements:** Python 3, and the `requests` library (`pip install requests`)

```bash
# Clone the repo
git clone https://github.com/scratchytube/load-balancer.git
cd load-balancer

# Start all servers
python start.py
```

Then open `frontend/index.html` in your browser.

## Project structure

```
load-balancer/
├── load-balancer/
│   └── load_balancer.py   # Load balancer (port 8000)
├── backend-servers/
│   ├── server1.py         # Backend server (port 8001)
│   ├── server2.py         # Backend server (port 8002)
│   └── server3.py         # Backend server (port 8003)
├── frontend/
│   ├── index.html         # Dashboard
│   ├── style.css
│   └── app.js
└── start.py               # Process manager + management API (port 8004)
```

## What I'd improve with more time

- Move hardcoded backend URLs and ports into a config file or environment variables
- Add a dedicated `/health` endpoint on each backend instead of health checking the root path
- Implement retry logic so a failed request automatically tries the next healthy backend
- Add structured logging with timestamps and log levels
- Accept any HTTP method and forward all request headers through to backends
