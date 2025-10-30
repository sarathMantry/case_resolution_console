"""
Prometheus metrics for monitoring application performance and business operations.
Centralized metrics that can be imported by any module.
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import os

# ============================================================================
# HTTP METRICS
# ============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)

# ============================================================================
# RATE LIMITING METRICS
# ============================================================================

rate_limit_exceeded_total = Counter(
    'rate_limit_exceeded_total',
    'Total number of rate limit exceeded responses',
    ['endpoint']
)

rate_limit_tokens_remaining = Gauge(
    'rate_limit_tokens_remaining',
    'Current token bucket tokens remaining',
    ['client']
)

# ============================================================================
# DATABASE METRICS
# ============================================================================

db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

# ============================================================================
# REDIS METRICS
# ============================================================================

redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status']
)

redis_operation_duration_seconds = Histogram(
    'redis_operation_duration_seconds',
    'Redis operation duration in seconds',
    ['operation'],
    buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1)
)

# ============================================================================
# BUSINESS METRICS - TRIAGE
# ============================================================================

triage_operations_total = Counter(
    'triage_operations_total',
    'Total triage operations',
    ['operation', 'status']
)

triage_duration_seconds = Histogram(
    'triage_duration_seconds',
    'Triage operation duration in seconds',
    ['operation'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

triage_alerts_processed = Counter(
    'triage_alerts_processed',
    'Total alerts processed by triage',
    ['status', 'risk_level']
)

triage_actions_taken = Counter(
    'triage_actions_taken',
    'Total triage actions taken',
    ['action', 'outcome']
)

triage_idempotent_requests = Counter(
    'triage_idempotent_requests',
    'Total idempotent triage requests (already processed)',
    ['action']
)

# ============================================================================
# WEBSOCKET METRICS
# ============================================================================

websocket_connections_total = Counter(
    'websocket_connections_total',
    'Total WebSocket connections',
    ['endpoint', 'status']
)

websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections',
    ['endpoint']
)

websocket_messages_sent = Counter(
    'websocket_messages_sent',
    'Total WebSocket messages sent',
    ['endpoint', 'message_type']
)

websocket_errors_total = Counter(
    'websocket_errors_total',
    'Total WebSocket errors',
    ['endpoint', 'error_type']
)

# ============================================================================
# CUSTOMER METRICS
# ============================================================================

customer_operations_total = Counter(
    'customer_operations_total',
    'Total customer operations',
    ['operation', 'status']
)

customer_risk_score = Histogram(
    'customer_risk_score',
    'Customer risk scores',
    buckets=(0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
)

# ============================================================================
# CASE METRICS
# ============================================================================

cases_created_total = Counter(
    'cases_created_total',
    'Total cases created',
    ['type', 'status']
)

case_resolution_duration_seconds = Histogram(
    'case_resolution_duration_seconds',
    'Time to resolve cases in seconds',
    ['type'],
    buckets=(3600, 7200, 14400, 28800, 43200, 86400, 172800, 604800)  # 1h to 1 week
)

# ============================================================================
# APPLICATION INFO
# ============================================================================

app_info = Info('app', 'Application information')
app_info.info({
    'name': 'Case Resolution Console',
    'version': '1.0.0',
    'environment': os.getenv('ENVIRONMENT', 'development'),
    'python_version': '3.11'
})

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def record_triage_operation(operation: str, status: str, duration: float = None):
    """Record a triage operation with optional duration."""
    triage_operations_total.labels(operation=operation, status=status).inc()
    if duration is not None:
        triage_duration_seconds.labels(operation=operation).observe(duration)


def record_triage_action(action: str, outcome: str, already_processed: bool = False):
    """Record a triage action."""
    triage_actions_taken.labels(action=action, outcome=outcome).inc()
    if already_processed:
        triage_idempotent_requests.labels(action=action).inc()


def record_websocket_message(endpoint: str, message_type: str):
    """Record a WebSocket message sent."""
    websocket_messages_sent.labels(endpoint=endpoint, message_type=message_type).inc()


def record_websocket_error(endpoint: str, error_type: str):
    """Record a WebSocket error."""
    websocket_errors_total.labels(endpoint=endpoint, error_type=error_type).inc()


def record_db_query(operation: str, table: str, duration: float):
    """Record a database query."""
    db_queries_total.labels(operation=operation, table=table).inc()
    db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)
