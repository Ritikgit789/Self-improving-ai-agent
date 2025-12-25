"""
Executor Agent - Executes research plans and can make mistakes
"""
from groq import Groq
from typing import List
from schemas import ResearchPlan, ExecutionTrace, ToolExecution
from tools import search_web, summarize_text, format_search_results
import config
import time
import random


class ExecutorAgent:
    """
    Agent responsible for executing research plans.
    Can intentionally make mistakes in early runs to demonstrate learning.
    """
    
    def __init__(self, mistake_probability: float = 0.0):
        """
        Args:
            mistake_probability: 0.0-1.0, chance of making mistakes (for demonstration)
        """
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set")
        
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.mistake_probability = mistake_probability
    
    def execute_plan(self, plan: ResearchPlan) -> ExecutionTrace:
        """
        Execute a research plan step by step
        
        Args:
            plan: The ResearchPlan to execute
            
        Returns:
            ExecutionTrace with execution details and final answer
        """
        start_time = time.time()
        tools_executed = []
        search_data = ""
        
        print(f"\n📋 Executing plan with {len(plan.steps)} steps...\n")
        
        for step in plan.steps:
            print(f"Step {step.step_number}: {step.description}")
            
            # Simulate mistake: randomly skip required tools
            if step.tool_required == "web_search" and self._should_make_mistake():
                print("  ⚠️  Skipping web search (mistake mode)")
                tools_executed.append(ToolExecution(
                    tool_name="web_search",
                    executed=False,
                    output_summary="Skipped intentionally"
                ))
                continue
            
            # Execute the required tool
            if step.tool_required == "web_search":
                try:
                    results = search_web(plan.question)
                    search_data = format_search_results(results)
                    
                    tools_executed.append(ToolExecution(
                        tool_name="web_search",
                        executed=True,
                        output_summary=f"Found {len(results)} results"
                    ))
                    print(f"  ✓ Web search completed: {len(results)} results")
                
                except Exception as e:
                    tools_executed.append(ToolExecution(
                        tool_name="web_search",
                        executed=False,
                        error=str(e)
                    ))
                    print(f"  ✗ Web search failed: {e}")
            
            elif step.tool_required == "summarize":
                # Simulate mistake: skip summarization sometimes
                if self._should_make_mistake():
                    print("  ⚠️  Skipping summarization (mistake mode)")
                    tools_executed.append(ToolExecution(
                        tool_name="summarize",
                        executed=False,
                        output_summary="Skipped intentionally"
                    ))
                    continue
                
                try:
                    if search_data:
                        summary = summarize_text(search_data, "search results")
                        tools_executed.append(ToolExecution(
                            tool_name="summarize",
                            executed=True,
                            output_summary=f"Extracted {len(summary.key_points)} key points"
                        ))
                        print(f"  ✓ Summarization completed")
                    else:
                        tools_executed.append(ToolExecution(
                            tool_name="summarize",
                            executed=False,
                            output_summary="No data to summarize"
                        ))
                        print("  ⚠️  No data to summarize")
                
                except Exception as e:
                    tools_executed.append(ToolExecution(
                        tool_name="summarize",
                        executed=False,
                        error=str(e)
                    ))
                    print(f"  ✗ Summarization failed: {e}")
            
            else:
                print(f"  → No tool required")
        
        # Generate final answer
        final_answer = self._generate_answer(plan.question, search_data)
        
        execution_time = time.time() - start_time
        
        return ExecutionTrace(
            plan=plan,
            tools_executed=tools_executed,
            final_answer=final_answer,
            execution_time_seconds=execution_time
        )
    
    def _should_make_mistake(self) -> bool:
        """Determine if agent should make a mistake (for demonstration)"""
        return random.random() < self.mistake_probability
    
    def _generate_answer(self, question: str, search_data: str) -> str:
        """Generate final answer using LLM"""
        
        # Simulate mistake: answer without data sometimes
        if not search_data and self._should_make_mistake():
            return self._answer_without_data(question)
        
        context = search_data if search_data else "No search data available"
        
        prompt = f"""You are a professional research assistant. Your task is to provide a comprehensive, factual answer based STRICTLY on the provided search data.

RESEARCH QUESTION:
{question}

SEARCH DATA:
{context}

INSTRUCTIONS:
1. Answer ONLY based on the data provided above
2. Do NOT use prior knowledge or make assumptions
3. If data is insufficient, clearly state: "Based on the provided data, [limited info available]"
4. Structure your answer clearly and concisely
5. Cite key facts from the search results

Provide your evidence-based answer:"""
        
        try:
            response = self.client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional research assistant. Answer questions ONLY based on provided search data. Never fabricate information. Be precise, factual, and cite evidence from the data."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            return f"Error generating answer: {e}"
    
    def _answer_without_data(self, question: str) -> str:
        """Generate answer without search data (demonstrates mistake)"""
        prompt = f"Answer this question briefly: {question}"
        
        try:
            response = self.client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except:
            return "I don't have enough information to answer this question."
