"""Main FastAPI application entry point."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from prometheus_client import (
    generate_latest,
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    Gauge,
    Info
)
from dotenv import load_dotenv
import time
import os

# Load environment variables
load_dotenv()

# Import routes and database
from .routes import (
    alert_routes,
    case_routes,
    customer_routes,
    knowledge_routes,
    transaction_routes,
    triage_routes
)
from .routes import dashboard_routes
from .utils.database import engine
from .utils.rate_limiter import rate_limit_middleware
from .models.base import Base
from .utils.logger import setup_logging
from .utils.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_progress,
    rate_limit_exceeded_total
)

# Set up logger
logger = setup_logging(__name__)
logger.info("🚀 Starting Case Resolution Console API")

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Case Resolution Console API",
    description="API for managing cases, alerts, and customer data",
    version="1.0.0"
)


@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    """Middleware to collect Prometheus metrics for HTTP requests."""
    # Skip metrics collection for /metrics endpoint to avoid recursion
    if request.url.path == "/metrics":
        return await call_next(request)
    
    method = request.method
    endpoint = request.url.path
    
    # Track request in progress
    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
    
    # Track request duration
    start_time = time.time()
    
    try:
        response = await call_next(request)
        status = response.status_code
        
        # Record metrics
        duration = time.time() - start_time
        http_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
        
        # Track rate limiting
        if status == 429:
            rate_limit_exceeded_total.labels(endpoint=endpoint).inc()
            logger.warning(f"Rate limit exceeded for {method} {endpoint}")
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        http_requests_total.labels(method=method, endpoint=endpoint, status="500").inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
        logger.error(f"Request error: {method} {endpoint} - {str(e)}")
        raise
        
    finally:
        # Decrement in-progress counter
        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

# Add rate limiting middleware (token bucket: 5 req/s per client)
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    return await rate_limit_middleware(request, call_next)



# Include routers
app.include_router(alert_routes.router, prefix="/api", tags=["alerts"])
app.include_router(case_routes.router, prefix="/api", tags=["cases"])
app.include_router(customer_routes.router, prefix="/api", tags=["customers"])
app.include_router(knowledge_routes.router, prefix="/api", tags=["knowledge"])
app.include_router(transaction_routes.router, prefix="/api", tags=["transactions"])
app.include_router(triage_routes.router, prefix="/api", tags=["triage"])
app.include_router(dashboard_routes.router, tags=["dashboard"])

# Health check endpoints
@app.get("/")
def root():
    """Root endpoint for basic health check."""
    return {"status": "ok", "message": "Case Resolution Console API is running"}

@app.get("/health")
async def health():
    """Detailed health check endpoint."""
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    data = generate_latest()
    return PlainTextResponse(data, media_type=CONTENT_TYPE_LATEST)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
