"""Service for managing knowledge base articles and policies."""
from typing import List, Optional
from sqlalchemy.orm import Session
# Use package-relative imports to reference model modules within the app package
from ..models.policy import Policy, KnowledgeArticle

class KnowledgeService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a policy by ID."""
        return self.db.query(Policy).filter(Policy.id == policy_id).first()
    
    def list_policies(self) -> List[Policy]:
        """List all policies."""
        return self.db.query(Policy).all()
    
    def create_policy(self, name: str, rule_json: dict) -> Policy:
        """Create a new policy."""
        policy = Policy(
            name=name,
            rule_json=rule_json
        )
        self.db.add(policy)
        self.db.commit()
        return policy
    
    def update_policy(self, policy_id: str, name: str, rule_json: dict) -> Policy:
        """Update an existing policy."""
        policy = self.get_policy(policy_id)
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
            
        policy.name = name
        policy.rule_json = rule_json
        self.db.commit()
        return policy
    
    def get_article(self, article_id: str) -> Optional[KnowledgeArticle]:
        """Get a knowledge article by ID."""
        return self.db.query(KnowledgeArticle)\
                     .filter(KnowledgeArticle.id == article_id)\
                     .first()
    
    def list_articles(self) -> List[KnowledgeArticle]:
        """List all knowledge articles."""
        return self.db.query(KnowledgeArticle).all()
    
    def create_article(self, title: str, content: str) -> KnowledgeArticle:
        """Create a new knowledge article."""
        article = KnowledgeArticle(
            title=title,
            content=content
        )
        self.db.add(article)
        self.db.commit()
        return article
    
    def update_article(self, article_id: str, title: str, content: str) -> KnowledgeArticle:
        """Update an existing knowledge article."""
        article = self.get_article(article_id)
        if not article:
            raise ValueError(f"Article {article_id} not found")
            
        article.title = title
        article.content = content
        self.db.commit()
        return article