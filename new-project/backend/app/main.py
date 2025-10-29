"""Main FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import routes and database
from .routes import (
    case_routes,
    customer_routes,
    knowledge_routes,
    transaction_routes
)
from .utils.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Case Resolution Console API",
    description="API for managing cases, alerts, and customer data",
    version="1.0.0"
)

# Configure metrics
REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])

@app.middleware("http")
async def metrics_middleware(request, call_next):
    response = await call_next(request)
    try:
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=str(response.status_code)
        ).inc()
    except Exception:
        pass
    return response



# Include routers
app.include_router(case_routes.router, tags=["cases"])
app.include_router(customer_routes.router, tags=["customers"])
app.include_router(knowledge_routes.router, tags=["knowledge"])
app.include_router(transaction_routes.router, tags=["transactions"])

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
