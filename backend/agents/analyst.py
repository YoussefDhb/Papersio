"""
Analyst Agent
Extracts key information from research sources
"""

from typing import Dict
import json


class AnalystAgent:
    """
    Analyzes sources and extracts key information
    """

    def __init__(self, llm_provider):
        """
        Initialize the analyst with an LLM provider

        Args:
            llm_provider: LLMProvider instance
        """
        self.llm = llm_provider

    def analyze_sources(self, question: str, sources_context: str) -> Dict:
        """
        Analyze sources and extract key information relevant to the question

        Args:
            question: The research question
            sources_context: Combined text from all sources

        Returns:
            Dict with:
            - key_findings: List of important facts
            - themes: Main themes identified
            - gaps: What's missing or unclear
            - analysis: Overall analysis text
        """

        prompt = f"""You are an expert research analyst. Your job is to carefully analyze research sources and extract key information.

                RESEARCH QUESTION: {question}

                SOURCES TO ANALYZE:
                {sources_context}

                Your task:
                1. Read through all the sources carefully
                2. Extract the most important facts and insights
                3. Identify main themes or patterns
                4. Note any gaps or contradictions in the information

                Provide your analysis in the following JSON format:
                {{
                    "key_findings": [
                        "Finding 1 with [source number]",
                        "Finding 2 with [source number]",
                        "Finding 3 with [source number]"
                    ],
                    "themes": [
                        "Theme 1",
                        "Theme 2"
                    ],
                    "gaps": [
                        "Gap or missing information 1",
                        "Gap or missing information 2"
                    ],
                    "confidence": "high/medium/low",
                    "summary": "Brief summary of what the sources tell us"
                }}

                Focus on:
                - Factual accuracy
                - Relevance to the question
                - Citing sources for each finding
                - Identifying what we know vs what's unclear

                Respond with ONLY valid JSON, no other text.
                """
        try:
            response_text = self.llm.generate(prompt, temperature=0.5).strip()

            if response_text.startswith("```"):
                start = response_text.find("{")
                end = response_text.rfind("}")
                if start != -1 and end != -1:
                    response_text = response_text[start : end + 1]

            analysis = json.loads(response_text)

            return {
                "success": True,
                "key_findings": analysis.get("key_findings", []),
                "themes": analysis.get("themes", []),
                "gaps": analysis.get("gaps", []),
                "confidence": analysis.get("confidence", "medium"),
                "summary": analysis.get("summary", ""),
                "question": question,
            }

        except Exception as e:
            simple_prompt = f"""Analyze these sources for the question: {question}

{sources_context}

Provide a brief analysis of the key points."""
            summary = self.llm.generate(simple_prompt, temperature=0.5)

            return {
                "success": False,
                "error": str(e),
                "key_findings": [],
                "themes": [],
                "gaps": [],
                "confidence": "medium",
                "summary": summary,
                "question": question,
            }
