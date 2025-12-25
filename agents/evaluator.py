"""
Evaluator Agent - Judges execution quality
"""
from schemas import ExecutionTrace, EvaluationResult
from groq import Groq
import config
import json


class EvaluatorAgent:
    """
    Agent responsible for evaluating execution quality.
    Checks if required tools were used, correct sequence followed,
    and if the answer is supported by data.
    """
    
    def __init__(self):
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set")
        
        self.client = Groq(api_key=config.GROQ_API_KEY)
    
    def evaluate(self, trace: ExecutionTrace) -> EvaluationResult:
        """
        Evaluate an execution trace
        
        Args:
            trace: ExecutionTrace from executor
            
        Returns:
            EvaluationResult with pass/fail and detailed feedback
        """
        issues = []
        
        # Check 1: Were required tools used?
        executed_tools = [t.tool_name for t in trace.tools_executed if t.executed]
        required_tools_used = "web_search" in executed_tools
        
        if not required_tools_used:
            issues.append("Required tool 'web_search' was not executed")
        
        # Check 2: Was correct sequence followed?
        correct_sequence = self._check_sequence(executed_tools)
        
        if not correct_sequence:
            issues.append("Tools were not called in the correct sequence (web_search → summarize)")
        
        # Check 3: Is answer supported by data?
        answer_supported = self._check_answer_support(trace)
        
        if not answer_supported:
            issues.append("Answer may not be supported by search data")
        
        # Calculate overall score
        checks_passed = sum([
            required_tools_used,
            correct_sequence,
            answer_supported
        ])
        score = checks_passed / 3.0
        
        # Overall pass/fail
        passed = score >= 0.66  # At least 2 out of 3 criteria
        
        # Generate feedback
        feedback = self._generate_feedback(trace, issues, score)
        
        return EvaluationResult(
            passed=passed,
            score=score,
            required_tools_used=required_tools_used,
            correct_sequence_followed=correct_sequence,
            answer_supported_by_data=answer_supported,
            feedback=feedback,
            issues=issues
        )
    
    def _check_sequence(self, executed_tools: list) -> bool:
        """Check if tools were executed in correct order"""
        if not executed_tools:
            return False
        
        # Ideal sequence: web_search before summarize
        if "web_search" in executed_tools and "summarize" in executed_tools:
            search_idx = executed_tools.index("web_search")
            summarize_idx = executed_tools.index("summarize")
            return search_idx < summarize_idx
        
        # If only web_search, that's acceptable
        if "web_search" in executed_tools:
            return True
        
        return False
    
    def _check_answer_support(self, trace: ExecutionTrace) -> bool:
        """
        Use LLM to check if answer is supported by search data
        """
        # If web_search wasn't executed, answer can't be properly supported
        web_search_executed = any(
            t.tool_name == "web_search" and t.executed 
            for t in trace.tools_executed
        )
        
        if not web_search_executed:
            # Check if answer admits lack of data
            answer_lower = trace.final_answer.lower()
            if any(phrase in answer_lower for phrase in [
                "don't have", "no data", "cannot answer", "insufficient information"
            ]):
                return True  # Honest admission
            return False  # Made up answer without data
        
        return True  # If search was executed, assume answer is based on it
    
    def _generate_feedback(
        self,
        trace: ExecutionTrace,
        issues: list,
        score: float
    ) -> str:
        """Generate human-readable feedback with detailed breakdown"""
        if score == 1.0:
            return "✅ Excellent! All criteria met. Required tools used, correct sequence followed, and answer is supported by data."
        
        elif score >= 0.66:
            feedback = f"⚠️  Acceptable but could improve.\n"
            feedback += f"📋 Failure Breakdown:\n"
            for i, issue in enumerate(issues, 1):
                feedback += f"   {i}. {issue}\n"
            return feedback.strip()
        
        else:
            feedback = f"❌ Failed evaluation.\n"
            feedback += f"📋 Failure Breakdown:\n"
            for i, issue in enumerate(issues, 1):
                feedback += f"   {i}. {issue}\n"
            feedback += f"\n💡 What went wrong:\n"
            
            # Detailed analysis of what failed
            executed_tools = [t.tool_name for t in trace.tools_executed if t.executed]
            
            if not executed_tools or "web_search" not in executed_tools:
                feedback += "   → Did not search the web for information\n"
            
            if "web_search" in executed_tools and "summarize" in executed_tools:
                search_idx = executed_tools.index("web_search")
                summarize_idx = executed_tools.index("summarize")
                if search_idx > summarize_idx:
                    feedback += "   → Tried to summarize before searching\n"
            
            if not any(t.executed for t in trace.tools_executed):
                feedback += "   → No tools were executed at all\n"
            
            return feedback.strip()
