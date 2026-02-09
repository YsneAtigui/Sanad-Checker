# Quick Start Guide - Development Setup

## Prerequisites
- Docker Desktop installed and running
- Python 3.10+ with venv activated

## Step-by-Step Setup

### 1. Start Infrastructure Services (PostgreSQL + Redis + Ollama)

```bash
# Start all services
docker-compose up -d postgres redis ollama

# Check if services are running
docker-compose ps

# View logs if needed
docker-compose logs -f postgres redis
```

### 2. Create .env File

Create `.env` file in project root if it doesn't exist:

```bash
# Copy from example
copy .env.example .env  # Windows
# OR
cp .env.example .env    # Linux/Mac
```

Edit `.env` with these values:
```env
DATABASE_URL=postgresql://sanad:sanad123@localhost:5432/sanad_aeo
REDIS_URL=redis://localhost:6379/0
OLLAMA_HOST=http://localhost:11434
```

### 3. Run Database Migrations

```bash
# Activate venv if not already
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Run migrations
alembic upgrade head
```

### 4. Start Celery Worker (Windows - Solo Pool)

```bash
# In a new terminal with venv activated
celery -A app.celery_app worker --pool=solo --loglevel=info
```

### 5. Start FastAPI Server

```bash
# In another terminal with venv activated
uvicorn app.main:app --reload --port 8000
```

### 6. Verify Everything is Running

Open browser to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health/full

Should show:
```json
{
  "status": "healthy",
  "checks": {
    "database": {"status": "healthy"},
    "celery": {"status": "healthy", "workers": 1},
    "redis": {"status": "healthy"}
  }
}
```

## Running E2E Tests

```bash
# With all services running
python tests/test_e2e.py
```

## Stopping Services

```bash
# Stop containers
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## Troubleshooting

### Redis Connection Refused
```bash
# Check if Redis is running
docker ps | findstr redis

# Restart Redis
docker-compose restart redis
```

### Database Connection Error
```bash
# Check PostgreSQL
docker ps | findstr postgres

# View logs
docker-compose logs postgres
```

### Celery Worker Crashes on Windows
Use `--pool=solo` flag:
```bash
celery -A app.celery_app worker --pool=solo --loglevel=info
```

## Quick Commands Reference

```bash
# Start infrastructure only
docker-compose up -d postgres redis ollama

# Start everything (including API and Celery)
docker-compose up -d

# View all logs
docker-compose logs -f

# Restart a service
docker-compose restart redis

# Check service status
docker-compose ps

# Stop all
docker-compose down
```
