"""
Research Memory Service
Manages storage and retrieval of research queries, results, and papers
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from models.research import ResearchQuery, ResearchResult, PaperContent
from tools.embeddings import (
    add_query_to_index,
    add_result_to_index,
    add_paper_to_index,
    search_similar_queries,
    search_similar_papers,
)
from tools.pdf_extractor import extract_paper_content
from database import get_db_session
import time


def save_research(
    query_text: str,
    mode: str,
    answer: str,
    sources: List[Dict],
    workflow_stages: Optional[List[Dict]] = None,
    quality_score: Optional[int] = None,
    processing_time: Optional[float] = None,
) -> Dict:
    """
    Save a research query and its results

    Args:
        query_text: The research question
        mode: Research mode used (simple, workflow, langgraph)
        answer: AI-generated answer
        sources: List of sources used
        workflow_stages: Workflow stages completed (if applicable)
        quality_score: Quality score from critic (if applicable)
        processing_time: Time taken in seconds

    Returns:
        Dict with query_id and result_id
    """
    db = get_db_session()

    try:
        query = ResearchQuery(query_text=query_text, mode=mode)
        db.add(query)
        db.flush()  # Get the ID

        query.embedding_id = add_query_to_index(query.id, query_text)

        result = ResearchResult(
            query_id=query.id,
            answer=answer,
            sources=sources,
            workflow_stages=workflow_stages,
            quality_score=quality_score,
            processing_time=processing_time,
        )
        db.add(result)
        db.flush()

        result.embedding_id = add_result_to_index(result.id, answer, query_text)

        db.commit()

        print(f"💾 Saved research: query_id={query.id}, result_id={result.id}")

        return {"success": True, "query_id": query.id, "result_id": result.id}

    except Exception as e:
        db.rollback()
        print(f"Error saving research: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_research_context(query_text: str, n_similar: int = 3) -> Dict:
    """
    Get relevant context from past research for a new query

    Args:
        query_text: New research question
        n_similar: Number of similar past queries to retrieve

    Returns:
        Dict with similar queries and their results
    """
    db = get_db_session()

    try:
        similar_queries = search_similar_queries(query_text, n_results=n_similar)

        if not similar_queries:
            return {"has_context": False, "similar_queries": [], "message": "No similar past research found"}

        context_items = []
        for sq in similar_queries:
            query = db.query(ResearchQuery).filter_by(id=sq["query_id"]).first()
            if query and query.results:
                result = query.results[0]  # Get most recent result
                context_items.append(
                    {
                        "past_query": query.query_text,
                        "past_answer": result.answer[:500],  # First 500 chars
                        "similarity": 1 - sq["distance"] if sq["distance"] else None,
                        "date": query.created_at.strftime("%Y-%m-%d"),
                    }
                )

        return {
            "has_context": len(context_items) > 0,
            "similar_queries": context_items,
            "message": f"Found {len(context_items)} similar past research(es)",
        }

    except Exception as e:
        print(f"Error getting research context: {e}")
        return {"has_context": False, "similar_queries": [], "error": str(e)}
    finally:
        db.close()


def save_paper_content(
    arxiv_id: str,
    title: str,
    authors: List[str],
    abstract: str,
    pdf_url: str,
    published_date: str,
    extract_full_content: bool = True,
) -> Dict:
    """
    Save paper metadata and optionally extract full content from PDF

    Args:
        arxiv_id: ArXiv paper ID
        title: Paper title
        authors: List of authors
        abstract: Paper abstract
        pdf_url: URL to PDF
        published_date: Publication date
        extract_full_content: Whether to download and extract PDF

    Returns:
        Dict with paper_id and extraction status
    """
    db = get_db_session()

    try:
        existing = db.query(PaperContent).filter_by(arxiv_id=arxiv_id).first()
        if existing:
            print(f"Paper {arxiv_id} already in database")
            return {"success": True, "paper_id": existing.id, "already_exists": True}

        paper = PaperContent(
            arxiv_id=arxiv_id,
            title=title,
            authors=authors,
            abstract=abstract,
            pdf_url=pdf_url,
            published_date=published_date,
            extraction_status="pending",
        )

        if extract_full_content:
            print(f"Extracting full content for {arxiv_id}...")
            extraction = extract_paper_content(pdf_url, max_pages=50)

            if extraction["success"]:
                paper.full_text = extraction["full_text"]
                paper.tables = extraction["tables"]
                paper.num_pages = extraction["num_pages"]
                paper.extraction_status = "success"
                print(f"Extracted {extraction['num_pages']} pages, {extraction['num_tables']} tables")
            else:
                paper.extraction_status = "failed"
                print(f"Extraction failed: {extraction.get('error')}")

        db.add(paper)
        db.flush()

        paper.embedding_id = add_paper_to_index(paper.id, arxiv_id, title, abstract, paper.full_text)

        db.commit()

        return {"success": True, "paper_id": paper.id, "extraction_status": paper.extraction_status}

    except Exception as e:
        db.rollback()
        print(f"Error saving paper: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_paper_content(arxiv_id: str) -> Optional[Dict]:
    """
    Retrieve full paper content from database

    Args:
        arxiv_id: ArXiv paper ID

    Returns:
        Dict with paper content or None if not found
    """
    db = get_db_session()

    try:
        paper = db.query(PaperContent).filter_by(arxiv_id=arxiv_id).first()

        if not paper:
            return None

        return {
            "arxiv_id": paper.arxiv_id,
            "title": paper.title,
            "authors": paper.authors,
            "abstract": paper.abstract,
            "full_text": paper.full_text,
            "tables": paper.tables,
            "num_pages": paper.num_pages,
            "extraction_status": paper.extraction_status,
        }

    finally:
        db.close()


def get_research_stats() -> Dict:
    """Get statistics about stored research"""
    db = get_db_session()

    try:
        num_queries = db.query(ResearchQuery).count()
        num_results = db.query(ResearchResult).count()
        num_papers = db.query(PaperContent).count()
        num_papers_extracted = db.query(PaperContent).filter_by(extraction_status="success").count()

        return {
            "total_queries": num_queries,
            "total_results": num_results,
            "total_papers": num_papers,
            "papers_with_full_text": num_papers_extracted,
        }

    finally:
        db.close()
