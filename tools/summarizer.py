"""
Summarization Tool using Groq LLM
"""
from groq import Groq
from schemas import SummaryOutput
import config
import json


def summarize_text(text: str, context: str = "search results") -> SummaryOutput:
    """
    Summarize text using Groq LLM with structured output
    
    Args:
        text: Text to summarize
        context: Context of what's being summarized
        
    Returns:
        SummaryOutput with key points, main topic, and confidence
    """
    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in environment variables")
    
    client = Groq(api_key=config.GROQ_API_KEY)
    
    prompt = f"""Analyze and summarize the following {context}:

{text}

Extract:
1. Key points (3-5 most important facts)
2. Main topic
3. Your confidence in the summary (high/medium/low)

Return ONLY a JSON object with this structure:
{{
    "key_points": ["point 1", "point 2", ...],
    "main_topic": "main topic here",
    "confidence": "high/medium/low"
}}"""
    
    try:
        response = client.chat.completions.create(
            model=config.GROQ_STRUCTURED_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise summarization assistant. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=1024
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract JSON from potential markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        summary_data = json.loads(content)
        return SummaryOutput(**summary_data)
    
    except Exception as e:
        print(f"⚠️  Summarization error: {e}")
        # Return a fallback summary
        return SummaryOutput(
            key_points=["Summarization failed - using raw text"],
            main_topic=context,
            confidence="low"
        )
