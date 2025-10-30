"""
Orchestrator Agent: Plans and executes sub-agents with timeouts and retries using LangGraph.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from langgraph.graph import Graph, END
from langchain_core.runnables import RunnableConfig

from .state import AgentState, StepResult
from .insights_agent import InsightsAgent
from .fraud_agent import FraudAgent
from .kb_agent import KBAgent
from .compliance_agent import ComplianceAgent
from ..utils.logger import setup_logging, log_service_call
from ..utils.metrics import record_triage_operation
from ..utils.gemini_llm import get_gemini_llm

logger = setup_logging("orchestrator")


class OrchestratorAgent:
    """
    Orchestrates the execution of sub-agents using LangGraph.
    Implements bounded planning, timeouts, retries, and error handling.
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
        
        # Initialize sub-agents
        self.insights_agent = InsightsAgent(db_session)
        self.fraud_agent = FraudAgent(db_session)
        self.kb_agent = KBAgent()
        self.compliance_agent = ComplianceAgent(db_session)
        self.llm = get_gemini_llm()
        
        # Configuration
        self.max_retries = 3
        self.step_timeout = 30  # seconds
        self.total_timeout = 120  # seconds
        
        # Default execution plan
        self.default_plan = [
            "getProfile",
            "recentTx", 
            "riskSignals",
            "kbLookup",
            "decide",
            "proposeAction"
        ]
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> Graph:
        """Build the LangGraph workflow."""
        workflow = Graph()
        
        # Add nodes for each step
        workflow.add_node("getProfile", self._get_profile_node)
        workflow.add_node("recentTx", self._recent_tx_node)
        workflow.add_node("riskSignals", self._risk_signals_node)
        workflow.add_node("kbLookup", self._kb_lookup_node)
        workflow.add_node("decide", self._decide_node)
        workflow.add_node("proposeAction", self._propose_action_node)
        
        # Define edges (execution flow)
        workflow.add_edge("getProfile", "recentTx")
        workflow.add_edge("recentTx", "riskSignals")
        workflow.add_edge("riskSignals", "kbLookup")
        workflow.add_edge("kbLookup", "decide")
        workflow.add_edge("decide", "proposeAction")
        workflow.add_edge("proposeAction", END)
        
        # Set entry point
        workflow.set_entry_point("getProfile")
        
        return workflow.compile()
    
    @log_service_call(logger)
    async def orchestrate(
        self,
        customer_id: str,
        transaction_id: Optional[str] = None,
        alert_id: Optional[str] = None,
        custom_plan: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate the agent workflow.
        
        Args:
            customer_id: Customer identifier
            transaction_id: Specific transaction to analyze (optional)
            alert_id: Alert ID if creating alert
            custom_plan: Custom execution plan (optional)
            
        Returns:
            Complete analysis with decision and proposed action
        """
        start_time = time.time()
        workflow_start = datetime.utcnow()
        
        try:
            # Initialize state
            initial_state: AgentState = {
                "customer_id": customer_id,
                "alert_id": alert_id,
                "transaction_id": transaction_id,
                "plan": custom_plan or self.default_plan,
                "current_step": "",
                "step_index": 0,
                "retries": {},
                "errors": [],
                "start_time": workflow_start,
                "profile": None,
                "recent_transactions": None,
                "insights": None,
                "risk_signals": None,
                "fraud_analysis": None,
                "kb_results": None,
                "compliance_check": None,
                "decision": None,
                "proposed_action": None,
                "confidence": None,
                "reasoning": None,
                "citations": None,
                "alert_created": False,
                "alert_data": None
            }
            
            logger.info(f"Starting orchestration for customer {customer_id}, plan: {initial_state['plan']}")
            
            # Execute workflow with timeout
            try:
                final_state = await asyncio.wait_for(
                    self._execute_workflow(initial_state),
                    timeout=self.total_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Workflow timeout after {self.total_timeout}s")
                return {
                    "success": False,
                    "error": f"Workflow timeout after {self.total_timeout} seconds",
                    "duration": time.time() - start_time
                }
            
            duration = time.time() - start_time
            
            # Record metrics
            status = "success" if final_state.get("decision") else "error"
            record_triage_operation("orchestration", status, duration)
            
            result = {
                "success": True,
                "customer_id": customer_id,
                "alert_id": alert_id,
                "transaction_id": transaction_id,
                "decision": final_state.get("decision"),
                "proposed_action": final_state.get("proposed_action"),
                "confidence": final_state.get("confidence"),
                "reasoning": final_state.get("reasoning", []),
                "citations": final_state.get("citations", []),
                "profile": final_state.get("profile"),
                "insights": final_state.get("insights"),
                "fraud_analysis": final_state.get("fraud_analysis"),
                "compliance_check": final_state.get("compliance_check"),
                "errors": final_state.get("errors", []),
                "alert_created": final_state.get("alert_created", False),
                "alert_data": final_state.get("alert_data"),
                "duration": duration,
                "workflow_timestamp": workflow_start.isoformat()
            }
            
            logger.info(
                f"Orchestration complete: decision={final_state.get('decision')}, "
                f"action={final_state.get('proposed_action')}, duration={duration:.2f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Orchestration error: {str(e)}")
            duration = time.time() - start_time
            record_triage_operation("orchestration", "error", duration)
            return {
                "success": False,
                "error": str(e),
                "duration": duration
            }
    
    async def _execute_workflow(self, initial_state: AgentState) -> AgentState:
        """Execute the LangGraph workflow."""
        # Run the compiled workflow
        config = RunnableConfig(recursion_limit=10)
        final_state = await self.workflow.ainvoke(initial_state, config)
        return final_state
    
    async def _get_profile_node(self, state: AgentState) -> AgentState:
        """Get customer profile."""
        state["current_step"] = "getProfile"
        logger.info(f"Executing step: getProfile for customer {state['customer_id']}")
        
        try:
            # Simulate profile fetch (in real impl, query from DB)
            profile = await self._fetch_profile(state["customer_id"])
            state["profile"] = profile
            
        except Exception as e:
            logger.error(f"Error in getProfile: {e}")
            state["errors"].append({"step": "getProfile", "error": str(e)})
        
        state["step_index"] += 1
        return state
    
    async def _recent_tx_node(self, state: AgentState) -> AgentState:
        """Fetch recent transactions."""
        state["current_step"] = "recentTx"
        logger.info(f"Executing step: recentTx for customer {state['customer_id']}")
        
        try:
            transactions = await self._fetch_transactions(state["customer_id"])
            state["recent_transactions"] = transactions
            
            # Run insights agent
            insights_result = self.insights_agent.analyze(
                state["customer_id"],
                transactions
            )
            if insights_result.get("success"):
                state["insights"] = insights_result
            
        except Exception as e:
            logger.error(f"Error in recentTx: {e}")
            state["errors"].append({"step": "recentTx", "error": str(e)})
        
        state["step_index"] += 1
        return state
    
    async def _risk_signals_node(self, state: AgentState) -> AgentState:
        """Analyze risk signals."""
        state["current_step"] = "riskSignals"
        logger.info(f"Executing step: riskSignals for customer {state['customer_id']}")
        
        try:
            if state["recent_transactions"] and state["profile"]:
                fraud_result = self.fraud_agent.analyze(
                    state["customer_id"],
                    state.get("transaction_id"),
                    state["recent_transactions"],
                    state["profile"]
                )
                
                if fraud_result.get("success"):
                    state["fraud_analysis"] = fraud_result
                    state["risk_signals"] = {
                        "risk_score": fraud_result.get("risk_score"),
                        "risk_level": fraud_result.get("risk_level"),
                        "signals": fraud_result.get("signal_scores", {})
                    }
            
        except Exception as e:
            logger.error(f"Error in riskSignals: {e}")
            state["errors"].append({"step": "riskSignals", "error": str(e)})
        
        state["step_index"] += 1
        return state
    
    async def _kb_lookup_node(self, state: AgentState) -> AgentState:
        """Lookup knowledge base."""
        state["current_step"] = "kbLookup"
        logger.info(f"Executing step: kbLookup for customer {state['customer_id']}")
        
        try:
            # Build search query from fraud reasons
            fraud_analysis = state.get("fraud_analysis", {})
            reasons = fraud_analysis.get("reasons", [])
            
            if reasons:
                search_query = " ".join(reasons[:3])  # Use top 3 reasons
                kb_result = self.kb_agent.search(search_query, max_results=5)
                
                if kb_result.get("success"):
                    state["kb_results"] = kb_result.get("results", [])
                    state["citations"] = [
                        {
                            "title": r["title"],
                            "anchor": r["anchor"],
                            "relevance": r["relevance_score"]
                        }
                        for r in kb_result.get("results", [])
                    ]
            
        except Exception as e:
            logger.error(f"Error in kbLookup: {e}")
            state["errors"].append({"step": "kbLookup", "error": str(e)})
        
        state["step_index"] += 1
        return state
    
    async def _decide_node(self, state: AgentState) -> AgentState:
        """Make decision based on analysis."""
        state["current_step"] = "decide"
        logger.info(f"Executing step: decide for customer {state['customer_id']}")
        
        try:
            fraud_analysis = state.get("fraud_analysis", {})
            risk_score = fraud_analysis.get("risk_score", 0)
            reasons = fraud_analysis.get("reasons", [])
            
            # Decision logic based on risk score
            if risk_score >= 80:
                decision = "block"
                confidence = 0.95
            elif risk_score >= 60:
                decision = "review"
                confidence = 0.85
            elif risk_score >= 40:
                decision = "escalate"
                confidence = 0.70
            else:
                decision = "approve"
                confidence = 0.90
            
            state["decision"] = decision
            state["confidence"] = confidence
            state["reasoning"] = reasons
            
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            state["errors"].append({"step": "decide", "error": str(e)})
            state["decision"] = "escalate"
            state["confidence"] = 0.5
        
        state["step_index"] += 1
        return state
    
    async def _propose_action_node(self, state: AgentState) -> AgentState:
        """Propose action and check compliance."""
        state["current_step"] = "proposeAction"
        logger.info(f"Executing step: proposeAction for customer {state['customer_id']}")
        
        try:
            fraud_analysis = state.get("fraud_analysis", {})
            proposed_action = fraud_analysis.get("recommended_action", "review_manual")
            
            # Check compliance
            if state["recent_transactions"] and state["profile"]:
                target_tx = state["recent_transactions"][0] if state["recent_transactions"] else {}
                
                compliance_result = self.compliance_agent.check_compliance(
                    state["customer_id"],
                    target_tx,
                    state["profile"],
                    proposed_action
                )
                
                state["compliance_check"] = compliance_result
                
                # Override action if not compliant
                if not compliance_result.get("can_proceed", True):
                    proposed_action = "manual_review_required"
                    state["reasoning"].append("Compliance check failed - manual review required")
            
            state["proposed_action"] = proposed_action
            
            # Use LLM for enhanced action recommendation
            if self.llm.enabled:
                try:
                    llm_recommendation = self.llm.generate_action_recommendation(
                        risk_score=fraud_analysis.get("risk_score", 0),
                        fraud_reasons=state.get("reasoning", []),
                        compliance_status=compliance_result,
                        kb_citations=state.get("kb_results", [])
                    )
                    if llm_recommendation:
                        state["llm_recommended_action"] = llm_recommendation["action"]
                        state["llm_action_reasoning"] = llm_recommendation["reasoning"]
                        # Override with LLM recommendation if available
                        proposed_action = llm_recommendation["action"]
                        state["proposed_action"] = proposed_action
                except Exception as e:
                    logger.warning(f"LLM action recommendation failed: {e}")
            
            # Create alert if risk score is high
            if fraud_analysis.get("risk_score", 0) >= 40:
                state["alert_created"] = True
                
                # Generate enhanced alert description using LLM
                alert_data = {
                    "customer_id": state["customer_id"],
                    "transaction_id": state.get("transaction_id"),
                    "risk_score": fraud_analysis.get("risk_score"),
                    "risk_level": fraud_analysis.get("risk_level"),
                    "proposed_action": proposed_action,
                    "reasons": state.get("reasoning", []),
                    "created_at": datetime.utcnow().isoformat()
                }
                
                if self.llm.enabled:
                    try:
                        enhanced_description = self.llm.enhance_alert_description(alert_data)
                        if enhanced_description:
                            alert_data["description"] = enhanced_description
                    except Exception as e:
                        logger.warning(f"LLM alert description failed: {e}")
                
                state["alert_data"] = alert_data
            
        except Exception as e:
            logger.error(f"Error in proposeAction: {e}")
            state["errors"].append({"step": "proposeAction", "error": str(e)})
            state["proposed_action"] = "manual_review"
        
        state["step_index"] += 1
        return state
    
    async def _fetch_profile(self, customer_id: str) -> Dict[str, Any]:
        """Fetch customer profile from database."""
        # TODO: Implement actual DB query
        await asyncio.sleep(0.1)  # Simulate DB call
        
        return {
            "customer_id": customer_id,
            "account_status": "active",
            "card_status": "active",
            "identity_verified": True,
            "kyc_status": "approved",
            "account_age_days": 365,
            "chargeback_count": 0,
            "dispute_count": 1,
            "daily_transaction_count": 3,
            "daily_transaction_amount": 250.0,
            "single_transaction_limit": 5000,
            "is_frozen": False
        }
    
    async def _fetch_transactions(self, customer_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent transactions from database."""
        # TODO: Implement actual DB query
        await asyncio.sleep(0.1)  # Simulate DB call
        
        # Return mock transactions
        return [
            {
                "id": f"tx_{i}",
                "customer_id": customer_id,
                "amount": 100.0 + (i * 10),
                "merchant_name": f"Merchant {i}",
                "category": "shopping",
                "mcc": "5411",
                "timestamp": datetime.utcnow().isoformat(),
                "is_international": False,
                "device_id": "device_123"
            }
            for i in range(limit)
        ]
    
    def orchestrate_sync(self, *args, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for orchestrate."""
        return asyncio.run(self.orchestrate(*args, **kwargs))
