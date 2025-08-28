"""
agents.py - Lightweight financial analysis agents.
Provides financial_analyst() which can use LLM (if API key available) or a fallback rule-based summary.
"""

import os
import json
from typing import Any, Dict

# Try to import OpenAI
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    HAS_OPENAI = True if os.getenv("OPENAI_API_KEY") else False
except ImportError:
    HAS_OPENAI = False


def financial_analyst(prompt: str, context: str = "") -> Dict[str, Any]:
    """
    Runs a financial analysis agent.
    If OPENAI_API_KEY is set, it queries OpenAI with the given prompt.
    Otherwise, returns a simple fallback analysis.
    """
    if HAS_OPENAI:
        try:
            # Call OpenAI chat model
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Return only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            output = response.choices[0].message.content.strip()

            # Ensure valid JSON
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return {"summary": output, "note": "Output was not valid JSON."}

        except Exception as e:
            return {"summary": context[:300], "note": f"LLM call failed: {e}"}

    # --- Fallback: No API key ---
    return {
        "summary": context[:300] + "...",
        "metrics": {},
        "recommendation": "No API key provided. Using fallback analysis."
    }
