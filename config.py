"""
Configuration settings for the Self-Improving AI Research Agent
"""
import os
from pathlib import Path

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"  # Fast, efficient model for planning/execution
GROQ_TEMPERATURE = 0.7
GROQ_MAX_TOKENS = 2048

# Model for structured outputs (more reliable for JSON)
GROQ_STRUCTURED_MODEL = "llama-3.3-70b-versatile"

# Tool Configuration
WEB_SEARCH_MAX_RESULTS = 5
SUMMARIZATION_MAX_LENGTH = 500

# Memory Configuration
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
MISTAKES_FILE = DATA_DIR / "mistakes.json"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Evaluation Criteria
REQUIRED_TOOLS = ["web_search"]  # Must be used for research tasks
CORRECT_SEQUENCE = ["web_search", "summarize"]  # Preferred order

# Learning Configuration
MAX_MISTAKES_STORED = 100
MISTAKE_FREQUENCY_THRESHOLD = 2  # Pattern detected after 2+ occurrences
