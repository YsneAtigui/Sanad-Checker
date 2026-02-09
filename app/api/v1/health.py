from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "sanad-aeo-auditor"
    }


@router.get("/health/db")
async def db_health_check():
    """Database health check"""
    from app.database import engine
    from sqlalchemy import text
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@router.get("/health/celery")
async def celery_health_check():
    """Celery health check"""
    from app.celery_app import celery_app
    
    try:
        # Ping workers
        stats = celery_app.control.inspect().stats()
        if stats:
            return {"status": "healthy", "celery": "workers_active", "workers": len(stats)}
        else:
            return {"status": "unhealthy", "celery": "no_workers"}
    except Exception as e:
        return {"status": "unhealthy", "celery": "error", "error": str(e)}


@router.get("/health/redis")
async def redis_health_check():
    """Redis cache health check"""
    from app.cache import redis_client
    
    try:
        is_healthy = redis_client.health_check()
        if is_healthy:
            return {"status": "healthy", "redis": "connected"}
        else:
            return {"status": "unhealthy", "redis": "disconnected"}
    except Exception as e:
        return {"status": "unhealthy", "redis": "error", "error": str(e)}


@router.get("/health/full")
async def full_health_check():
    """
    Comprehensive health check for all services
    
    Returns status for:
    - API service
    - Database connection
    - Celery workers
    - Redis cache
    """
    from app.database import engine
    from sqlalchemy import text
    from app.celery_app import celery_app
    from app.cache import redis_client
    
    health_status = {
        "status": "healthy",
        "checks": {}
    }
    
    # Database check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Celery check
    try:
        stats = celery_app.control.inspect().stats()
        if stats:
            health_status["checks"]["celery"] = {"status": "healthy", "workers": len(stats)}
        else:
            health_status["checks"]["celery"] = {"status": "unhealthy", "message": "no_workers"}
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["celery"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Redis check
    try:
        is_healthy = redis_client.health_check()
        if is_healthy:
            health_status["checks"]["redis"] = {"status": "healthy"}
        else:
            health_status["checks"]["redis"] = {"status": "unhealthy"}
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    return health_status

