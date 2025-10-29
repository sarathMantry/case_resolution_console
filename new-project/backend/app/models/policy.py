"""Policy and knowledge base models."""
from sqlalchemy import Column, String, DateTime, JSON, Text, func
from .base import Base

class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    rule_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"
    
    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())