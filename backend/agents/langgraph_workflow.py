"""
LangGraph-based Research Workflow
Professional state machine orchestration for multi-agent research
"""

from typing import Dict, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator


class ResearchState(TypedDict):
    """State object that flows through the workflow"""

    query: str
    use_search: bool

    plan: Dict
    needs_breakdown: bool
    sub_questions: List[str]

    sources: List[Dict]
    search_context: str

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


class LangGraphResearchWorkflow:
    """
    LangGraph-based workflow for orchestrating research agents
    """

    def __init__(self, planner, analyst, writer, critic, search_func):
        """
        Initialize with all agents and search function

        Args:
            planner: Planning agent
            analyst: Analysis agent
            writer: Writing agent
            critic: Critique agent
            search_func: Async function to perform searches
        """
        self.planner = planner
        self.analyst = analyst
        self.writer = writer
        self.critic = critic
        self.search_func = search_func

        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""

        workflow = StateGraph(ResearchState)

        workflow.add_node("plan", self._plan_node)
        workflow.add_node("search", self._search_node)
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("write", self._write_node)
        workflow.add_node("critique", self._critique_node)
        workflow.add_node("finalize", self._finalize_node)

        workflow.set_entry_point("plan")

        workflow.add_edge("plan", "search")
        workflow.add_edge("search", "analyze")
        workflow.add_edge("analyze", "write")
        workflow.add_edge("write", "critique")

        workflow.add_conditional_edges(
            "critique",
            self._should_revise,
            {
                "revise": "write",  # Loop back to writing if not approved
                "finalize": "finalize",  # Move to finalization if approved
            },
        )

        workflow.add_edge("finalize", END)

        return workflow.compile()

    def _plan_node(self, state: ResearchState) -> Dict:
        """Planning stage"""
        print("Stage 1: Planning...")

        plan = self.planner.create_research_plan(state["query"])

        return {
            "plan": plan,
            "needs_breakdown": plan.get("needs_breakdown", False),
            "sub_questions": plan.get("sub_questions", [state["query"]]),
            "current_stage": "plan",
        }

    async def _search_node(self, state: ResearchState) -> Dict:
        """Search stage"""
        print("Stage 2: Searching...")

        if not state.get("use_search", True):
            return {"sources": [], "search_context": "", "current_stage": "search"}

        all_sources = []
        all_contexts = []

        for sub_q in state["sub_questions"]:
            try:
                result = await self.search_func(sub_q)
                all_sources.extend(result.get("sources", []))
                if result.get("context"):
                    all_contexts.append(result["context"])
            except Exception as e:
                print(f"Search error for '{sub_q}': {e}")
                state["errors"].append(f"Search failed: {str(e)}")

        return {"sources": all_sources, "search_context": "\n\n".join(all_contexts), "current_stage": "search"}

    def _analyze_node(self, state: ResearchState) -> Dict:
        """Analysis stage"""
        print("Stage 3: Analyzing...")

        try:
            analysis = self.analyst.analyze_sources(state["query"], state.get("search_context", ""))

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

    async def _write_node(self, state: ResearchState) -> Dict:
        """Writing stage"""
        print("Stage 4: Writing...")

        retry_count = state.get("retry_count", 0)
        if state.get("current_stage") == "critique":
            retry_count += 1
            print(f"Revision attempt {retry_count}...")

        try:
            critique_feedback = state.get("critique") if state.get("current_stage") == "critique" else None
            result = await self.writer.write_report(
                state["query"], state.get("analysis", {}), state.get("search_context", ""), critique_feedback=critique_feedback
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

    def _critique_node(self, state: ResearchState) -> Dict:
        """Critique stage"""
        print("🎓 Stage 5: Critiquing...")

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
                "approved": True,  # Approve if we can't critique
                "errors": [f"Critique failed: {str(e)}"],
                "current_stage": "critique",
            }

    def _finalize_node(self, state: ResearchState) -> Dict:
        """Finalization stage"""
        print("Stage 6: Finalizing...")

        return {"final_report": state.get("draft_report", ""), "current_stage": "complete"}

    def _should_revise(self, state: ResearchState) -> str:
        """Decide whether to revise or finalize"""

        if state.get("retry_count", 0) >= 3:
            print("Max revisions reached, proceeding to finalization")
            return "finalize"

        if not state.get("approved", True) or state.get("quality_score", 100) < 80:
            print("Quality needs improvement, revising...")
            return "revise"

        return "finalize"

    async def execute(self, query: str, use_search: bool = True) -> Dict:
        """
        Execute the complete research workflow

        Args:
            query: Research question
            use_search: Whether to use search

        Returns:
            Final state with all results
        """

        initial_state: ResearchState = {
            "query": query,
            "use_search": use_search,
            "plan": {},
            "needs_breakdown": False,
            "sub_questions": [],
            "sources": [],
            "search_context": "",
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
        }

        print("Starting LangGraph Research Workflow...")
        print("=" * 50)

        final_state = initial_state
        async for output in self.workflow.astream(initial_state):
            for key, value in output.items():
                if isinstance(value, dict):
                    final_state.update(value)

        print("=" * 50)
        print("Workflow Complete!")

        return final_state
