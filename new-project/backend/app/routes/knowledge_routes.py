"""API routes for knowledge base and policy management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from ..services.knowledge_service import KnowledgeService
from ..utils.database import get_db
from ..models.policy import Policy, KnowledgeArticle

router = APIRouter(prefix="/knowledge")

# Policy routes
@router.get("/policies/{policy_id}", response_model=None)
def get_policy(policy_id: str, db: Session = Depends(get_db)):
    knowledge_service = KnowledgeService(db)
    policy = knowledge_service.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy

@router.get("/policies", response_model=None)
def list_policies(db: Session = Depends(get_db)):
    knowledge_service = KnowledgeService(db)
    return knowledge_service.list_policies()

@router.post("/policies", response_model=None)
def create_policy(name: str, rule_json: Dict, db: Session = Depends(get_db)):
    knowledge_service = KnowledgeService(db)
    return knowledge_service.create_policy(name=name, rule_json=rule_json)

@router.put("/policies/{policy_id}", response_model=None)
def update_policy(
    policy_id: str,
    name: str,
    rule_json: Dict,
    db: Session = Depends(get_db)
):
    knowledge_service = KnowledgeService(db)
    try:
        return knowledge_service.update_policy(
            policy_id=policy_id,
            name=name,
            rule_json=rule_json
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Knowledge article routes
@router.get("/articles/{article_id}", response_model=None)
def get_article(article_id: str, db: Session = Depends(get_db)):
    knowledge_service = KnowledgeService(db)
    article = knowledge_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.get("/articles", response_model=None)
def list_articles(db: Session = Depends(get_db)):
    knowledge_service = KnowledgeService(db)
    return knowledge_service.list_articles()

@router.post("/articles", response_model=None)
def create_article(title: str, content: str, db: Session = Depends(get_db)):
    knowledge_service = KnowledgeService(db)
    return knowledge_service.create_article(title=title, content=content)

@router.put("/articles/{article_id}", response_model=None)
def update_article(
    article_id: str,
    title: str,
    content: str,
    db: Session = Depends(get_db)
):
    knowledge_service = KnowledgeService(db)
    try:
        return knowledge_service.update_article(
            article_id=article_id,
            title=title,
            content=content
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))