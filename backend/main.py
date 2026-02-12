"""Papersio - FastAPI Backend with Multi-Source Search (Gemini)."""

import os
import time
from typing import List, Dict, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import json
from connection_manager import manager

from llm import ModelFactory

from tools.search_router import search_all
from tools.research_memory import (
    save_research,
    get_research_context,
    save_paper_content,
    get_research_stats
)
from tools.arxiv_search import search_arxiv
from tools.pdf_generator import generate_research_pdf
from thread_executor import run_in_thread

from agents.planner import PlannerAgent
from agents.analyst import AnalystAgent
from agents.writer import WriterAgent
from agents.critic import CriticAgent
from agents.workflow import ResearchWorkflow
from agents.langgraph_workflow import LangGraphResearchWorkflow
from agents.ultra_workflow import UltraResearchWorkflow

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI(
    title="Papersio API",
    description="AI research assistant for papers and web sources powered by Google Gemini",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


try:
    llm_provider = ModelFactory.create()
    print(f"Using LLM: {llm_provider.get_model_name()}")
except Exception as e:
    print(f"Error initializing LLM provider: {e}")
    print("Falling back to Gemini Flash")
    llm_provider = ModelFactory.create(provider='gemini', model='gemini-2.5-flash')

planner = PlannerAgent(llm_provider)
analyst = AnalystAgent(llm_provider)
writer = WriterAgent(llm_provider)
critic = CriticAgent(llm_provider)

workflow = ResearchWorkflow(planner, analyst, writer, critic)



class ResearchRequest(BaseModel):
    query: str  
    use_search: bool = True 
    use_planning: bool = True 


class Source(BaseModel):
    title: str
    url: str
    source_type: str  
    authors: Optional[List[str]] = None  


class SubQuestionResult(BaseModel):
    question: str
    answer: str
    sources: List[Source] = []

class ResearchResponse(BaseModel):
    query: str
    answer: str
    sources: List[Source] = []
    search_strategy: Optional[str] = None
    plan: Optional[Dict] = None 
    sub_results: Optional[List[SubQuestionResult]] = None 


@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "message": "Papersio API is running!",
        "status": "ok",
        "version": "0.1.0"
    }


async def research_single_question(query: str, use_search: bool = True) -> Dict:
    """Research a single question and return results"""
    sources = []
    search_context = ""
    search_strategy = None
    
    if use_search:
        search_results = search_all(query, max_results_per_source=3)
        search_strategy = search_results["strategy"]["reason"]
        search_context = search_results["combined_context"]
        
        for paper in search_results["arxiv_results"]:
            sources.append(Source(
                title=paper["title"],
                url=paper["arxiv_url"],
                source_type="arxiv",
                authors=paper["authors"]
            ))
        
        for article in search_results["web_results"]:
            sources.append(Source(
                title=article["title"],
                url=article["url"],
                source_type="web"
            ))
    
    if search_context:
        prompt = f"""You are an expert AI research assistant. Please answer the following question:

QUESTION: {query}

SOURCES:
{search_context}

Based on the above sources, provide a clear, concise answer that:
1. Directly answers the question
2. Synthesizes information from sources
3. Cites sources using [1], [2], [3] etc.
4. Is well-structured and informative

Your answer:"""
    else:
        prompt = f"""You are an AI research assistant. Please answer: {query}

Provide a clear, concise, and informative answer."""
    
    answer = llm_provider.generate(prompt)
    
    return {
        "answer": answer,
        "sources": sources,
        "search_strategy": search_strategy
    }


@app.post("/api/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """
    Research endpoint - takes a query and returns AI-generated answer
    Now with question decomposition and multi-source search!
    
    Example:
        POST /api/research
        Body: {"query": "Compare Python and JavaScript", "use_search": true, "use_planning": true}
    """
    try:
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        plan = None
        sub_results = []
        all_sources = []
        
        if request.use_planning:
            plan = planner.create_research_plan(request.query)
            
            if plan.get("needs_breakdown") and plan.get("sub_questions"):
                for sub_q in plan["sub_questions"]:
                    sub_result = await research_single_question(sub_q, request.use_search)
                    
                    sub_results.append(SubQuestionResult(
                        question=sub_q,
                        answer=sub_result["answer"],
                        sources=sub_result["sources"]
                    ))
                    
                    all_sources.extend(sub_result["sources"])
                
                sub_qa_text = "\n\n".join([
                    f"Q: {sr.question}\nA: {sr.answer}" 
                    for sr in sub_results
                ])
                
                synthesis_prompt = f"""You are an expert research synthesizer. You've researched several sub-questions about a topic.

MAIN QUESTION: {request.query}

SUB-QUESTIONS AND ANSWERS:
{sub_qa_text}

Now synthesize all this information into a single, comprehensive, well-structured answer to the main question.

Requirements:
1. Create a cohesive narrative (not just listing sub-answers)
2. Organize information logically
3. Include all important points from sub-answers
4. Maintain citations [1], [2], [3] etc.
5. Write in a clear, professional tone

Your comprehensive research report:"""
                
                final_answer = llm_provider.generate(synthesis_prompt)
                
                return ResearchResponse(
                    query=request.query,
                    answer=final_answer,
                    sources=all_sources,
                    plan=plan,
                    sub_results=sub_results,
                    search_strategy="Multi-step research with question decomposition"
                )
        
        result = await research_single_question(request.query, request.use_search)
        
        return ResearchResponse(
            query=request.query,
            answer=result["answer"],
            sources=result["sources"],
            search_strategy=result["search_strategy"],
            plan=plan if plan else None
        )
    
    except Exception as e:
        error_msg = str(e)
        
        if "429" in error_msg or "quota" in error_msg.lower():
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Please wait a minute and try again. Consider using simpler questions or the basic endpoint (/api/research) which uses fewer API calls. Error: {error_msg}"
            )
        
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating response: {error_msg}"
        )


@app.post("/api/research/workflow")
async def research_workflow(request: ResearchRequest):
    """
    Advanced research endpoint using full workflow:
    Plan → Search → Analyze → Write → Critique
    
    Example:
        POST /api/research/workflow
        Body: {"query": "Compare Python and JavaScript", "use_search": true}
    """
    try:
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        async def search_function(query: str):
            """Search function that workflow will use"""
            if not request.use_search:
                return {"sources": [], "context": ""}
            
            search_results = search_all(query, max_results_per_source=3)
            sources = []
            
            for paper in search_results["arxiv_results"]:
                sources.append(Source(
                    title=paper["title"],
                    url=paper["arxiv_url"],
                    source_type="arxiv",
                    authors=paper["authors"]
                ))
            
            for article in search_results["web_results"]:
                sources.append(Source(
                    title=article["title"],
                    url=article["url"],
                    source_type="web"
                ))
            
            return {
                "sources": sources,
                "context": search_results["combined_context"]
            }
        
        result = await workflow.execute_research(
            request.query,
            search_function,
            use_critique=True
        )
        
        return {
            "query": request.query,
            "answer": result["final_report"],
            "sources": result["sources"],
            "workflow_stages": result["workflow_stages"],
            "quality_assessment": result.get("quality_assessment"),
            "search_strategy": "Multi-stage workflow: Plan → Search → Analyze → Write → Critique"
        }
    
    except Exception as e:
        error_msg = str(e)
        
        if "429" in error_msg or "quota" in error_msg.lower():
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. The workflow endpoint uses 5 API calls and may hit limits quickly. Try the basic endpoint (/api/research) instead, or wait a minute. Error: {error_msg}"
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error in workflow: {error_msg}"
        )


@app.post("/api/research/langgraph")
async def research_langgraph(request: ResearchRequest):
    """
    MOST ADVANCED ENDPOINT - LangGraph state machine orchestration
    
    Features:
    - Professional state management
    - Conditional workflow routing
    - Automatic revision cycles
    - Better error handling
    - Industry-standard framework
    
    Example:
        POST /api/research/langgraph
        Body: {"query": "What are the latest trends in quantum computing?", "use_search": true}
    """
    try:
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        async def search_function(query: str):
            """Search function that LangGraph workflow will use"""
            if not request.use_search:
                return {"sources": [], "context": ""}
            
            search_results = search_all(query, max_results_per_source=3)
            sources = []
            
            for paper in search_results["arxiv_results"]:
                sources.append({
                    "title": paper["title"],
                    "url": paper["arxiv_url"],
                    "source_type": "arxiv",
                    "authors": paper["authors"]
                })
            
            for article in search_results["web_results"]:
                sources.append({
                    "title": article["title"],
                    "url": article["url"],
                    "source_type": "web"
                })
            
            return {
                "sources": sources,
                "context": search_results["combined_context"]
            }
        
        langgraph_workflow = LangGraphResearchWorkflow(
            planner=planner,
            analyst=analyst,
            writer=writer,
            critic=critic,
            search_func=search_function
        )
        
        final_state = await langgraph_workflow.execute(
            query=request.query,
            use_search=request.use_search
        )
        
        formatted_sources = []
        for source in final_state.get("sources", []):
            formatted_sources.append(Source(
                title=source["title"],
                url=source["url"],
                source_type=source["source_type"],
                authors=source.get("authors")
            ))
        
        workflow_stages = []
        
        if final_state.get("plan"):
            workflow_stages.append({
                "stage": "Planning",
                "status": "complete",
                "details": final_state["plan"]
            })
        
        if final_state.get("sources"):
            workflow_stages.append({
                "stage": "Search",
                "status": "complete",
                "details": f"Found {len(final_state['sources'])} sources"
            })
        
        if final_state.get("analysis"):
            workflow_stages.append({
                "stage": "Analysis",
                "status": "complete",
                "details": {
                    "themes": len(final_state.get("themes", [])),
                    "findings": len(final_state.get("key_findings", []))
                }
            })
        
        if final_state.get("draft_report"):
            workflow_stages.append({
                "stage": "Writing",
                "status": "complete",
                "details": f"Generated report ({len(final_state['draft_report'])} chars)"
            })
        
        if final_state.get("critique"):
            workflow_stages.append({
                "stage": "Critique",
                "status": "complete",
                "details": {
                    "quality_score": final_state.get("quality_score", 0),
                    "approved": final_state.get("approved", False),
                    "revisions": final_state.get("retry_count", 0)
                }
            })
        
        return {
            "query": request.query,
            "answer": final_state.get("final_report", ""),
            "sources": formatted_sources,
            "workflow_stages": workflow_stages,
            "quality_assessment": final_state.get("critique"),
            "search_strategy": "LangGraph State Machine: Plan → Search → Analyze → Write → Critique (with conditional revision)",
            "framework": "LangGraph",
            "revisions_made": final_state.get("retry_count", 0),
            "errors": final_state.get("errors", [])
        }
    
    except Exception as e:
        error_msg = str(e)
        
        if "429" in error_msg or "quota" in error_msg.lower():
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. LangGraph workflow uses multiple API calls. Try reducing complexity or wait a minute. Error: {error_msg}"
            )
        
        if "langgraph" in error_msg.lower() or "state" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail=f"LangGraph workflow error: {error_msg}. Try the standard /api/research/workflow endpoint instead."
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error in LangGraph execution: {error_msg}"
        )


@app.post("/api/research/contextual")
async def research_contextual(request: ResearchRequest):
    """
    CONTEXTUAL RESEARCH - with Memory & Deep PDF Analysis
    
    Features:
    - Remembers past research
    - Extracts full text + tables from PDFs
    - Uses semantic search to find relevant context
    - References previous findings
    - Stores results for future queries
    
    Example:
        POST /api/research/contextual
        Body: {"query": "What are the latest advances in transformer models?", "use_search": true}
    """
    import time
    start_time = time.time()
    
    try:
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        print(f"\nContextual Research: {request.query}")
        
        print("Searching past research...")
        context = get_research_context(request.query, n_similar=3)
        
        print("Searching for new information...")
        if request.use_search:
            arxiv_results = search_arxiv(
                request.query,
                max_results=2,  # Limit to 2 papers to avoid timeout
                extract_full_content=True
            )
            
            search_results = search_all(request.query, max_results_per_source=3)
            
            sources = []
            search_context = search_results.get("combined_context", "")
            
            for paper in arxiv_results.get("results", []):
                sources.append(Source(
                    title=paper["title"],
                    url=paper["arxiv_url"],
                    source_type="arxiv",
                    authors=paper["authors"]
                ))
                
                if paper.get("full_text"):
                    search_context += f"\n\nFULL PAPER: {paper['title']}\n{paper['full_text'][:5000]}\n"
                    
                    if paper.get("tables"):
                        for table in paper["tables"][:2]:  # First 2 tables
                            search_context += f"\n{table.get('markdown', '')}\n"
            
            for article in search_results.get("web_results", []):
                sources.append(Source(
                    title=article["title"],
                    url=article["url"],
                    source_type="web"
                ))
        else:
            sources = []
            search_context = ""
        
        print("Building context-aware response...")
        
        context_prompt = f"Research Question: {request.query}\n\n"
        
        if context.get("has_context"):
            context_prompt += "PAST RESEARCH (You researched similar topics before):\n\n"
            for i, item in enumerate(context["similar_queries"], 1):
                context_prompt += f"Previous Query {i}: {item['past_query']}\n"
                context_prompt += f"Previous Finding: {item['past_answer']}\n"
                context_prompt += f"Date: {item['date']}\n\n"
            context_prompt += "Use this past research to provide continuity and reference previous findings.\n\n"
        
        if search_context:
            context_prompt += f"NEW INFORMATION:\n{search_context}\n\n"
        
        context_prompt += """
        Please provide a comprehensive research report that:
        1. References any relevant past research (if available)
        2. Incorporates the new information found
        3. Synthesizes findings from full papers (not just abstracts)
        4. Includes data from tables and detailed methodology
        5. Provides a cohesive, well-structured answer
        
        Format your response as a detailed research report with sections, citations, and clear conclusions.
        """
        
        print("Generating AI response...")
        answer = llm_provider.generate(context_prompt)
        
        processing_time = time.time() - start_time
        print(f"Saving to memory (took {processing_time:.2f}s)...")
        
        save_result = save_research(
            query_text=request.query,
            mode="contextual",
            answer=answer,
            sources=[s.dict() for s in sources],
            processing_time=processing_time
        )
        
        return {
            "query": request.query,
            "answer": answer,
            "sources": sources,
            "context_used": {
                "has_past_research": context.get("has_context", False),
                "num_similar_queries": len(context.get("similar_queries", [])),
                "similar_queries": [item["past_query"] for item in context.get("similar_queries", [])]
            },
            "search_strategy": "Contextual Research: Memory + Full PDF Analysis",
            "processing_time": processing_time,
            "saved_to_memory": save_result.get("success", False)
        }
    
    except Exception as e:
        error_msg = str(e)
        
        if "429" in error_msg or "quota" in error_msg.lower():
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Contextual mode extracts full PDFs which takes time. Try again later. Error: {error_msg}"
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error in contextual research: {error_msg}"
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket, str(id(websocket)))
    try:
        while True:
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            query = request_data.get("query")
            use_search = request_data.get("use_search", True)
            mode = request_data.get("mode", "ultra") # Default to ultra
            
            if not query:
                await manager.send_message({"type": "error", "content": "Query is empty"}, str(id(websocket)))
                continue

            async def on_step_update(step_name, step_details=None):
                 await manager.send_message({
                    "type": "status",
                    "stage": step_name,
                    "details": step_details
                }, str(id(websocket)))

            try:
                if mode == "ultra":
                    
                    import time
                    start_time = time.time()

                    async def ultra_search_function(q):
                         
                         
                         search_results = await run_in_thread(search_all, q, max_results_per_source=3)
                         
                         sources = []
                         context_parts = [search_results.get("combined_context", "")]
                         
                         from tools.arxiv_search import search_arxiv
                         arxiv_results = await run_in_thread(search_arxiv, q, max_results=2, extract_full_content=True)
                         
                         papers_extracted = 0
                         tables_found = 0

                         for paper in arxiv_results.get("results", []):
                            sources.append({
                                "title": paper["title"],
                                "url": paper["arxiv_url"],
                                "source_type": "arxiv",
                                "authors": paper["authors"]
                            })
                            if paper.get("full_text"):
                                papers_extracted += 1
                                context_parts.append(f"\n\nFULL PAPER: {paper['title']}\n{paper['full_text'][:5000]}")
                                if paper.get("tables"):
                                    tables_found += len(paper["tables"])
                                    for table in paper["tables"][:2]:
                                         context_parts.append(f"\n{table.get('markdown', '')}\n")

                         for article in search_results.get("web_results", []):
                            sources.append({
                                "title": article["title"],
                                "url": article["url"],
                                "source_type": "web"
                            })

                         return {
                            "sources": sources,
                            "context": "\n".join(context_parts),
                            "papers_extracted": papers_extracted,
                            "tables_found": tables_found
                        }

                    def ultra_memory_function(q):
                        return get_research_context(q, n_similar=3)

                    def ultra_save_function(query_text, answer, sources, quality_score, mode):
                         return save_research(
                             query_text=query_text,
                             mode=mode,
                             answer=answer,
                             sources=sources,
                             quality_score=quality_score,
                             processing_time=time.time() - start_time
                         )

                    ultra_workflow_ws = UltraResearchWorkflow(
                        planner=planner,
                        analyst=analyst,
                        writer=writer,
                        critic=critic,
                        search_func=ultra_search_function,
                        memory_func=ultra_memory_function,
                        save_func=ultra_save_function
                    )
                    
                    ultra_workflow_ws.on_step_update = on_step_update
                    
                    result = await ultra_workflow_ws.execute(query, use_search)
                    
                    await manager.send_message({
                        "type": "result",
                        "answer": result.get("final_report", ""),
                        "sources": result.get("sources", [])
                    }, str(id(websocket)))

                else:
                    async def search_func_std(q):
                        res = await run_in_thread(search_all, q, max_results_per_source=3)
                        return {"sources": [], "context": res["combined_context"]} # Simplified
                    
                    workflow.on_step_update = on_step_update
                    result = await workflow.execute_research(query, search_func_std)
                    
                    await manager.send_message({
                        "type": "result",
                         "answer": result["final_report"],
                         "sources": result["sources"]
                    }, str(id(websocket)))

            except Exception as e:
                await manager.send_message({"type": "error", "content": str(e)}, str(id(websocket)))

    except WebSocketDisconnect:
        manager.disconnect(str(id(websocket)))
    except Exception as e:
        print(f"WS Error: {e}")
        manager.disconnect(str(id(websocket)))


@app.post("/api/research/ultra")
async def research_ultra(request: ResearchRequest):
    """
    ULTRA MODE - Papersio Ultra
    
    Combines ALL features:
    - LangGraph state machine orchestration
    - Memory & context from past research
    - Full PDF extraction (text + tables)
    - Multi-agent collaboration (Plan → Search → Analyze → Write → Critique)
    - Quality-based automatic revisions
    - Automatic database storage
    
    This is the most advanced and comprehensive research mode!
    
    Example:
        POST /api/research/ultra
        Body: {"query": "What is quantum computing?", "use_search": true}
    """
    import time
    start_time = time.time()
    
    try:
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        print(f"\nULTRA MODE: {request.query}")
        
        async def ultra_search_function(query: str):
            """Enhanced search with full PDF extraction"""
            if not request.use_search:
                return {
                    "sources": [],
                    "context": "",
                    "papers_extracted": 0,
                    "tables_found": 0
                }
            
            print(f" Searching ArXiv with PDF extraction...")
            arxiv_results = search_arxiv(
                query,
                max_results=2,
                extract_full_content=True
            )
            
            search_results = search_all(query, max_results_per_source=3)
            
            sources = []
            context_parts = [search_results.get("combined_context", "")]
            papers_extracted = 0
            tables_found = 0
            
            for paper in arxiv_results.get("results", []):
                sources.append({
                    "title": paper["title"],
                    "url": paper["arxiv_url"],
                    "source_type": "arxiv",
                    "authors": paper["authors"]
                })
                
                if paper.get("full_text"):
                    papers_extracted += 1
                    context_parts.append(f"\n\nFULL PAPER: {paper['title']}\n{paper['full_text'][:5000]}")
                    
                    if paper.get("tables"):
                        tables_found += len(paper["tables"])
                        for table in paper["tables"][:2]:  # First 2 tables
                            context_parts.append(f"\n{table.get('markdown', '')}\n")
            
            for article in search_results.get("web_results", []):
                sources.append({
                    "title": article["title"],
                    "url": article["url"],
                    "source_type": "web"
                })
            
            return {
                "sources": sources,
                "context": "\n".join(context_parts),
                "papers_extracted": papers_extracted,
                "tables_found": tables_found
            }
        
        def ultra_memory_function(query: str):
            """Get relevant past research"""
            return get_research_context(query, n_similar=3)
        
        def ultra_save_function(query_text, answer, sources, quality_score, mode):
            """Save research to database"""
            return save_research(
                query_text=query_text,
                mode=mode,
                answer=answer,
                sources=sources,
                quality_score=quality_score,
                processing_time=time.time() - start_time
            )
        
        ultra_workflow = UltraResearchWorkflow(
            planner=planner,
            analyst=analyst,
            writer=writer,
            critic=critic,
            search_func=ultra_search_function,
            memory_func=ultra_memory_function,
            save_func=ultra_save_function
        )
        
        final_state = await ultra_workflow.execute(
            query=request.query,
            use_search=request.use_search
        )
        
        formatted_sources = []
        for source in final_state.get("sources", []):
            formatted_sources.append(Source(
                title=source["title"],
                url=source["url"],
                source_type=source["source_type"],
                authors=source.get("authors")
            ))
        
        workflow_stages = [
            {
                "stage": "Memory",
                "status": "complete",
                "details": f"Found {len(final_state.get('past_research', []))} similar past research(es)"
            },
            {
                "stage": "Planning",
                "status": "complete",
                "details": final_state.get("plan", {})
            },
            {
                "stage": "Search",
                "status": "complete",
                "details": {
                    "papers_extracted": final_state.get("papers_extracted", 0),
                    "tables_found": final_state.get("tables_found", 0),
                    "sources": len(final_state.get("sources", []))
                }
            },
            {
                "stage": "Analysis",
                "status": "complete",
                "details": {
                    "themes": len(final_state.get("themes", [])),
                    "findings": len(final_state.get("key_findings", []))
                }
            },
            {
                "stage": "Writing",
                "status": "complete",
                "details": f"Generated ({len(final_state.get('draft_report', ''))} chars)"
            },
            {
                "stage": "Critique",
                "status": "complete",
                "details": {
                    "quality_score": final_state.get("quality_score", 0),
                    "approved": final_state.get("approved", False),
                    "revisions": final_state.get("retry_count", 0)
                }
            },
            {
                "stage": "Database",
                "status": "complete" if final_state.get("saved_to_db") else "failed",
                "details": f"Saved with query_id={final_state.get('query_id')}"
            }
        ]
        
        return {
            "query": request.query,
            "answer": final_state.get("final_report", ""),
            "sources": formatted_sources,
            "workflow_stages": workflow_stages,
            "quality_assessment": final_state.get("critique"),
            "search_strategy": "🚀 ULTRA: LangGraph + Memory + Full PDFs + Quality Revisions + Auto-Save",
            "framework": "UltraMode",
            "has_past_context": final_state.get("has_past_context", False),
            "papers_extracted": final_state.get("papers_extracted", 0),
            "tables_found": final_state.get("tables_found", 0),
            "revisions_made": final_state.get("retry_count", 0),
            "saved_to_database": final_state.get("saved_to_db", False),
            "processing_time": time.time() - start_time,
            "errors": final_state.get("errors", [])
        }
    
    except Exception as e:
        error_msg = str(e)
        
        if "429" in error_msg or "quota" in error_msg.lower():
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Ultra mode uses extensive API calls. Please wait and try again. Error: {error_msg}"
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error in Ultra execution: {error_msg}"
        )


@app.post("/api/research/export/pdf")
def export_research_pdf(
    research_data: dict,
    citation_style: str = "IEEE"
):
    """
    Export research result as a publication-quality PDF using LaTeX.
    
    Request body should include:
        - query: str
        - answer: str
        - sources: List[Dict]
        - quality_assessment: Optional[Dict]
    
    Citation styles: IEEE, APA, ACM, Nature
    """
    try:
        print(f"Generating PDF export with {citation_style} citations...")
        
        if not research_data.get("query") or not research_data.get("answer"):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: query and answer"
            )
        
        pdf_path = generate_research_pdf(research_data, citation_style)
        
        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=500,
                detail="PDF generation failed - file not created"
            )
        
        filename = f"research_paper_{int(time.time())}.pdf"
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except RuntimeError as e:
        error_msg = str(e)
        if "LaTeX not found" in error_msg:
            raise HTTPException(
                status_code=503,
                detail=(
                    "LaTeX is not installed on the server. "
                    "Please install: brew install --cask basictex (macOS) "
                    "or sudo apt-get install texlive-latex-base texlive-latex-extra (Linux)"
                )
            )
        elif "compilation failed" in error_msg:
            raise HTTPException(
                status_code=500,
                detail=f"LaTeX compilation failed: {error_msg}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"PDF generation error: {error_msg}"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during PDF export: {str(e)}"
        )


@app.get("/api/stats")
def get_stats():
    """
    Get statistics about stored research
    """
    try:
        stats = get_research_stats()
        from tools.embeddings import get_collection_stats
        vector_stats = get_collection_stats()
        
        return {
            "database": stats,
            "vectors": vector_stats,
            "message": "Research memory statistics"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    print("Starting Papersio API...")
    print("API docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
