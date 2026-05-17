# Distributed CDN System

A fully containerized distributed Content Delivery Network (CDN) simulation built using microservices architecture.  
The system demonstrates intelligent traffic routing, distributed edge caching, failover handling, cache invalidation, request tracing, and real-time monitoring through an interactive frontend dashboard.

---

# Architecture Overview

The system consists of multiple independent services communicating over a Docker network.

## Core Components

### Traffic Manager
Acts as the central routing layer.

Responsibilities:
- Receives incoming client requests
- Selects optimal edge node
- Performs load balancing
- Detects unhealthy nodes
- Handles failover routing

---

### Edge Nodes (A, B, C)
Distributed cache servers that deliver content to users.

Responsibilities:
- Cache frequently requested content
- Serve cached responses
- Fetch uncached data from Origin Server
- Support LRU + TTL caching policies
- Maintain request trace metadata

---

### Origin Server
Primary source of truth for all content.

Responsibilities:
- Stores original content
- Responds to cache misses
- Simulates backend content server

---

### Service Registry
Dynamic service discovery system.

Responsibilities:
- Registers active edge nodes
- Tracks node health
- Provides node metadata to Traffic Manager

---

### Purge Service
Handles cache invalidation across distributed nodes.

Responsibilities:
- Broadcast cache purge requests
- Remove stale cached content
- Maintain cache consistency

---

### Monitoring Service
Collects runtime metrics from all services.

Responsibilities:
- Monitor request flow
- Track node health
- Store traffic statistics
- Provide observability APIs

---

### Frontend Dashboard
Interactive frontend visualization layer.

Responsibilities:
- Visualize CDN architecture
- Display live service metrics
- Show request routing
- Monitor cache activity
- Observe failover behavior

---

# System Features

## Distributed Edge Caching
- Multi-node distributed caching
- Reduced latency through edge delivery
- Independent cache storage per node

## Intelligent Routing
- Dynamic edge node selection
- Health-aware routing
- Traffic balancing

## Failover Handling
- Automatic unhealthy node detection
- Traffic rerouting to active nodes
- High availability simulation

## Cache Invalidation
- Distributed cache purge mechanism
- Consistent cache updates across nodes

## Request Tracing
- End-to-end request tracking
- Request path visibility across services

## Real-Time Monitoring
- Live service health monitoring
- Metrics visualization dashboard
- Request analytics

## Containerized Infrastructure
- Fully Dockerized architecture
- Multi-service orchestration using Docker Compose

---

# Tech Stack

## Backend
- Python
- FastAPI
- REST APIs

## Frontend
- React / Next.js

## Infrastructure
- Docker
- Docker Compose

## Monitoring & Communication
- HTTP APIs
- Internal service networking

---

# Project Structure

```text
distributed-cdn-system/
│
├── services/
│   ├── traffic-manager/
│   ├── edge-node-a/
│   ├── edge-node-b/
│   ├── edge-node-c/
│   ├── origin-server/
│   ├── service-registry/
│   ├── purge-service/
│   └── monitoring/
│
├── frontend/
├── docs/
├── docker-compose.yml
└── README.md
```

---

# How the System Works

1. Client sends request to Traffic Manager
2. Traffic Manager selects optimal edge node
3. Edge node checks local cache
4. If cache hit:
   - Response returned immediately
5. If cache miss:
   - Edge node requests data from Origin Server
   - Response cached locally
   - Content returned to client
6. Monitoring service tracks request lifecycle
7. Purge service invalidates stale cache entries when required

---

# Setup Instructions

## Prerequisites

Install:
- Docker
- Docker Compose
- Git

---

# Running the Project

Clone the repository:

```bash
git clone https://github.com/dhruv0525/distributed-cdn-system.git
cd distributed-cdn-system
```

Start all services:

```bash
docker-compose up --build
```

Run in detached mode:

```bash
docker-compose up -d --build
```

Stop all services:

```bash
docker-compose down
```

---

# Service Ports

| Service | Port |
|---|---|
| Frontend Dashboard | 3000 |
| Traffic Manager | 8000 |
| Edge Node A | 8001 |
| Edge Node B | 8002 |
| Edge Node C | 8003 |
| Origin Server | 8004 |
| Service Registry | 8005 |
| Purge Service | 8006 |
| Monitoring Service | 8007 |

---

# Example Scenarios

## Cache Hit
- Request served directly from edge cache
- Lower response time

## Cache Miss
- Edge node fetches content from Origin Server
- Content stored for future requests

## Node Failure
- Traffic Manager detects unhealthy node
- Requests rerouted automatically

## Cache Purge
- Purge service invalidates distributed cached data
- Ensures consistency across nodes

---

# Future Improvements

- Geographic routing simulation
- Redis distributed caching
- Kubernetes deployment
- HTTPS support
- Rate limiting
- CDN analytics engine
- Distributed tracing with OpenTelemetry
- Autoscaling edge nodes

---

# Learning Outcomes

This project demonstrates practical understanding of:
- Distributed systems
- CDN architecture
- Microservices
- Load balancing
- Caching strategies
- Failover systems
- Service discovery
- Container orchestration
- Observability and monitoring
---

# License

MIT License

---

# Author

Dhruv Thakor,
Pooja Sharma,
Jaimin Koriya,
Tanvi Patange, 
Tanisha Mishra,
Medha Kumar

