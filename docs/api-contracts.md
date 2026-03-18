# API Contracts

## Traffic Manager
GET /route?file=<filename>
Headers:
- X-Client-Location

---

## Edge Node
GET /fetch?file=<filename>
GET /health
DELETE /cache/<filename>

---

## Origin Server
GET /get-file/<filename>
POST /upload

---

## Service Registry
POST /register
POST /heartbeat
GET /nodes

---

## Purge Service
POST /purge/<filename>

---

## Monitoring
GET /metrics
GET /logs
GET /nodes-status