"""
Google Gemini AI integration for enhanced fraud detection reasoning.
"""

import os
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI

from .logger import setup_logging

logger = setup_logging("gemini_llm")

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "2048"))

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info(f"✅ Gemini AI configured with model: {GEMINI_MODEL}")
else:
    logger.warning("⚠️ GOOGLE_API_KEY not set - LLM features will be disabled")


class GeminiLLM:
    """
    Wrapper for Google Gemini AI model integration.
    """
    
    def __init__(self):
        self.api_key = GOOGLE_API_KEY
        self.model_name = GEMINI_MODEL
        self.temperature = GEMINI_TEMPERATURE
        self.max_tokens = GEMINI_MAX_TOKENS
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            # Initialize LangChain Gemini
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Initialize direct Gemini client
            self.model = genai.GenerativeModel(self.model_name)
            logger.info("Gemini LLM initialized successfully")
        else:
            self.llm = None
            self.model = None
            logger.warning("Gemini LLM not initialized - API key missing")
    
    def generate_fraud_reasoning(
        self,
        fraud_signals: Dict[str, Any],
        transaction_data: Dict[str, Any],
        customer_profile: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate human-readable fraud reasoning using Gemini.
        
        Args:
            fraud_signals: Detected fraud signals and scores
            transaction_data: Transaction details
            customer_profile: Customer profile information
            
        Returns:
            Natural language explanation of fraud analysis
        """
        if not self.enabled:
            return None
        
        try:
            prompt = f"""You are a fraud detection expert analyzing a potentially fraudulent transaction.

FRAUD SIGNALS:
{self._format_signals(fraud_signals)}

TRANSACTION DETAILS:
- Amount: ${transaction_data.get('amount', 0):.2f}
- Merchant: {transaction_data.get('merchant_name', 'Unknown')}
- Category: {transaction_data.get('category', 'Unknown')}
- Location: {transaction_data.get('merchant_city', 'Unknown')}, {transaction_data.get('merchant_country', 'Unknown')}
- Time: {transaction_data.get('timestamp', 'Unknown')}

CUSTOMER PROFILE:
- Account Age: {customer_profile.get('account_age_days', 0)} days
- Previous Chargebacks: {customer_profile.get('chargeback_count', 0)}
- Previous Disputes: {customer_profile.get('dispute_count', 0)}
- Account Status: {customer_profile.get('account_status', 'Unknown')}

Provide a concise 2-3 sentence explanation of why this transaction is flagged as potentially fraudulent. Focus on the most significant risk factors."""

            response = self.model.generate_content(prompt)
            reasoning = response.text.strip()
            
            logger.info("Generated fraud reasoning via Gemini")
            return reasoning
            
        except Exception as e:
            logger.error(f"Error generating fraud reasoning: {e}")
            return None
    
    def generate_insights_summary(
        self,
        insights_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate a natural language summary of transaction insights.
        
        Args:
            insights_data: Transaction pattern analysis
            
        Returns:
            Human-readable insights summary
        """
        if not self.enabled:
            return None
        
        try:
            prompt = f"""Summarize the following transaction pattern analysis in 2-3 clear sentences:

TRANSACTION PATTERNS:
- Total Transactions: {insights_data.get('transaction_count', 0)}
- Spending Patterns: {insights_data.get('spending_patterns', {})}
- Anomalies Detected: {len(insights_data.get('anomalies', []))}
- Top Categories: {insights_data.get('categories', {}).get('top_categories', [])}
- Merchant Concentration: {insights_data.get('merchants', {}).get('merchant_concentration', 0):.2%}

Key Anomalies:
{self._format_anomalies(insights_data.get('anomalies', []))}

Provide a clear summary highlighting the most important patterns and concerns."""

            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            
            logger.info("Generated insights summary via Gemini")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating insights summary: {e}")
            return None
    
    def generate_action_recommendation(
        self,
        risk_score: float,
        fraud_reasons: List[str],
        compliance_status: Dict[str, Any],
        kb_citations: List[Dict[str, Any]]
    ) -> Optional[Dict[str, str]]:
        """
        Generate action recommendation with detailed reasoning.
        
        Args:
            risk_score: Calculated risk score
            fraud_reasons: List of fraud detection reasons
            compliance_status: Compliance check results
            kb_citations: Relevant knowledge base articles
            
        Returns:
            Dictionary with recommended action and reasoning
        """
        if not self.enabled:
            return None
        
        try:
            kb_context = "\n".join([
                f"- {cite['title']}: {cite.get('content', 'N/A')[:100]}..."
                for cite in kb_citations[:3]
            ])
            
            prompt = f"""You are a fraud prevention specialist. Based on the analysis below, recommend the best course of action.

RISK SCORE: {risk_score}/100

FRAUD INDICATORS:
{self._format_list(fraud_reasons)}

COMPLIANCE STATUS: {compliance_status.get('compliance_status', 'unknown')}
Violations: {len(compliance_status.get('violations', []))}
Requirements: {compliance_status.get('requirements', [])}

KNOWLEDGE BASE GUIDANCE:
{kb_context}

Recommend ONE of these actions:
1. freeze_card - Immediately block the card
2. open_dispute - Create a dispute case for review
3. contact_customer - Reach out for verification
4. mark_false_positive - Approve as legitimate
5. manual_review - Escalate to human analyst

Provide your recommendation and 2-3 sentences explaining why this is the most appropriate action."""

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Parse action from response
            action = self._extract_action(result_text)
            
            logger.info(f"Generated action recommendation: {action}")
            return {
                "action": action,
                "reasoning": result_text
            }
            
        except Exception as e:
            logger.error(f"Error generating action recommendation: {e}")
            return None
    
    def enhance_alert_description(
        self,
        alert_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate a clear, actionable alert description.
        
        Args:
            alert_data: Alert information
            
        Returns:
            Enhanced alert description
        """
        if not self.enabled:
            return None
        
        try:
            prompt = f"""Create a clear, professional alert description for a fraud analyst:

ALERT TYPE: {alert_data.get('risk_level', 'unknown').upper()} RISK
Risk Score: {alert_data.get('risk_score', 0)}/100
Customer: {alert_data.get('customer_id', 'Unknown')}

DETECTED ISSUES:
{self._format_list(alert_data.get('reasons', []))}

Proposed Action: {alert_data.get('proposed_action', 'Unknown')}

Write a concise 2-3 sentence alert description that:
1. States the primary concern
2. Highlights the most critical risk factor
3. Suggests immediate action needed

Use professional, clear language suitable for a fraud analyst dashboard."""

            response = self.model.generate_content(prompt)
            description = response.text.strip()
            
            logger.info("Generated alert description via Gemini")
            return description
            
        except Exception as e:
            logger.error(f"Error generating alert description: {e}")
            return None
    
    def _format_signals(self, signals: Dict[str, Any]) -> str:
        """Format fraud signals for prompt."""
        if not signals:
            return "No signals detected"
        
        signal_scores = signals.get('signal_scores', {})
        reasons = signals.get('reasons', [])
        
        lines = []
        for signal, score in signal_scores.items():
            lines.append(f"- {signal.replace('_', ' ').title()}: {score}/100")
        
        if reasons:
            lines.append("\nKey Reasons:")
            for reason in reasons[:5]:
                lines.append(f"  • {reason}")
        
        return "\n".join(lines)
    
    def _format_anomalies(self, anomalies: List[Dict[str, Any]]) -> str:
        """Format anomalies for prompt."""
        if not anomalies:
            return "None detected"
        
        lines = []
        for i, anomaly in enumerate(anomalies[:3], 1):
            reasons = anomaly.get('reasons', [])
            lines.append(f"{i}. {', '.join(reasons)}")
        
        return "\n".join(lines)
    
    def _format_list(self, items: List[str]) -> str:
        """Format list items for prompt."""
        if not items:
            return "None"
        return "\n".join([f"- {item}" for item in items[:10]])
    
    def _extract_action(self, text: str) -> str:
        """Extract action from LLM response."""
        text_lower = text.lower()
        
        actions = [
            "freeze_card",
            "open_dispute",
            "contact_customer",
            "mark_false_positive",
            "manual_review"
        ]
        
        for action in actions:
            if action.replace('_', ' ') in text_lower or action in text_lower:
                return action
        
        # Default to manual review if unclear
        return "manual_review"


# Global LLM instance
_llm_instance = None


def get_gemini_llm() -> GeminiLLM:
    """Get the global Gemini LLM instance."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = GeminiLLM()
    return _llm_instance
