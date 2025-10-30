"""API routes for triage operations."""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import asyncio

from ..services.triage_service import TriageService
from ..utils.database import get_db
from ..utils.logger import setup_logging, log_route_call, safe_log_data
from ..utils.metrics import (
    websocket_connections_total,
    websocket_connections_active,
    record_websocket_message,
    record_websocket_error
)

# Set up logger for triage routes
logger = setup_logging(__name__)

router = APIRouter(prefix="/triage")


class ActionRequest(BaseModel):
    alert_id: str
    reason_code: str = "unauthorized"


@router.get("/{alert_id}", response_model=None)
@log_route_call(logger)
def get_triage_details(alert_id: str, db: Session = Depends(get_db)):
    """Get comprehensive triage details for an alert."""
    logger.info(f"GET /triage/{alert_id} - Fetching triage details")
    triage_service = TriageService(db)
    details = triage_service.get_triage_details(alert_id)
    if not details:
        logger.warning(f"GET /triage/{alert_id} - Alert not found")
        raise HTTPException(status_code=404, detail="Alert not found")
    logger.info(f"GET /triage/{alert_id} - Successfully retrieved details")
    return details


@router.post("/freeze-card", response_model=None)
@log_route_call(logger)
def freeze_card(
    action_request: ActionRequest,
    db: Session = Depends(get_db)
):
    """Freeze the card associated with an alert."""
    logger.info(f"POST /triage/freeze-card - alert_id: {action_request.alert_id}")
    triage_service = TriageService(db)
    try:
        result = triage_service.freeze_card(action_request.alert_id)
        logger.info(f"POST /triage/freeze-card - Success (idempotent: {result.get('already_processed', False)})")
        return result
    except ValueError as e:
        logger.error(f"POST /triage/freeze-card - Error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/open-dispute", response_model=None)
@log_route_call(logger)
def open_dispute(
    action_request: ActionRequest,
    db: Session = Depends(get_db)
):
    """Open a dispute case for an alert."""
    logger.info(f"POST /triage/open-dispute - alert_id: {action_request.alert_id}, reason: {action_request.reason_code}")
    triage_service = TriageService(db)
    try:
        result = triage_service.open_dispute(action_request.alert_id, action_request.reason_code)
        logger.info(f"POST /triage/open-dispute - Success (idempotent: {result.get('already_processed', False)})")
        return result
    except ValueError as e:
        logger.error(f"POST /triage/open-dispute - Error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/contact-customer", response_model=None)
@log_route_call(logger)
def contact_customer(
    action_request: ActionRequest,
    db: Session = Depends(get_db)
):
    """Mark alert for customer contact."""
    logger.info(f"POST /triage/contact-customer - alert_id: {action_request.alert_id}")
    triage_service = TriageService(db)
    try:
        result = triage_service.contact_customer(action_request.alert_id)
        logger.info(f"POST /triage/contact-customer - Success")
        return result
    except ValueError as e:
        logger.error(f"POST /triage/contact-customer - Error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/mark-false-positive", response_model=None)
@log_route_call(logger)
def mark_false_positive(
    action_request: ActionRequest,
    db: Session = Depends(get_db)
):
    """Mark an alert as a false positive."""
    logger.info(f"POST /triage/mark-false-positive - alert_id: {action_request.alert_id}")
    triage_service = TriageService(db)
    try:
        result = triage_service.mark_false_positive(action_request.alert_id)
        logger.info(f"POST /triage/mark-false-positive - Success (idempotent: {result.get('already_processed', False)})")
        return result
    except ValueError as e:
        logger.error(f"POST /triage/mark-false-positive - Error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))


@router.websocket("/ws/{alert_id}")
async def triage_stream(websocket: WebSocket, alert_id: str):
    """Stream triage execution progress in real-time via WebSocket."""
    logger.info(f"WebSocket connection initiated for alert: {alert_id}")
    
    # Track connection
    websocket_connections_total.labels(endpoint="/triage/ws", status="accepted").inc()
    websocket_connections_active.labels(endpoint="/triage/ws").inc()
    
    await websocket.accept()
    
    async def safe_send(data: dict) -> bool:
        """Safely send data, return False if connection is closed."""
        try:
            await websocket.send_json(data)
            record_websocket_message("/triage/ws", data.get("type", "unknown"))
            return True
        except Exception as e:
            logger.warning(f"WebSocket send failed for alert {alert_id}: {str(e)}")
            record_websocket_error("/triage/ws", "send_failed")
            return False
    
    try:
        # Get database session
        db = next(get_db())
        triage_service = TriageService(db)
        logger.debug(f"WebSocket: Starting triage analysis for alert {alert_id}")
        
        # Send initial status
        if not await safe_send({
            "type": "status",
            "message": "Starting triage analysis...",
            "status": "started"
        }):
            return
        await asyncio.sleep(0.3)
        
        # Get triage details
        details = triage_service.get_triage_details(alert_id)
        if not details:
            await safe_send({
                "type": "error",
                "message": "Alert not found"
            })
            return
        
        # Stream alert information
        if not await safe_send({
            "type": "alert",
            "data": {
                "alert_id": details["alert_id"],
                "customer_id": details["customer_id"],
                "status": details["status"],
                "created_at": details["created_at"]
            }
        }):
            return
        await asyncio.sleep(0.2)
        
        # Stream risk information
        if not await safe_send({
            "type": "risk",
            "data": {
                "risk": details["triage"]["risk"],
                "recommended_action": details["recommended_action"]
            }
        }):
            return
        await asyncio.sleep(0.2)
        
        # Stream transaction details
        if details.get("transaction"):
            if not await safe_send({
                "type": "transaction",
                "data": details["transaction"]
            }):
                return
            await asyncio.sleep(0.2)
        
        # Stream reasons
        if details.get("triage", {}).get("reasons"):
            if not await safe_send({
                "type": "reasons",
                "data": details["triage"]["reasons"]
            }):
                return
            await asyncio.sleep(0.2)
        
        # Stream tool calls (simulate progressive execution)
        if details.get("tool_calls"):
            for tool_call in details["tool_calls"]:
                # Send tool call as "running"
                running_call = {**tool_call, "status": "running"}
                if not await safe_send({
                    "type": "tool_call",
                    "data": running_call
                }):
                    return
                
                # Simulate execution time
                duration_ms = tool_call.get("duration_ms", 100)
                await asyncio.sleep(min(duration_ms / 1000.0, 0.5))
                
                # Send tool call as completed
                if not await safe_send({
                    "type": "tool_call",
                    "data": tool_call
                }):
                    return
                await asyncio.sleep(0.1)
        
        # Stream citations
        if details.get("citations"):
            if not await safe_send({
                "type": "citations",
                "data": details["citations"]
            }):
                return
            await asyncio.sleep(0.2)
        
        # Send completion
        logger.info(f"WebSocket: Triage analysis completed for alert {alert_id}")
        await safe_send({
            "type": "complete",
            "message": "Triage analysis complete",
            "data": {
                "recommended_action": details["recommended_action"],
                "latency_ms": details.get("triage", {}).get("latency_ms", 0)
            }
        })
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket: Client disconnected for alert {alert_id}")
        websocket_connections_total.labels(endpoint="/triage/ws", status="disconnected").inc()
        pass
    except Exception as e:
        logger.error(f"WebSocket error for alert {alert_id}: {str(e)}", exc_info=True)
        websocket_connections_total.labels(endpoint="/triage/ws", status="error").inc()
        record_websocket_error("/triage/ws", "exception")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        # Decrement active connections counter
        websocket_connections_active.labels(endpoint="/triage/ws").dec()
        try:
            await websocket.close()
        except:
            pass
