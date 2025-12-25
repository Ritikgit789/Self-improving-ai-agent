"""
Tool Manager - Central registry and executor for all tools
"""
from typing import Dict, Callable, Any, List
from datetime import datetime


class ToolManager:
    """Manages available tools and their execution"""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.execution_log: List[Dict[str, Any]] = []
    
    def register_tool(
        self,
        name: str,
        function: Callable,
        description: str,
        required_for_research: bool = False
    ):
        """Register a tool in the manager"""
        self.tools[name] = {
            "function": function,
            "description": description,
            "required": required_for_research,
            "executions": 0
        }
    
    def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a tool by name with arguments"""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found. Available: {list(self.tools.keys())}")
        
        tool = self.tools[name]
        
        try:
            result = tool["function"](**kwargs)
            tool["executions"] += 1
            
            # Log execution
            self.execution_log.append({
                "tool": name,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "args": kwargs
            })
            
            return result
        
        except Exception as e:
            # Log failure
            self.execution_log.append({
                "tool": name,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "args": kwargs
            })
            raise
    
    def get_tool_description(self, name: str) -> str:
        """Get description of a tool"""
        if name in self.tools:
            return self.tools[name]["description"]
        return "Tool not found"
    
    def list_tools(self) -> List[str]:
        """List all registered tools"""
        return list(self.tools.keys())
    
    def get_required_tools(self) -> List[str]:
        """Get list of tools required for research"""
        return [name for name, tool in self.tools.items() if tool["required"]]
    
    def reset_log(self):
        """Clear execution log"""
        self.execution_log = []
