"""
Research Workflow Coordinator
Orchestrates the multi-step research process
"""

from typing import Dict
from .planner import PlannerAgent
from .analyst import AnalystAgent
from .writer import WriterAgent
from .critic import CriticAgent


class ResearchWorkflow:
    """
    Coordinates the complete research workflow:
    Plan → Search → Analyze → Write → Critique
    """

    def __init__(self, planner: PlannerAgent, analyst: AnalystAgent, writer: WriterAgent, critic: CriticAgent):
        """
        Initialize workflow with all agents

        Args:
            planner: Planning Agent
            analyst: Analyst Agent
            writer: Writer Agent
            critic: Critic Agent
        """
        self.planner = planner
        self.analyst = analyst
        self.writer = writer
        self.critic = critic

    async def execute_research(self, question: str, search_func, use_critique: bool = True) -> Dict:
        """
        Execute the complete research workflow

        Args:
            question: Research question
            search_func: Async function to perform search (returns sources and context)
            use_critique: Whether to use the critique step

        Returns:
            Dict with:
            - workflow_stages: Results from each stage
            - final_report: The final research report
            - quality_assessment: Critique results if enabled
        """

        async def send_update(stage, details=None):
            if hasattr(self, "on_step_update") and self.on_step_update:
                await self.on_step_update(stage, details)

        workflow_stages = {}

        await send_update("Planning", "Creating research plan...")
        plan = self.planner.create_research_plan(question)
        workflow_stages["plan"] = plan

        if plan.get("needs_breakdown") and plan.get("sub_questions"):
            sub_questions = plan["sub_questions"]
        else:
            sub_questions = [question]

        await send_update("Searching", "Searching for information...")
        all_sources = []
        all_contexts = []
        search_results_list = []

        for sub_q in sub_questions:
            search_result = await search_func(sub_q)
            search_results_list.append(
                {"question": sub_q, "sources": search_result.get("sources", []), "context": search_result.get("context", "")}
            )
            all_sources.extend(search_result.get("sources", []))
            if search_result.get("context"):
                all_contexts.append(f"## {sub_q}\n{search_result['context']}")

        combined_context = "\n\n".join(all_contexts)
        workflow_stages["search"] = {"sub_results": search_results_list, "total_sources": len(all_sources)}

        await send_update("Analyzing", "Analyzing sources and extracting insights...")
        analysis = self.analyst.analyze_sources(question, combined_context)
        workflow_stages["analysis"] = analysis

        await send_update("Writing", "Drafting final report...")
        report_result = await self.writer.write_report(question, analysis, combined_context)
        workflow_stages["write"] = report_result
        final_report = report_result.get("report", "")

        if use_critique:
            max_revisions = 3
            revision_count = 0

            await send_update("Critiquing", "Reviewing report quality...")
            critique = self.critic.critique_report(question, final_report)
            workflow_stages["critique"] = critique

            while not critique.get("approved", True) and revision_count < max_revisions:
                revision_count += 1
                await send_update("Revising", f"Applying critique feedback (attempt {revision_count}/{max_revisions})...")
                revision_result = await self.writer.write_report(
                    question, analysis, combined_context, critique_feedback=critique
                )
                workflow_stages[f"write_revision_{revision_count}"] = revision_result
                final_report = revision_result.get("report", final_report)

                await send_update("Re-Critiquing", "Validating revised report...")
                critique = self.critic.critique_report(question, final_report)
                workflow_stages[f"critique_revision_{revision_count}"] = critique

            workflow_stages["status"] = "approved" if critique.get("approved", True) else "needs_revision"
        else:
            workflow_stages["status"] = "completed"

        return {
            "workflow_stages": workflow_stages,
            "final_report": final_report,
            "sources": all_sources,
            "quality_assessment": workflow_stages.get("critique_revision") or workflow_stages.get("critique"),
            "success": True,
        }
