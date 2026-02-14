"""
Writer Agent
Creates structured, well-written research reports
"""

from typing import Dict, Optional
from thread_executor import run_in_thread


class WriterAgent:
    """
    Writes comprehensive research reports based on analysis
    """

    def __init__(self, llm_provider):
        """
        Initialize the writer with an LLM provider

        Args:
            llm_provider: LLMProvider instance
        """
        self.llm = llm_provider

    async def write_report(
        self, question: str, analysis: Dict, sources_context: str = "", critique_feedback: Optional[Dict] = None
    ) -> Dict:
        """
        Write a comprehensive research report

        Args:
            question: The research question
            analysis: Analysis from the Analyst Agent
            sources_context: Optional raw source text

        Returns:
            Dict with:
            - report: The written report
            - structure: Report structure used
        """

        findings_text = "\n".join([f"- {f}" for f in analysis.get("key_findings", [])])
        themes_text = "\n".join([f"- {t}" for t in analysis.get("themes", [])])

        prompt = f"""You are an expert research writer creating an academic-style research report.
    Your output will be used to generate a publication-quality PDF, so structure, rigor, and citations are crucial.

RESEARCH QUESTION: {question}

KEY FINDINGS FROM ANALYSIS:
{findings_text}

MAIN THEMES:
{themes_text}

CONFIDENCE LEVEL: {analysis.get('confidence', 'medium')}

ANALYSIS SUMMARY:
{analysis.get('summary', '')}
"""

        if critique_feedback:
            prompt += """
REVISION FEEDBACK (address all items):
"""
            for item in critique_feedback.get("recommendations", []):
                prompt += f"- {item}\n"

        if sources_context:
            prompt += f"\nRAW SOURCES (for reference):\n{sources_context[:2000]}\n"

        prompt += """
            Your task:
            Write a comprehensive research report using the EXACT section structure below. Each section is mandatory.


            Write a concise 2-3 sentence summary of the research question, methodology, and key findings.

            - Introduce the research question and its significance
            - Provide context and background
            - State the objectives of this research

            - Explain the research approach used
            - Describe data sources (ArXiv papers, web sources, etc.)
            - Mention any AI/ML techniques applied (LangGraph agents, RAG, semantic search, etc.)

            - Present the main research findings in detail
            - Use subsections (###) for different aspects
            - Include citations for all claims
            - Use bullet points and tables where appropriate

            - Analyze and interpret the findings
            - Compare different perspectives from sources
            - Discuss implications and significance
            - Address limitations or uncertainties

            - Summarize the key takeaways
            - Provide clear answers to the research question
            - Suggest future research directions if applicable

            1. **Headings**: Use ## for main sections, ### for subsections
            2. **Citations**: Use [1], [2], [3] format for all source references
            3. **Evidence density**: Every factual claim must have a citation
            4. **Clarity**: Write in clear, professional academic language
            5. **Length**: Be comprehensive but concise (aim for 700-1200 words)
            6. **Tables**: Use markdown tables if comparing multiple items
            7. **Bullets**: Use for lists and key points

            Write the complete structured report now, following the EXACT section headings above.
            Do not include any text outside the report:
        """

        required_sections = [
            "## Abstract",
            "## Introduction",
            "## Methodology",
            "## Findings",
            "## Discussion",
            "## Conclusion",
        ]

        def missing_sections(report_text: str) -> list:
            report_lower = report_text.lower()
            return [s for s in required_sections if s.lower() not in report_lower]

        try:
            report = await run_in_thread(self.llm.generate, prompt, temperature=0.7, max_tokens=4000)

            missing = missing_sections(report)
            if missing:
                repair_prompt = f"""You are correcting an incomplete research report.
                                The report is missing these required sections: {", ".join(missing)}.

                                Return the FULL report with ALL required sections and the exact headings:
                                {chr(10).join(required_sections)}

                                Keep any valid content from the original report, but ensure every section is present and complete.
                                Only return the report with those exact headings, no extra text.

                                ORIGINAL REPORT:
                                {report}
                                """
                report = await run_in_thread(self.llm.generate, repair_prompt, temperature=0.4, max_tokens=4000)

            return {"success": True, "report": report, "structure": "markdown", "word_count": len(report.split())}

        except Exception as e:
            return {"success": False, "error": str(e), "report": f"Error generating report: {str(e)}", "structure": "text"}
