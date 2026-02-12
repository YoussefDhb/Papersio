"""
Vector Embeddings and Semantic Search
Uses sentence-transformers and ChromaDB for semantic similarity
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import os
from pathlib import Path
from dotenv import load_dotenv

try:
    from transformers import logging as transformers_logging
except Exception:
    transformers_logging = None

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
if hf_token:
    os.environ.setdefault("HF_TOKEN", hf_token)
    os.environ.setdefault("HUGGINGFACE_HUB_TOKEN", hf_token)

if transformers_logging:
    transformers_logging.set_verbosity_error()

_embedding_model = None


def get_embedding_model():
    """Get or create the embedding model (singleton pattern)"""
    global _embedding_model
    if _embedding_model is None:
        print("Loading embedding model (all-MiniLM-L6-v2)...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded!")
    return _embedding_model


CHROMA_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

chroma_client = chromadb.PersistentClient(
    path=CHROMA_DB_PATH,
    settings=Settings(anonymized_telemetry=False)
)

QUERIES_COLLECTION = "research_queries"
RESULTS_COLLECTION = "research_results"
PAPERS_COLLECTION = "paper_contents"


def get_or_create_collection(name: str):
    """Get or create a ChromaDB collection"""
    return chroma_client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity
    )


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for text
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats (embedding vector)
    """
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def add_query_to_index(query_id: int, query_text: str) -> str:
    """
    Add a research query to the vector index
    
    Args:
        query_id: Database ID of the query
        query_text: The query text
        
    Returns:
        Embedding ID
    """
    collection = get_or_create_collection(QUERIES_COLLECTION)
    
    embedding = generate_embedding(query_text)
    
    embedding_id = f"query_{query_id}"
    
    collection.add(
        embeddings=[embedding],
        documents=[query_text],
        ids=[embedding_id],
        metadatas=[{"query_id": query_id}]
    )
    
    return embedding_id


def add_result_to_index(result_id: int, answer_text: str, query_text: str) -> str:
    """
    Add a research result to the vector index
    
    Args:
        result_id: Database ID of the result
        answer_text: The answer/report text
        query_text: Original query for context
        
    Returns:
        Embedding ID
    """
    collection = get_or_create_collection(RESULTS_COLLECTION)
    
    combined_text = f"Query: {query_text}\n\nAnswer: {answer_text[:1000]}"  # First 1000 chars
    
    embedding = generate_embedding(combined_text)
    
    embedding_id = f"result_{result_id}"
    
    collection.add(
        embeddings=[embedding],
        documents=[combined_text],
        ids=[embedding_id],
        metadatas=[{"result_id": result_id}]
    )
    
    return embedding_id


def add_paper_to_index(paper_id: int, arxiv_id: str, title: str, abstract: str, full_text: Optional[str] = None) -> str:
    """
    Add a paper to the vector index
    
    Args:
        paper_id: Database ID of the paper
        arxiv_id: ArXiv ID
        title: Paper title
        abstract: Paper abstract
        full_text: Full paper text (optional, will use first 2000 chars)
        
    Returns:
        Embedding ID
    """
    collection = get_or_create_collection(PAPERS_COLLECTION)
    
    text_parts = [f"Title: {title}", f"Abstract: {abstract}"]
    if full_text:
        text_parts.append(f"Content: {full_text[:2000]}")
    
    combined_text = "\n\n".join(text_parts)
    
    embedding = generate_embedding(combined_text)
    
    embedding_id = f"paper_{arxiv_id}"
    
    collection.add(
        embeddings=[embedding],
        documents=[combined_text],
        ids=[embedding_id],
        metadatas={"paper_id": paper_id, "arxiv_id": arxiv_id}
    )
    
    return embedding_id


def search_similar_queries(query_text: str, n_results: int = 5) -> List[Dict]:
    """
    Find similar past queries using semantic search
    
    Args:
        query_text: Query to search for
        n_results: Number of results to return
        
    Returns:
        List of similar queries with metadata
    """
    try:
        collection = get_or_create_collection(QUERIES_COLLECTION)
        
        if collection.count() == 0:
            return []
        
        query_embedding = generate_embedding(query_text)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count())
        )
        
        similar_queries = []
        if results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                similar_queries.append({
                    "query_id": results['metadatas'][0][i]['query_id'],
                    "query_text": results['documents'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
        
        return similar_queries
        
    except Exception as e:
        print(f"Error searching queries: {e}")
        return []


def search_similar_papers(query_text: str, n_results: int = 5) -> List[Dict]:
    """
    Find similar papers using semantic search
    
    Args:
        query_text: Query to search for
        n_results: Number of results to return
        
    Returns:
        List of similar papers with metadata
    """
    try:
        collection = get_or_create_collection(PAPERS_COLLECTION)
        
        if collection.count() == 0:
            return []
        
        query_embedding = generate_embedding(query_text)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count())
        )
        
        similar_papers = []
        if results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                similar_papers.append({
                    "paper_id": results['metadatas'][0][i]['paper_id'],
                    "arxiv_id": results['metadatas'][0][i]['arxiv_id'],
                    "content_preview": results['documents'][0][i][:200],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
        
        return similar_papers
        
    except Exception as e:
        print(f"Error searching papers: {e}")
        return []


def get_collection_stats() -> Dict:
    """Get statistics about the vector collections"""
    queries_collection = get_or_create_collection(QUERIES_COLLECTION)
    results_collection = get_or_create_collection(RESULTS_COLLECTION)
    papers_collection = get_or_create_collection(PAPERS_COLLECTION)
    
    return {
        "queries_indexed": queries_collection.count(),
        "results_indexed": results_collection.count(),
        "papers_indexed": papers_collection.count()
    }
