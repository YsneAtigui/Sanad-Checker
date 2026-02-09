import sys
import asyncio
import warnings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.api.v1 import health, audits, protocols, extraction, schema, edge, scoring, reports, analytics

# Fix for Windows + Python 3.13 + Playwright/Crawl4AI compatibility issues
if sys.platform == 'win32':
    # Use WindowsSelectorEventLoopPolicy for better subprocess support
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Suppress NotImplementedError warnings from Playwright
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")
    
    # Custom exception handler to suppress unhandled task exceptions from Playwright
    def custom_exception_handler(loop, context):
        exception = context.get('exception')
        # Suppress NotImplementedError from Playwright subprocess issues
        if isinstance(exception, NotImplementedError):
            return
        # For other exceptions, use default handler
        loop.default_exception_handler(context)
    
    # Set the custom exception handler
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(custom_exception_handler)

app = FastAPI(
    title="Sanad AEO Auditor API",
    description="AI-first auditor for Arabic e-commerce AEO compliance",
    version="0.1.0"
)

# Register global exception handlers
from app.exceptions import register_exception_handlers
register_exception_handlers(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(audits.router, prefix="/api/v1/audits", tags=["Audits"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(protocols.router, prefix="/api/v1/protocols", tags=["Protocols"])
app.include_router(extraction.router, prefix="/api/v1/extraction", tags=["Extraction"])
app.include_router(schema.router, prefix="/api/v1/schema", tags=["Schema"])
app.include_router(edge.router, prefix="/api/v1/edge", tags=["Edge Visibility"])
app.include_router(scoring.router, prefix="/api/v1/scoring", tags=["Content Scoring"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])


@app.get("/")
async def root():
    return {
        "message": "Sanad AEO Auditor API",
        "version": "0.1.0",
        "docs": "/docs",
        "dashboard": "/dashboard"
    }


@app.get("/dashboard")
async def dashboard():
    """Serve the dashboard HTML"""
    return FileResponse("frontend/index.html")
