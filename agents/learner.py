"""
Learner Agent - Analyzes mistakes and generates learning rules
"""
from typing import List
from schemas import (
    EvaluationResult, ExecutionTrace, Mistake, 
    LearningRule, MistakeType
)
from datetime import datetime
import hashlib


class LearnerAgent:
    """
    Agent responsible for analyzing failures and generating
    corrective learning rules.
    """
    
    def analyze_failure(
        self,
        trace: ExecutionTrace,
        evaluation: EvaluationResult
    ) -> List[Mistake]:
        """
        Analyze a failed execution and identify mistakes
        
        Args:
            trace: ExecutionTrace from executor
            evaluation: EvaluationResult from evaluator
            
        Returns:
            List of Mistake objects
        """
        mistakes = []
        
        # Analyze each issue
        for issue in evaluation.issues:
            if "web_search" in issue and "not executed" in issue:
                mistakes.append(self._create_mistake(
                    mistake_type=MistakeType.TOOL_SKIPPED,
                    description=f"Failed to execute web_search for question: {trace.plan.question}",
                    corrective_rule="ALWAYS execute web_search before attempting to answer research questions",
                    question=trace.plan.question
                ))
            
            elif "sequence" in issue.lower():
                mistakes.append(self._create_mistake(
                    mistake_type=MistakeType.WRONG_ORDER,
                    description=f"Tools executed in wrong order for: {trace.plan.question}",
                    corrective_rule="ALWAYS execute web_search BEFORE summarize",
                    question=trace.plan.question
                ))
            
            elif "not supported" in issue.lower():
                # Check if answer was given without data
                web_search_executed = any(
                    t.tool_name == "web_search" and t.executed 
                    for t in trace.tools_executed
                )
                
                if not web_search_executed:
                    mistakes.append(self._create_mistake(
                        mistake_type=MistakeType.PREMATURE_ANSWER,
                        description=f"Answered without gathering data: {trace.plan.question}",
                        corrective_rule="NEVER answer research questions without first executing web_search",
                        question=trace.plan.question
                    ))
                else:
                    mistakes.append(self._create_mistake(
                        mistake_type=MistakeType.UNSUPPORTED_CLAIM,
                        description=f"Answer contradicts search data: {trace.plan.question}",
                        corrective_rule="ALWAYS base answers strictly on search results",
                        question=trace.plan.question
                    ))
        
        return mistakes
    
    def _create_mistake(
        self,
        mistake_type: str,
        description: str,
        corrective_rule: str,
        question: str
    ) -> Mistake:
        """Create a Mistake object"""
        return Mistake(
            mistake_type=mistake_type,
            description=description,
            corrective_rule=corrective_rule,
            question=question,
            timestamp=datetime.now().isoformat()
        )
    
    def generate_learning_rules(self, mistakes: List[Mistake]) -> List[LearningRule]:
        """
        Convert mistakes into actionable learning rules
        
        Args:
            mistakes: List of all mistakes (including recurring ones)
            
        Returns:
            List of LearningRule objects prioritized by frequency
        """
        # Group mistakes by type
        mistake_groups = {}
        for mistake in mistakes:
            if mistake.mistake_type not in mistake_groups:
                mistake_groups[mistake.mistake_type] = []
            mistake_groups[mistake.mistake_type].append(mistake)
        
        rules = []
        
        for mistake_type, group in mistake_groups.items():
            # Use the most recent mistake's rule
            latest = max(group, key=lambda m: m.timestamp)
            
            # Priority based on frequency and severity
            frequency = len(group)
            priority = min(10, 3 + frequency)  # Higher frequency = higher priority
            
            rule_id = self._generate_rule_id(mistake_type)
            
            rules.append(LearningRule(
                rule_id=rule_id,
                rule_text=latest.corrective_rule,
                applies_to="planning",  # Most rules affect planning
                priority=priority
            ))
        
        return sorted(rules, key=lambda r: r.priority, reverse=True)
    
    def _generate_rule_id(self, mistake_type: str) -> str:
        """Generate unique rule ID from mistake type"""
        return hashlib.md5(mistake_type.encode()).hexdigest()[:8]
