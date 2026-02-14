"""
Critic Agent
Reviews research reports for quality and completeness
"""

from typing import Dict
import json
import re


class CriticAgent:
    """
    Reviews research reports and provides feedback
    """

    def __init__(self, llm_provider):
        """
        Initialize the critic with an LLM provider

        Args:
            llm_provider: LLMProvider instance
        """
        self.llm = llm_provider

    def critique_report(self, question: str, report: str) -> Dict:
        """
        Critique a research report for quality

        Args:
            question: The original research question
            report: The research report to critique

        Returns:
            Dict with:
            - overall_quality: Rating (excellent/good/fair/poor)
            - strengths: List of strong points
            - weaknesses: List of areas for improvement
            - missing_topics: Topics that should be covered
            - recommendations: Specific improvements
            - approved: Boolean whether report meets quality standards
        """

        prompt = f"""You are a senior research reviewer. Your job is to critically evaluate research reports for quality, completeness, and accuracy.

RESEARCH QUESTION: {question}

RESEARCH REPORT TO REVIEW:
{report}

Evaluate this report on:
1. **Completeness**: Does it fully address the question?
2. **Accuracy**: Is the information correct?
3. **Structure**: Is it well-organized?
4. **Clarity**: Is it easy to understand?
5. **Evidence**: Are claims properly cited?
6. **Depth**: Does it provide sufficient detail?

Provide your critique in JSON format:
{{
    "overall_quality": "excellent/good/fair/poor",
    "quality_score": 0-100,
    "strengths": [
        "Strength 1",
        "Strength 2"
    ],
    "weaknesses": [
        "Weakness 1",
        "Weakness 2"
    ],
    "missing_topics": [
        "Missing topic 1",
        "Missing topic 2"
    ],
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ],
    "approved": true/false,
    "feedback_summary": "Brief overall assessment"
}}

Be constructive but thorough. Identify both strengths and areas for improvement.

Respond with ONLY valid JSON, no other text.
"""

        try:
            response_text = self.llm.generate(prompt, temperature=0.5).strip()

            if response_text.startswith("```"):
                start = response_text.find("{")
                end = response_text.rfind("}")
                if start != -1 and end != -1:
                    response_text = response_text[start : end + 1]

            critique = json.loads(response_text)

            required_sections = [
                "## abstract",
                "## introduction",
                "## methodology",
                "## findings",
                "## discussion",
                "## conclusion",
            ]
            report_lower = report.lower()
            missing_sections = [s for s in required_sections if s not in report_lower]
            has_citations = re.search(r"\[\d+\]", report) is not None

            quality_score = int(critique.get("quality_score", 75))
            approved = bool(critique.get("approved", True))

            if missing_sections:
                quality_score = min(quality_score, 65)
                approved = False
                critique.setdefault("weaknesses", []).append("Missing required report sections")
                critique.setdefault("recommendations", []).append(
                    "Include all required sections: Abstract, Introduction, Methodology, Findings, Discussion, Conclusion"
                )

            if not has_citations:
                quality_score = min(quality_score, 60)
                approved = False
                critique.setdefault("weaknesses", []).append("Missing citations for factual claims")
                critique.setdefault("recommendations", []).append("Add citations [1], [2], [3] to all factual claims")

            if quality_score < 80:
                approved = False

            return {
                "success": True,
                "overall_quality": critique.get("overall_quality", "good"),
                "quality_score": quality_score,
                "strengths": critique.get("strengths", []),
                "weaknesses": critique.get("weaknesses", []),
                "missing_topics": critique.get("missing_topics", []),
                "recommendations": critique.get("recommendations", []),
                "approved": approved,
                "feedback_summary": critique.get("feedback_summary", ""),
            }

        except Exception as e:
            simple_prompt = f"""Briefly assess this research report for: {question}

Report:
{report[:1000]}...

Is it good quality? What could be improved?"""

            feedback = self.llm.generate(simple_prompt, temperature=0.5)

            return {
                "success": False,
                "error": str(e),
                "overall_quality": "fair",
                "quality_score": 60,
                "strengths": ["Report provides information"],
                "weaknesses": ["Could not perform detailed analysis"],
                "missing_topics": [],
                "recommendations": [
                    "Re-run critique to obtain structured JSON feedback",
                    "Address required sections and add citations",
                ],
                "approved": False,
                "feedback_summary": feedback[:200],
            }
