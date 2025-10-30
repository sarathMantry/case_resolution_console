"""
Agent state definition for the LangGraph workflow.
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class AgentState(TypedDict):
    """Shared state passed between agents in the workflow."""
    
    # Input data
    customer_id: str
    alert_id: Optional[str]
    transaction_id: Optional[str]
    
    # Execution metadata
    plan: List[str]
    current_step: str
    step_index: int
    retries: Dict[str, int]
    errors: List[Dict[str, Any]]
    start_time: datetime
    
    # Agent outputs
    profile: Optional[Dict[str, Any]]
    recent_transactions: Optional[List[Dict[str, Any]]]
    insights: Optional[Dict[str, Any]]
    risk_signals: Optional[Dict[str, Any]]
    fraud_analysis: Optional[Dict[str, Any]]
    kb_results: Optional[List[Dict[str, Any]]]
    compliance_check: Optional[Dict[str, Any]]
    
    # Final decision
    decision: Optional[str]  # "approve", "review", "block", "escalate"
    proposed_action: Optional[str]  # "freeze_card", "open_dispute", "contact_customer", "mark_false_positive"
    confidence: Optional[float]
    reasoning: Optional[List[str]]
    citations: Optional[List[Dict[str, Any]]]
    
    # Alert creation
    alert_created: bool
    alert_data: Optional[Dict[str, Any]]


class StepResult(TypedDict):
    """Result from a single agent step."""
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    duration: float
    retries: int
