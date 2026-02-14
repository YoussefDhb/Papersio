"""
Planning Agent
Breaks down complex research questions into manageable sub-questions
"""

from typing import Dict
import json


class PlannerAgent:
    """
    Plans research by decomposing complex questions into sub-questions
    """

    def __init__(self, llm_provider):
        """
        Initialize the planner with an LLM provider

        Args:
            llm_provider: LLMProvider instance
        """
        self.llm = llm_provider

    def create_research_plan(self, query: str) -> Dict:
        """
        Create a research plan by breaking down the query into sub-questions

        Args:
            query: The main research question

        Returns:
            Dict with:
            - main_query: Original question
            - sub_questions: List of sub-questions
            - reasoning: Why this breakdown makes sense
        """

        prompt = f"""You are a research planning expert. Your job is to break down complex research questions into focused sub-questions.

                MAIN RESEARCH QUESTION: {query}

                Analyze this question and create a research plan by:
                1. Identifying the key aspects that need to be researched
                2. Breaking it down into 3-5 specific, focused sub-questions
                3. Ensuring sub-questions are logical and build toward answering the main question

                RULES:
                - Each sub-question should be clear and specific
                - Sub-questions should be answerable through research
                - Cover all important aspects of the main question
                - Order sub-questions logically (foundational concepts first, then specifics)

                OUTPUT FORMAT (respond with valid JSON):
                {{
                    "needs_breakdown": true/false,
                    "reasoning": "Brief explanation of whether this needs breakdown and why",
                    "sub_questions": [
                        "Sub-question 1",
                        "Sub-question 2",
                        "Sub-question 3"
                    ]
                }}

                If the question is simple and doesn't need breakdown (like "What is AI?"), set needs_breakdown to false and provide an empty list.
                If the question is complex (like comparisons, "how does X work", deep dives), set needs_breakdown to true and provide 3-5 sub-questions.

                Respond with ONLY the JSON, no other text.
                """

        try:
            response_text = self.llm.generate(prompt, temperature=0.7).strip()

            if response_text.startswith("```"):
                start = response_text.find("{")
                end = response_text.rfind("}")
                if start != -1 and end != -1:
                    response_text = response_text[start : end + 1]

            plan = json.loads(response_text)

            return {
                "main_query": query,
                "needs_breakdown": plan.get("needs_breakdown", False),
                "reasoning": plan.get("reasoning", ""),
                "sub_questions": plan.get("sub_questions", []),
                "success": True,
            }

        except json.JSONDecodeError as e:
            return {
                "main_query": query,
                "needs_breakdown": False,
                "reasoning": f"Failed to parse plan: {str(e)}",
                "sub_questions": [],
                "success": False,
                "error": "JSON parsing failed",
            }
        except Exception as e:
            return {
                "main_query": query,
                "needs_breakdown": False,
                "reasoning": f"Error creating plan: {str(e)}",
                "sub_questions": [],
                "success": False,
                "error": str(e),
            }

    def should_break_down(self, query: str) -> bool:
        """
        Quick check if a query needs to be broken down

        Args:
            query: The research question

        Returns:
            bool: True if needs breakdown, False otherwise
        """
        complex_keywords = [
            "compare",
            "difference",
            "vs",
            "versus",
            "how does",
            "how do",
            "explain",
            "pros and cons",
            "advantages and disadvantages",
            "better",
            "best",
            "relationship between",
            "impact of",
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in complex_keywords)
