"""
Knowledge Base Agent: Retrieves cited answers from local JSON knowledge base.
"""

import time
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..utils.logger import setup_logging, log_service_call

logger = setup_logging("kb_agent")


class KBAgent:
    """
    Retrieves relevant information from knowledge base with citations.
    Supports keyword search and contextual matching.
    """
    
    def __init__(self, kb_path: Optional[str] = None):
        self.timeout = 5  # seconds
        self.kb_path = kb_path or self._get_default_kb_path()
        self.knowledge_base = self._load_knowledge_base()
    
    def _get_default_kb_path(self) -> str:
        """Get default knowledge base path."""
        return str(Path(__file__).parent.parent / "data" / "knowledge_base.json")
    
    def _load_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load knowledge base from JSON file."""
        try:
            kb_path = Path(self.kb_path)
            if kb_path.exists():
                with open(kb_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Knowledge base not found at {self.kb_path}, using default entries")
                return self._get_default_kb()
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return self._get_default_kb()
    
    def _get_default_kb(self) -> List[Dict[str, Any]]:
        """Return default knowledge base entries."""
        return [
            {
                "id": "kb001",
                "title": "High Velocity Transactions",
                "category": "fraud_detection",
                "content": "Multiple transactions within a short time period (5+ in 1 hour) indicates potential card testing or account takeover.",
                "tags": ["velocity", "fraud", "card_testing"],
                "anchor": "#velocity-fraud",
                "relevance_score": 0.95
            },
            {
                "id": "kb002",
                "title": "Device Fingerprint Changes",
                "category": "fraud_detection",
                "content": "Sudden changes in device fingerprints, especially multiple devices in short succession, suggest compromised credentials.",
                "tags": ["device", "account_takeover", "fraud"],
                "anchor": "#device-fraud",
                "relevance_score": 0.90
            },
            {
                "id": "kb003",
                "title": "MCC Risk Categories",
                "category": "merchant_categories",
                "content": "High-risk MCCs include 5967 (teleservices), 7995 (gambling), 5966 (outbound marketing). These require additional scrutiny.",
                "tags": ["mcc", "risk", "categories"],
                "anchor": "#mcc-risk",
                "relevance_score": 0.85
            },
            {
                "id": "kb004",
                "title": "Chargeback Patterns",
                "category": "disputes",
                "content": "Customers with 2+ chargebacks in 6 months have 60% probability of future disputes. Enhanced monitoring recommended.",
                "tags": ["chargeback", "dispute", "patterns"],
                "anchor": "#chargeback-patterns",
                "relevance_score": 0.88
            },
            {
                "id": "kb005",
                "title": "International Transaction Flags",
                "category": "fraud_detection",
                "content": "International transactions, especially to high-risk countries, require verification. Impossible travel detection is key.",
                "tags": ["international", "travel", "location"],
                "anchor": "#international-fraud",
                "relevance_score": 0.82
            },
            {
                "id": "kb006",
                "title": "Card Freeze Guidelines",
                "category": "actions",
                "content": "Freeze card immediately for risk scores >80, open dispute for 60-80, contact customer for 40-60.",
                "tags": ["freeze", "action", "response"],
                "anchor": "#freeze-guidelines",
                "relevance_score": 0.90
            },
            {
                "id": "kb007",
                "title": "False Positive Indicators",
                "category": "fraud_detection",
                "content": "Travel bookings, large purchases at known merchants, and recurring subscriptions often trigger false positives.",
                "tags": ["false_positive", "legitimate", "patterns"],
                "anchor": "#false-positives",
                "relevance_score": 0.75
            },
            {
                "id": "kb008",
                "title": "OTP Verification Requirements",
                "category": "compliance",
                "content": "Transactions >$500 or international transactions require OTP verification per PSD2/SCA requirements.",
                "tags": ["otp", "verification", "compliance"],
                "anchor": "#otp-requirements",
                "relevance_score": 0.92
            }
        ]
    
    @log_service_call(logger)
    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Search knowledge base for relevant entries.
        
        Args:
            query: Search query (keywords or context)
            max_results: Maximum number of results to return
            
        Returns:
            Search results with citations
        """
        start_time = time.time()
        
        try:
            # Normalize query
            query_lower = query.lower()
            query_words = set(query_lower.split())
            
            # Score each KB entry
            scored_entries = []
            for entry in self.knowledge_base:
                score = self._calculate_relevance(entry, query_lower, query_words)
                if score > 0:
                    scored_entries.append((score, entry))
            
            # Sort by score and take top results
            scored_entries.sort(reverse=True, key=lambda x: x[0])
            top_entries = scored_entries[:max_results]
            
            results = [
                {
                    "id": entry["id"],
                    "title": entry["title"],
                    "category": entry["category"],
                    "content": entry["content"],
                    "anchor": entry["anchor"],
                    "relevance_score": score,
                    "tags": entry.get("tags", [])
                }
                for score, entry in top_entries
            ]
            
            logger.info(f"KB search for '{query}' returned {len(results)} results")
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "result_count": len(results),
                "duration": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Error in KB search: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    def _calculate_relevance(self, entry: Dict[str, Any], query: str, query_words: set) -> float:
        """Calculate relevance score for a KB entry."""
        score = 0.0
        
        # Check title match
        title_lower = entry["title"].lower()
        if query in title_lower:
            score += 10.0
        
        # Check content match
        content_lower = entry["content"].lower()
        if query in content_lower:
            score += 5.0
        
        # Check tag matches
        tags = entry.get("tags", [])
        tag_matches = sum(1 for tag in tags if tag.lower() in query_words)
        score += tag_matches * 3.0
        
        # Check word overlap
        entry_words = set(title_lower.split() + content_lower.split())
        word_overlap = len(query_words & entry_words)
        score += word_overlap * 1.0
        
        # Apply base relevance
        score *= entry.get("relevance_score", 1.0)
        
        return score
    
    @log_service_call(logger)
    def get_by_category(self, category: str) -> Dict[str, Any]:
        """
        Get all KB entries for a specific category.
        
        Args:
            category: Category name
            
        Returns:
            All entries in the category
        """
        start_time = time.time()
        
        try:
            results = [
                entry for entry in self.knowledge_base 
                if entry.get("category") == category
            ]
            
            return {
                "success": True,
                "category": category,
                "results": results,
                "result_count": len(results),
                "duration": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Error getting KB category: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    @log_service_call(logger)
    def get_by_tags(self, tags: List[str]) -> Dict[str, Any]:
        """
        Get KB entries matching any of the provided tags.
        
        Args:
            tags: List of tags to search for
            
        Returns:
            Matching entries
        """
        start_time = time.time()
        
        try:
            tags_lower = [tag.lower() for tag in tags]
            results = []
            
            for entry in self.knowledge_base:
                entry_tags = [tag.lower() for tag in entry.get("tags", [])]
                if any(tag in entry_tags for tag in tags_lower):
                    results.append(entry)
            
            return {
                "success": True,
                "tags": tags,
                "results": results,
                "result_count": len(results),
                "duration": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Error getting KB by tags: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
