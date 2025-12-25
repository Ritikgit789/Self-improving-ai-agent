"""
Self-Improving AI Research Agent
Main application orchestrating the learning loop
"""
import sys
import os
from dotenv import load_dotenv
from colorama import init, Fore, Style
import argparse

# Load environment variables
load_dotenv()

# Initialize colorama for Windows
init(autoreset=True)

from agents import PlannerAgent, ExecutorAgent, EvaluatorAgent, LearnerAgent
from memory import MistakeStore, BehaviorModifier
import config


class ResearchAgent:
    """
    Self-improving research agent that learns from mistakes
    """
    
    def __init__(self, mistake_probability: float = 0.0, auto_learning_mode: bool = True):
        """
        Args:
            mistake_probability: Probability of making mistakes (for demonstration)
            auto_learning_mode: If True, automatically adjust mistake rate for first few runs
        """
        # Check API key
        if not config.GROQ_API_KEY:
            print(f"{Fore.RED}❌ ERROR: GROQ_API_KEY not found in environment variables{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please create a .env file with your Groq API key:{Style.RESET_ALL}")
            print(f"   GROQ_API_KEY=your_key_here")
            print(f"\nGet your key from: https://console.groq.com/keys")
            sys.exit(1)
        
        # Initialize memory first to check run count
        self.memory = MistakeStore()
        
        # Auto-adjust mistake probability for demonstration
        if auto_learning_mode and mistake_probability == 0.0:
            stats = self.memory.get_stats()
            total_runs = stats['total_runs']
            
            # First 3 runs: High mistake rate to demonstrate learning
            if total_runs < 3:
                mistake_probability = 0.6  # 60% chance of mistakes
                print(f"{Fore.YELLOW}🎓 Learning Mode: Run {total_runs + 1}/3 - Will make mistakes to learn{Style.RESET_ALL}\n")
            elif total_runs < 5:
                mistake_probability = 0.3  # 30% chance
                print(f"{Fore.YELLOW}🎓 Learning Mode: Run {total_runs + 1}/5 - Reducing mistake rate{Style.RESET_ALL}\n")
            else:
                mistake_probability = 0.0  # No forced mistakes
        
        # Initialize agents
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent(mistake_probability=mistake_probability)
        self.evaluator = EvaluatorAgent()
        self.learner = LearnerAgent()
        
        # Initialize behavior modifier
        self.behavior_modifier = BehaviorModifier()
        
        # Load learned rules
        self._apply_learning()
    
    def _apply_learning(self):
        """Load mistakes from memory and inject into planner"""
        snapshot = self.memory.load()
        
        if snapshot.mistakes:
            rules = self.behavior_modifier.generate_constraints(snapshot.mistakes)
            self.planner.inject_learning(rules)
            
            print(f"{Fore.CYAN}🧠 Loaded {len(snapshot.mistakes)} mistakes from memory{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Applied {len(rules)} learning rules to planner{Style.RESET_ALL}\n")
    
    def research(self, question: str) -> dict:
        """
        Run complete research loop: Plan → Execute → Evaluate → Learn
        
        Args:
            question: Research question to answer
            
        Returns:
            Dict with results and learning status
        """
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🔬 RESEARCH QUESTION:{Style.RESET_ALL} {question}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        # Step 1: Plan
        print(f"{Fore.YELLOW}📋 STEP 1: PLANNING{Style.RESET_ALL}")
        plan = self.planner.create_plan(question)
        
        print(f"\nPlan created with {len(plan.steps)} steps:")
        for step in plan.steps:
            tool_info = f"[{step.tool_required}]" if step.tool_required else "[no tool]"
            print(f"  {step.step_number}. {step.description} {Fore.BLUE}{tool_info}{Style.RESET_ALL}")
        
        # Step 2: Execute
        print(f"\n{Fore.YELLOW}⚙️  STEP 2: EXECUTION{Style.RESET_ALL}")
        trace = self.executor.execute_plan(plan)
        
        print(f"\n{Fore.GREEN}💡 FINAL ANSWER:{Style.RESET_ALL}")
        print(f"{trace.final_answer}\n")
        
        # Step 3: Evaluate
        print(f"{Fore.YELLOW}📊 STEP 3: EVALUATION{Style.RESET_ALL}")
        evaluation = self.evaluator.evaluate(trace)
        
        print(f"\n{evaluation.feedback}")
        print(f"Score: {evaluation.score:.1%}")
        print(f"✓ Required tools used: {evaluation.required_tools_used}")
        print(f"✓ Correct sequence: {evaluation.correct_sequence_followed}")
        print(f"✓ Answer supported: {evaluation.answer_supported_by_data}")
        
        # Step 4: Learn (if failed)
        learned_something = False
        if not evaluation.passed:
            print(f"\n{Fore.YELLOW}🧠 STEP 4: LEARNING FROM MISTAKES{Style.RESET_ALL}")
            mistakes = self.learner.analyze_failure(trace, evaluation)
            
            if mistakes:
                print(f"\nIdentified {len(mistakes)} mistake(s):")
                for mistake in mistakes:
                    print(f"  • {Fore.RED}{mistake.mistake_type}{Style.RESET_ALL}: {mistake.description}")
                    print(f"    → Learning: {Fore.GREEN}{mistake.corrective_rule}{Style.RESET_ALL}")
                
                # Save to memory
                self.memory.add_mistakes(mistakes)
                learned_something = True
                
                print(f"\n{Fore.GREEN}✓ Mistakes saved to memory{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}✓ No mistakes detected - execution was successful!{Style.RESET_ALL}")
        
        # Update statistics
        self.memory.update_stats(success=evaluation.passed)
        
        # Show learning progress
        stats = self.memory.get_stats()
        print(f"\n{Fore.CYAN}📈 LEARNING PROGRESS:{Style.RESET_ALL}")
        print(f"   Total runs: {stats['total_runs']}")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        print(f"   Patterns learned: {stats['recurring_patterns']}")
        
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        return {
            "question": question,
            "answer": trace.final_answer,
            "passed": evaluation.passed,
            "score": evaluation.score,
            "learned": learned_something,
            "stats": stats
        }


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Self-Improving AI Research Agent"
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Research question to answer"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demonstration showing learning progression"
    )
    parser.add_argument(
        "--clear-memory",
        action="store_true",
        help="Clear all learned mistakes"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show learning statistics"
    )
    parser.add_argument(
        "--mistake-rate",
        type=float,
        default=0.0,
        help="Probability of making mistakes (0.0-1.0, for demonstration)"
    )
    
    args = parser.parse_args()
    
    # Clear memory if requested
    if args.clear_memory:
        store = MistakeStore()
        store.clear()
        print(f"{Fore.GREEN}✓ Memory cleared{Style.RESET_ALL}")
        return
    
    # Show stats if requested
    if args.stats:
        store = MistakeStore()
        stats = store.get_stats()
        print(f"\n{Fore.CYAN}📊 LEARNING STATISTICS{Style.RESET_ALL}")
        print(f"Total runs: {stats['total_runs']}")
        print(f"Successful: {stats['successful_runs']}")
        print(f"Failed: {stats['failed_runs']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Total mistakes recorded: {stats['total_mistakes']}")
        print(f"Recurring patterns: {stats['recurring_patterns']}\n")
        return
    
    # Run demo
    if args.demo:
        run_demo()
        return
    
    # Check if question provided
    if not args.question:
        parser.print_help()
        return
    
    # Run research
    agent = ResearchAgent(mistake_probability=args.mistake_rate)
    agent.research(args.question)


def run_demo():
    """
    Run demonstration showing learning progression
    """
    print(f"\n{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}🎓 SELF-IMPROVING AGENT DEMONSTRATION{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}\n")
    
    print("This demo shows how the agent learns from mistakes.\n")
    print(f"{Fore.YELLOW}Phase 1:{Style.RESET_ALL} Agent will make mistakes (high error rate)")
    print(f"{Fore.YELLOW}Phase 2:{Style.RESET_ALL} Agent learns from failures")
    print(f"{Fore.YELLOW}Phase 3:{Style.RESET_ALL} Agent performs better (lower error rate)\n")
    
    input(f"{Fore.CYAN}Press Enter to start...{Style.RESET_ALL}")
    
    # Clear memory for fresh demo
    store = MistakeStore()
    store.clear()
    
    questions = [
        "What is the capital of France?",
        "What is the population of Tokyo?",
        "Who invented the telephone?"
    ]
    
    # Phase 1: High mistake rate
    print(f"\n{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}PHASE 1: INITIAL RUNS (Making Mistakes){Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    
    agent_v1 = ResearchAgent(mistake_probability=0.7)  # 70% chance of mistakes
    
    for question in questions[:2]:
        agent_v1.research(question)
        input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}\n")
    
    # Phase 2: Learning
    print(f"\n{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}📚 LEARNING PHASE{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}\n")
    
    snapshot = store.load()
    print(f"Mistakes in memory: {len(snapshot.mistakes)}\n")
    
    for mistake in snapshot.mistakes:
        print(f"  • {Fore.RED}{mistake.mistake_type}{Style.RESET_ALL}")
        print(f"    Rule: {mistake.corrective_rule}")
        print(f"    Frequency: {mistake.frequency}\n")
    
    input(f"{Fore.CYAN}Press Enter to see improved performance...{Style.RESET_ALL}\n")
    
    # Phase 3: Improved performance
    print(f"\n{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}PHASE 3: IMPROVED RUNS (Learning Applied){Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    
    agent_v2 = ResearchAgent(mistake_probability=0.2)  # 20% chance of mistakes
    
    for question in questions[2:]:
        agent_v2.research(question)
        input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}\n")
    
    # Final stats
    print(f"\n{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}📊 FINAL STATISTICS{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}\n")
    
    stats = store.get_stats()
    print(f"Total runs: {stats['total_runs']}")
    print(f"Success rate: {Fore.GREEN}{stats['success_rate']:.1f}%{Style.RESET_ALL}")
    print(f"Patterns learned: {stats['recurring_patterns']}")
    
    print(f"\n{Fore.GREEN}✓ Demo complete! The agent has learned from its mistakes.{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
