"""
Database models for storing research queries, results, and paper content
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class ResearchQuery(Base):
    """Store user research queries and metadata"""
    __tablename__ = "research_queries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    mode = Column(String(50), nullable=False)  # simple, workflow, langgraph
    created_at = Column(DateTime, default=datetime.utcnow)
    
    embedding_id = Column(String(100))  # ChromaDB ID
    
    results = relationship("ResearchResult", back_populates="query", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ResearchQuery(id={self.id}, query='{self.query_text[:50]}...')>"


class ResearchResult(Base):
    """Store the AI-generated research results"""
    __tablename__ = "research_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(Integer, ForeignKey("research_queries.id"), nullable=False)
    
    answer = Column(Text, nullable=False)
    sources = Column(JSON)  # List of sources used
    
    workflow_stages = Column(JSON)  # Stages completed
    quality_score = Column(Integer)  # Critique score if available
    
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time = Column(Float)  # Seconds taken
    
    embedding_id = Column(String(100))  # ChromaDB ID
    
    query = relationship("ResearchQuery", back_populates="results")
    
    def __repr__(self):
        return f"<ResearchResult(id={self.id}, query_id={self.query_id})>"


class PaperContent(Base):
    """Store full content extracted from ArXiv papers"""
    __tablename__ = "paper_contents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    arxiv_id = Column(String(50), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    authors = Column(JSON)  # List of author names
    published_date = Column(String(20))
    
    abstract = Column(Text)
    full_text = Column(Text)  # Extracted text from PDF
    tables = Column(JSON)  # Extracted tables
    
    pdf_url = Column(String(500))
    num_pages = Column(Integer)
    extraction_status = Column(String(20))  # success, failed, pending
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    embedding_id = Column(String(100))  # ChromaDB ID
    
    def __repr__(self):
        return f"<PaperContent(arxiv_id='{self.arxiv_id}', title='{self.title[:50]}...')>"
