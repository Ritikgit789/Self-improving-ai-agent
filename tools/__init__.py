"""
Tools module - Contains all tools available to the research agent
"""
from .web_search import search_web, format_search_results
from .summarizer import summarize_text
from .tool_manager import ToolManager

__all__ = ["search_web", "format_search_results", "summarize_text", "ToolManager"]
