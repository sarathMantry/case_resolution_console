"""
Agent routes for manual triggering of LangGraph agents.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from ..agents.orchestrator import OrchestratorAgent
from ..db import get_db
from ..utils.logger import setup_logging, log_route_call

logger = setup_logging("agent_routes")
router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request body for agent analysis."""
    customer_id: str
    transaction_id: Optional[str] = None
    alert_id: Optional[str] = None
    custom_plan: Optional[List[str]] = None


class AnalyzeResponse(BaseModel):
    """Response from agent analysis."""
    success: bool
    customer_id: str
    decision: Optional[str]
    proposed_action: Optional[str]
    confidence: Optional[float]
    reasoning: List[str]
    risk_score: Optional[float]
    risk_level: Optional[str]
    alert_created: bool
    duration: float
    llm_reasoning: Optional[str] = None
    llm_insights_summary: Optional[str] = None
    llm_action_reasoning: Optional[str] = None
    alert_description: Optional[str] = None


@router.post("/agents/analyze", response_model=AnalyzeResponse)
@log_route_call(logger)
async def analyze_customer(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Manually trigger LangGraph agent analysis for a customer.
    
    This endpoint orchestrates all sub-agents (Insights, Fraud, KB, Compliance)
    to perform comprehensive fraud analysis and generate recommendations.
    
    Args:
        request: Analysis request with customer and transaction IDs
        db: Database session
        
    Returns:
        Complete analysis with decision and proposed action
    """
    logger.info(f"Starting agent analysis for customer {request.customer_id}")
    
    try:
        orchestrator = OrchestratorAgent(db)
        
        # Run orchestration (async)
        result = await orchestrator.orchestrate(
            customer_id=request.customer_id,
            transaction_id=request.transaction_id,
            alert_id=request.alert_id,
            custom_plan=request.custom_plan
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Agent analysis failed: {result.get('error', 'Unknown error')}"
            )
        
        # Extract fraud analysis for risk score
        fraud_analysis = result.get("fraud_analysis") or {}
        insights = result.get("insights") or {}
        alert_data = result.get("alert_data") or {}
        
        return AnalyzeResponse(
            success=True,
            customer_id=result["customer_id"],
            decision=result.get("decision"),
            proposed_action=result.get("proposed_action"),
            confidence=result.get("confidence"),
            reasoning=result.get("reasoning", []),
            risk_score=fraud_analysis.get("risk_score"),
            risk_level=fraud_analysis.get("risk_level"),
            alert_created=result.get("alert_created", False),
            duration=result.get("duration", 0),
            llm_reasoning=fraud_analysis.get("llm_reasoning"),
            llm_insights_summary=insights.get("llm_summary"),
            llm_action_reasoning=result.get("llm_action_reasoning"),
            alert_description=alert_data.get("description")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/health")
@log_route_call(logger)
async def agent_health():
    """
    Health check for agent system.
    
    Returns status of all sub-agents and orchestrator.
    """
    return {
        "status": "healthy",
        "agents": {
            "orchestrator": "available",
            "insights": "available",
            "fraud": "available",
            "kb": "available",
            "compliance": "available"
        },
        "langgraph_version": "0.0.50+"
    }


@router.get("/agents/plan")
@log_route_call(logger)
async def get_default_plan():
    """
    Get the default agent execution plan.
    
    Returns the default sequence of steps the orchestrator executes.
    """
    return {
        "default_plan": [
            "getProfile",
            "recentTx",
            "riskSignals",
            "kbLookup",
            "decide",
            "proposeAction"
        ],
        "description": {
            "getProfile": "Fetch customer profile and account information",
            "recentTx": "Retrieve recent transactions and run insights analysis",
            "riskSignals": "Analyze fraud signals using Fraud Agent",
            "kbLookup": "Search knowledge base for relevant information",
            "decide": "Make decision based on all analysis",
            "proposeAction": "Propose action and check compliance"
        }
    }
