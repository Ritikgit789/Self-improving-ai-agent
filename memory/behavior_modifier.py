"""
Behavior Modifier - Converts mistakes into planning constraints
"""
from typing import List
from schemas import Mistake, LearningRule
from agents.learner import LearnerAgent


class BehaviorModifier:
    """
    Converts learned mistakes into actionable constraints
    that modify agent behavior
    """
    
    def __init__(self):
        self.learner = LearnerAgent()
    
    def generate_constraints(self, mistakes: List[Mistake]) -> List[LearningRule]:
        """
        Generate learning rules from mistakes
        
        Args:
            mistakes: List of mistakes from memory
            
        Returns:
            List of LearningRule objects to inject into planning
        """
        if not mistakes:
            return []
        
        # Use learner to convert mistakes to rules
        rules = self.learner.generate_learning_rules(mistakes)
        
        return rules
    
    def get_planning_reminders(self, rules: List[LearningRule]) -> str:
        """
        Format learning rules as human-readable reminders
        
        Args:
            rules: List of LearningRule objects
            
        Returns:
            Formatted string with reminders
        """
        if not rules:
            return "No learned constraints yet."
        
        planning_rules = [r for r in rules if r.applies_to == "planning"]
        
        if not planning_rules:
            return "No planning constraints yet."
        
        reminders = "🧠 Learned Constraints:\n"
        for i, rule in enumerate(sorted(planning_rules, key=lambda r: r.priority, reverse=True), 1):
            reminders += f"{i}. {rule.rule_text} (priority: {rule.priority})\n"
        
        return reminders
