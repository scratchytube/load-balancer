# Python HTTP Load Balancer

A lightweight HTTP reverse proxy load balancer that distributes requests across multiple backend services and automatically removes unhealthy instances from rotation.

## Features
- Round-robin request routing across backends
- Active health checks (background polling)
- Automatic failover when a backend becomes unavailable
- Forwards GET and POST requests and returns backend responses
- Returns appropriate errors when backends are unavailable (502 / 503)

## Architecture

  Client
  ↓
  Load Balancer (localhost:8000)
  ↓
  Backend Servers (localhost:8001–8003)
  
  The load balancer routes traffic only to healthy servers.  
  If a backend stops responding, it is automatically removed from rotation.

## Running Locally

  ### 1) Start backend servers
    Open three terminals:
    
    ```bash
    python backends/server1.py
    python backends/server2.py
    python backends/server3.py

  ### 2) Start the load balancer

    python balancer.py

## Testing

  GET Request
  curl http://localhost:8000

  POST Request
  curl -X POST http://localhost:8000 -H "Content-Type: text/plain" -d "hello"

  
