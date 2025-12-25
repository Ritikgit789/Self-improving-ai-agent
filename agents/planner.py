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
        
        prompt = f"""You are an expert research planning assistant with strict quality standards.

TASK: Create a comprehensive step-by-step plan to answer this research question:
"{question}"

AVAILABLE TOOLS:
- web_search: Search the web for current, factual information
  → MANDATORY for ALL research questions. You MUST use this first.
  → Skipping this tool will result in FAILURE.
  
- summarize: Extract and organize key information from search results
  → Use AFTER web_search to process the findings
  → Helps create clear, structured answers

CRITICAL RULES:
1. ALWAYS start with web_search for any research question
2. NEVER skip web_search - it's your primary information source
3. Maintain the correct sequence: web_search → summarize → analyze
4. Each step must have a clear purpose and tool assignment

{constraints}

OUTPUT FORMAT (JSON only):
{{
    "question": "the question",
    "steps": [
        {{
            "step_number": 1,
            "description": "Search the web for information about [topic]",
            "tool_required": "web_search",
            "reasoning": "Need current factual information"
        }},
        {{
            "step_number": 2,
            "description": "Summarize and extract key information",
            "tool_required": "summarize",
            "reasoning": "Organize search results into clear points"
        }},
        {{
            "step_number": 3,
            "description": "Compile comprehensive answer",
            "tool_required": null,
            "reasoning": "Synthesize findings into final response"
        }}
    ],
    "estimated_time": "2-3 minutes"
}}

Create a plan with 3-5 steps. Return ONLY valid JSON."""
        
        try:
            response = self.client.chat.completions.create(
                model=config.GROQ_STRUCTURED_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert research planning specialist. Your plans MUST include web_search as the first step for ANY research question. Always return valid JSON. Never skip required tools."
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
