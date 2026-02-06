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
