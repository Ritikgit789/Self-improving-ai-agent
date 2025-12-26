"""
Planner Agent - Creates step-by-step research plans
"""
from groq import Groq
from typing import List, Optional
from schemas import ResearchPlan, PlanStep, LearningRule
import config
import json


class PlannerAgent:
    """
    Agent responsible for planning research steps.
    Accepts learned constraints to improve planning over time.
    """
    
    def __init__(self):
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set")
        
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.learned_rules: List[LearningRule] = []
    
    def inject_learning(self, rules: List[LearningRule]):
        """Inject learned rules that modify planning behavior"""
        self.learned_rules = [r for r in rules if r.applies_to == "planning"]
    
    def create_plan(self, question: str) -> ResearchPlan:
        """
        Create a research plan for answering a question
        
        Args:
            question: The research question to answer
            
        Returns:
            ResearchPlan with steps and tool requirements
        """
        # Build constraints from learned rules
        constraints = ""
        if self.learned_rules:
            constraints = "\n\n🧠 LEARNED CONSTRAINTS (follow these strictly):\n"
            for rule in sorted(self.learned_rules, key=lambda r: r.priority, reverse=True):
                constraints += f"- {rule.rule_text}\n"
        
        # Progressive prompt strengthening based on runs + learning
        # Runs 1-2: Very weak (fails consistently)
        # Runs 3-4: Medium (+ learned rules)
        # Runs 5+: Strong (+ all learned rules)
        
        # Get run count from memory
        from memory import MistakeStore
        stats = MistakeStore().get_stats()
        run_count = stats['total_runs']
        
        has_learned = len(self.learned_rules) > 0
        
        # Determine prompt strength level
        if run_count < 2:
            # VERY WEAK - Almost no guidance
            prompt = f"""Question: {question}

You likely know this already. Create a quick 1-step plan.

Return JSON: {{\"question\": \"{question}\", \"steps\": [{{\"step_number\": 1, \"description\": \"answer\", \"tool_required\": null, \"reasoning\": \"know it\"}}], \"estimated_time\": \"instant\"}}"""
            
        elif run_count < 4:
            # WEAK - Mentions tools but doesn't require them
            prompt = f"""Question: {question}

Create a plan. You can use web_search or summarize if needed, or answer directly.

{constraints if has_learned else ""}

Return JSON: {{\"question\": \"{question}\", \"steps\": [{{\"step_number\": 1, \"description\": \"step\", \"tool_required\": \"tool or null\", \"reasoning\": \"why\"}}], \"estimated_time\": \"1 min\"}}"""
            
        else:
            # STRONG - Explicit requirements + learned rules
            prompt = f"""You are an expert research planning assistant.

TASK: Create a step-by-step plan to answer: "{question}"

AVAILABLE TOOLS:
- web_search: Search the web for information
- summarize: Extract key information from search results

{constraints}

{("IMPORTANT: Follow the learned constraints above strictly." if has_learned else "")}

Return a JSON plan with this structure:
{{
    "question": "the question",
    "steps": [
        {{
            "step_number": 1,
            "description": "what to do",
            "tool_required": "tool_name or null",
            "reasoning": "why needed"
        }}
    ],
    "estimated_time": "estimate"
}}

Create 3-5 steps. Return ONLY valid JSON."""
        
        try:
            # Adaptive system message based on learning
            system_msg = ("You are a research planning expert. Always return valid JSON. Follow learned constraints strictly." 
                         if has_learned 
                         else "You are a helpful assistant. Return valid JSON.")
            
            response = self.client.chat.completions.create(
                model=config.GROQ_STRUCTURED_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_msg
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=config.GROQ_TEMPERATURE,
                max_tokens=config.GROQ_MAX_TOKENS
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            plan_data = json.loads(content)
            return ResearchPlan(**plan_data)
        
        except Exception as e:
            print(f"⚠️  Planning error: {e}")
            # Return a minimal fallback plan
            return ResearchPlan(
                question=question,
                steps=[
                    PlanStep(
                        step_number=1,
                        description="Answer based on general knowledge",
                        tool_required=None,
                        reasoning="Fallback due to planning error"
                    )
                ],
                estimated_time="1 minute"
            )
