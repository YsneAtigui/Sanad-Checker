# Celery Configuration for Windows Development

This document explains how to run Celery on Windows for the Sanad AEO Auditor project.

## Issues on Windows

Celery has known compatibility issues with Windows due to:
1. **Multiprocessing** - Windows doesn't support `fork()` like Unix systems
2. **Billiard pool** - Permission errors with shared memory on Windows

## Solution: Use Solo Pool or Gevent

For Windows development, use one of these workarounds:

### Option 1: Solo Pool (Simplest - Single Process)

```bash
celery -A app.celery_app worker --pool=solo --loglevel=info
```

**Pros:**
- No multiprocessing issues
- Works reliably on Windows
- Good for development/testing

**Cons:**
- Single process only (no concurrency)
- Slower for multiple tasks

### Option 2: Gevent Pool (Concurrent)

First install gevent:
```bash
pip install gevent
```

Then run:
```bash
celery -A app.celery_app worker --pool=gevent --concurrency=10 --loglevel=info
```

**Pros:**  
- Supports concurrency (greenlets)
- Better performance than solo

**Cons:**
- Requires additional dependency
- May have compatibility issues with some libraries

### Option 3: Eventlet Pool

Install eventlet:
```bash
pip install eventlet
```

Run:
```bash
celery -A app.celery_app worker --pool=eventlet --concurrency=10 --loglevel=info
```

## Redis Setup

You also need Redis running. For Windows:

### Option A: Redis via Docker (Recommended)
```bash
docker run -d -p 6379:6379 redis:latest
```

### Option B: WSL2 + Redis
```bash
# In WSL2:
sudo apt-get install redis-server
redis-server
```

### Option C: Windows Port (Not Recommended)
Download from: https://github.com/tporadowski/redis/releases

## Recommended Development Setup

1. **Start Redis** (in separate terminal):
   ```bash
   docker run -d -p 6379:6379 redis:latest
   ```

2. **Start Celery Worker** (in project terminal):
   ```bash
   celery -A app.celery_app worker --pool=solo --loglevel=info
   ```

3. **Start FastAPI** (in another terminal):
   ```bash
   uvicorn app.main:app --reload
   ```

## For Production (Linux)

On Linux servers, use the default prefork pool:
```bash
celery -A app.celery_app worker --loglevel=info --concurrency=4
```

## Testing Without Celery

For quick testing, you can run tasks synchronously:

```python
# In your code
from app.tasks.audit_tasks import run_audit_task

# Call directly (blocks until complete)
result = run_audit_task(audit_id, options)
```

## Quick Start Commands

```bash
# Terminal 1: Redis
docker run -d -p 6379:6379 redis:latest

# Terminal 2: Celery
celery -A app.celery_app worker --pool=solo --loglevel=info

# Terminal 3: FastAPI
uvicorn app.main:app --reload --port 8000
```
