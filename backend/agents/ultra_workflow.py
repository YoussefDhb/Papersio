"""
Ultra Research Workflow - Papersio Ultra Mode
Combines: LangGraph + Memory + Full PDF Analysis + Quality Revisions
"""

from typing import Dict, List, TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
import operator


class UltraResearchState(TypedDict):
    """Enhanced state with memory and PDF analysis"""

    query: str
    use_search: bool

    has_past_context: bool
    past_research: List[Dict]

    plan: Dict
    needs_breakdown: bool
    sub_questions: List[str]

    sources: List[Dict]
    search_context: str
    papers_extracted: int
    tables_found: int

    analysis: Dict
    key_findings: List[str]
    themes: List[str]

    draft_report: str

    critique: Dict
    quality_score: int
    approved: bool

    final_report: str

    current_stage: str
    errors: Annotated[List[str], operator.add]
    retry_count: int

    saved_to_db: bool
    query_id: Optional[int]


class UltraResearchWorkflow:
    """
    ULTRA MODE: The most advanced research workflow

    Combines:
    - LangGraph state machine orchestration
    - Memory & context from past research
    - Full PDF extraction (text + tables)
    - Multi-agent collaboration
    - Quality-based revisions
    - Automatic database storage
    """

    def __init__(self, planner, analyst, writer, critic, search_func, memory_func, save_func):
        """
        Initialize with all components

        Args:
            planner: Planning agent
            analyst: Analysis agent
            writer: Writing agent
            critic: Critique agent
            search_func: Async function to perform searches (with PDF extraction)
            memory_func: Function to search past research
            save_func: Function to save results to database
        """
        self.planner = planner
        self.analyst = analyst
        self.writer = writer
        self.critic = critic
        self.search_func = search_func
        self.memory_func = memory_func
        self.save_func = save_func
        self.on_step_update = None  # Callback for real-time updates

        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the Ultra workflow graph"""

        workflow = StateGraph(UltraResearchState)

        workflow.add_node("memory", self._memory_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("search", self._search_node)
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("write", self._write_node)
        workflow.add_node("critique", self._critique_node)
        workflow.add_node("save", self._save_node)
        workflow.add_node("finalize", self._finalize_node)

        workflow.set_entry_point("memory")

        workflow.add_edge("memory", "plan")
        workflow.add_edge("plan", "search")
        workflow.add_edge("search", "analyze")
        workflow.add_edge("analyze", "write")
        workflow.add_edge("write", "critique")

        workflow.add_conditional_edges("critique", self._should_revise, {"revise": "write", "save": "save"})

        workflow.add_edge("save", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    async def _send_update(self, stage, details=None):
        if self.on_step_update:
            await self.on_step_update(stage, details)

    async def _memory_node(self, state: UltraResearchState) -> Dict:
        """Stage 0: Check memory for relevant past research"""
        await self._send_update("Checking Memory", "Looking for relevant past research...")
        print("Stage 0: Checking memory...")

        try:
            context = self.memory_func(state["query"])

            if context.get("has_context"):
                print(f"Found {len(context['similar_queries'])} similar past research(es)")
                return {"has_past_context": True, "past_research": context["similar_queries"], "current_stage": "memory"}
            else:
                print("No past research found - starting fresh")
                return {"has_past_context": False, "past_research": [], "current_stage": "memory"}
        except Exception as e:
            print(f"Memory search error: {e}")
            return {
                "has_past_context": False,
                "past_research": [],
                "errors": [f"Memory search failed: {str(e)}"],
                "current_stage": "memory",
            }

    async def _plan_node(self, state: UltraResearchState) -> Dict:
        """Stage 1: Planning with memory context"""
        await self._send_update("Planning", "Creating research plan...")
        print("Stage 1: Planning...")

        planning_context = f"Query: {state['query']}\n"

        if state.get("has_past_context"):
            planning_context += "\nRelevant past research:\n"
            for pr in state["past_research"][:2]:  # Top 2
                planning_context += f"- {pr['past_query']}\n"

        plan = self.planner.create_research_plan(planning_context)

        return {
            "plan": plan,
            "needs_breakdown": plan.get("needs_breakdown", False),
            "sub_questions": plan.get("sub_questions", [state["query"]]),
            "current_stage": "plan",
        }

    async def _search_node(self, state: UltraResearchState) -> Dict:
        """Stage 2: Search with full PDF extraction"""
        await self._send_update("Searching", "Searching ArXiv and Web (with PDF extractions)...")
        print("Stage 2: Searching (with full PDF extraction)...")

        if not state.get("use_search", True):
            return {"sources": [], "search_context": "", "papers_extracted": 0, "tables_found": 0, "current_stage": "search"}

        all_sources = []
        all_contexts = []
        papers_count = 0
        tables_count = 0

        for sub_q in state["sub_questions"]:
            try:
                result = await self.search_func(sub_q)
                all_sources.extend(result.get("sources", []))

                if result.get("context"):
                    all_contexts.append(result["context"])

                papers_count += result.get("papers_extracted", 0)
                tables_count += result.get("tables_found", 0)

            except Exception as e:
                print(f"Search error for '{sub_q}': {e}")
                state["errors"].append(f"Search failed: {str(e)}")

        print(f"Extracted {papers_count} papers, {tables_count} tables")

        return {
            "sources": all_sources,
            "search_context": "\n\n".join(all_contexts),
            "papers_extracted": papers_count,
            "tables_found": tables_count,
            "current_stage": "search",
        }

    async def _analyze_node(self, state: UltraResearchState) -> Dict:
        """Stage 3: Analysis with past context"""
        await self._send_update("Analyzing", "Analyzing collected sources...")
        print("Stage 3: Analyzing...")

        try:
            analysis_context = state.get("search_context", "")

            if state.get("has_past_context"):
                analysis_context = "PAST RESEARCH CONTEXT:\n"
                for pr in state["past_research"]:
                    analysis_context += f"\n{pr['past_query']}: {pr['past_answer'][:200]}...\n"
                analysis_context += f"\nNEW RESEARCH:\n{state.get('search_context', '')}"

            analysis = self.analyst.analyze_sources(state["query"], analysis_context)

            return {
                "analysis": analysis,
                "key_findings": analysis.get("key_findings", []),
                "themes": analysis.get("themes", []),
                "current_stage": "analyze",
            }
        except Exception as e:
            print(f"Analysis error: {e}")
            return {
                "analysis": {},
                "key_findings": [],
                "themes": [],
                "errors": [f"Analysis failed: {str(e)}"],
                "current_stage": "analyze",
            }

    async def _write_node(self, state: UltraResearchState) -> Dict:
        """Stage 4: Writing"""
        await self._send_update("Writing", "Drafting research report...")
        print("Stage 4: Writing...")

        retry_count = state.get("retry_count", 0)
        if state.get("current_stage") == "critique":
            retry_count += 1
            print(f"Revision attempt {retry_count}...")

        try:
            writing_context = state.get("search_context", "")

            if state.get("has_past_context"):
                writing_context = "REFERENCE PREVIOUS RESEARCH:\n"
                for pr in state["past_research"]:
                    writing_context += f"- {pr['past_query']}\n"
                writing_context += f"\nNEW INFORMATION:\n{state.get('search_context', '')}"

            critique_feedback = state.get("critique") if state.get("current_stage") == "critique" else None
            result = await self.writer.write_report(
                state["query"], state.get("analysis", {}), writing_context, critique_feedback=critique_feedback
            )

            return {"draft_report": result.get("report", ""), "retry_count": retry_count, "current_stage": "write"}
        except Exception as e:
            print(f"Writing error: {e}")
            return {
                "draft_report": "Error generating report",
                "errors": [f"Writing failed: {str(e)}"],
                "retry_count": retry_count,
                "current_stage": "write",
            }

    async def _critique_node(self, state: UltraResearchState) -> Dict:
        """Stage 5: Critique"""
        await self._send_update("Critiquing", "Reviewing report quality...")
        print("Stage 5: Critiquing...")

        try:
            critique = self.critic.critique_report(state["query"], state.get("draft_report", ""))

            return {
                "critique": critique,
                "quality_score": critique.get("quality_score", 0),
                "approved": critique.get("approved", True),
                "current_stage": "critique",
            }
        except Exception as e:
            print(f"Critique error: {e}")
            return {
                "critique": {"error": str(e)},
                "quality_score": 70,
                "approved": True,
                "errors": [f"Critique failed: {str(e)}"],
                "current_stage": "critique",
            }

    async def _save_node(self, state: UltraResearchState) -> Dict:
        """Stage 6: Save to database"""
        await self._send_update("Saving", "Saving results to database...")
        print("Stage 6: Saving to database...")

        try:
            save_result = self.save_func(
                query_text=state["query"],
                answer=state.get("draft_report", ""),
                sources=[s for s in state.get("sources", [])],
                quality_score=state.get("quality_score"),
                mode="ultra",
            )

            if save_result.get("success"):
                print(f"Saved: query_id={save_result.get('query_id')}")
                return {"saved_to_db": True, "query_id": save_result.get("query_id"), "current_stage": "save"}
            else:
                return {"saved_to_db": False, "errors": [f"Save failed: {save_result.get('error')}"], "current_stage": "save"}
        except Exception as e:
            print(f"Save error: {e}")
            return {"saved_to_db": False, "errors": [f"Save failed: {str(e)}"], "current_stage": "save"}

    async def _finalize_node(self, state: UltraResearchState) -> Dict:
        """Stage 7: Finalization"""
        await self._send_update("Finished", "Research complete!")
        print("Stage 7: Finalizing...")

        return {"final_report": state.get("draft_report", ""), "current_stage": "complete"}

    def _should_revise(self, state: UltraResearchState) -> str:
        """Decide whether to revise or save"""

        if state.get("retry_count", 0) >= 3:
            print("Max revisions reached, proceeding to save")
            return "save"

        if not state.get("approved", True) or state.get("quality_score", 100) < 80:
            print("Quality needs improvement, revising...")
            return "revise"

        return "save"

    async def execute(self, query: str, use_search: bool = True) -> Dict:
        """Execute the Ultra workflow"""

        initial_state: UltraResearchState = {
            "query": query,
            "use_search": use_search,
            "has_past_context": False,
            "past_research": [],
            "plan": {},
            "needs_breakdown": False,
            "sub_questions": [],
            "sources": [],
            "search_context": "",
            "papers_extracted": 0,
            "tables_found": 0,
            "analysis": {},
            "key_findings": [],
            "themes": [],
            "draft_report": "",
            "critique": {},
            "quality_score": 0,
            "approved": False,
            "final_report": "",
            "current_stage": "init",
            "errors": [],
            "retry_count": 0,
            "saved_to_db": False,
            "query_id": None,
        }

        print("Starting ULTRA Research Workflow...")
        print("=" * 60)

        final_state = initial_state
        async for output in self.workflow.astream(initial_state):
            for key, value in output.items():
                if isinstance(value, dict):
                    final_state.update(value)

        print("=" * 60)
        print("ULTRA Workflow Complete!")

        return final_state
