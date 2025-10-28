from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter
import os
import time
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    response = await call_next(request)
    try:
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=str(response.status_code)).inc()
    except Exception:
        pass
    return response


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return PlainTextResponse(data, media_type=CONTENT_TYPE_LATEST)


@app.get('/api/health')
async def api_health():
    return {"ok": True, "env": os.getenv('NODE_ENV', 'dev')}


class TriageRequest(BaseModel):
    alertId: str | None = None


@app.post('/api/triage')
async def triage(body: TriageRequest):
    return {"runId": f"run_{int(time.time() * 1000)}", "alertId": body.alertId}


@app.get('/api/kb/search')
async def kb_search(q: str = ''):
    results = []
    if q:
        results = [{"docId": "kb1", "title": "Demo", "anchor": "#1", "extract": "demo extract"}]
    return {"results": results}
