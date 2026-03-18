# Distributed CDN System

## Overview
This project simulates a distributed CDN system with multiple edge nodes, intelligent routing, caching, and monitoring.

## Components
- Traffic Manager
- Edge Nodes (A, B, C)
- Origin Server
- Service Registry
- Purge Service
- Monitoring Service
- Frontend Dashboard

## Features
- Dynamic node registration
- Intelligent routing
- Cache (LRU + TTL)
- Load balancing and failover
- Cache invalidation (purge)
- Request tracing
- Live monitoring dashboard

## Folder Structure

```
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

## How to Run
```bash
docker-compose up --build