# Docker Containers - Status Report

**Status**: ✅ All containers running successfully

## Running Containers

| Container | Status | Port Mapping | Health |
|-----------|--------|--------------|---------|
| **ai_mentor_backend** | Running | 8000:8000 | ✅ Healthy |
| **ai_mentor_frontend** | Running | 3000:3000 | ✅ Healthy |
| **ai_mentor_postgres** | Running | 5433:5432 | ✅ Healthy |
| **ai_mentor_mongodb** | Running | 27018:27017 | ✅ Healthy |
| **ai_mentor_redis** | Running | 6380:6379 | ✅ Healthy |

## Service URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5433
- **MongoDB**: localhost:27018
- **Redis**: localhost:6380

## Issues Fixed

1. ✅ **MongoDB SSL Connection Issue**: Fixed SSL handshake error by conditionally applying TLS settings only for MongoDB Atlas connections (remote). Local MongoDB containers don't require SSL.

## Quick Commands

### Start all containers
```bash
docker-compose up -d
```

### Stop all containers
```bash
docker-compose down
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Rebuild and restart
```bash
docker-compose down
docker-compose up --build -d
```

### Check container status
```bash
docker-compose ps
```

## Database Connections

### PostgreSQL
- Host: localhost
- Port: 5433
- Database: ai_mentor
- User: postgres
- Password: postgres123

### MongoDB
- Host: localhost
- Port: 27018
- Database: ai_mentor

### Redis
- Host: localhost
- Port: 6380

## Development Features

- ✅ Hot reload enabled for backend (FastAPI auto-reload)
- ✅ Hot reload enabled for frontend (Next.js dev mode)
- ✅ Volume mounting for live code changes
- ✅ Health checks for all database services
- ✅ Network isolation with custom bridge network

## Notes

- All services are connected via `ai_mentor_network` Docker network
- Volumes are persisted for databases (postgres_data, mongo_data, redis_data)
- Hot reload is configured for development with file watching enabled
- All containers start automatically with dependency health checks
