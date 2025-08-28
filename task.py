"""
task.py - core analysis task for financial documents.
This module exposes analyze_financial_document which takes a file path and returns JSON results.
"""

from typing import Dict, Any
from tools import extract_text_from_pdf
from agents import financial_analyst
import re, json

def analyze_financial_document(file_path: str) -> Dict[str, Any]:
    # Extract text from PDF
    text = extract_text_from_pdf(file_path)
    cleaned = " ".join(text.split())

    # --- Deterministic regex-based extraction ---
    metrics = {}
    number = r"\(?-?[\d,]+(?:\.\d+)?\)?"
    patterns = {
        "revenue": [r"revenue[:\s]*" + number, r"total revenue[:\s]*" + number],
        "net_income": [r"net income[:\s]*" + number, r"net loss[:\s]*" + number],
        "eps": [r"eps[:\s]*" + number, r"earnings per share[:\s]*" + number],
        "operating_income": [r"operating income[:\s]*" + number],
    }

    for key, pats in patterns.items():
        for pat in pats:
            m = re.search(pat, cleaned, re.IGNORECASE)
            if m:
                # take only the numeric value
                val = re.search(number, m.group(0))
                if val:
                    metrics[key] = val.group(0).replace(",", "").strip("()")
                break
        # If metric not found, set null
        if key not in metrics:
            metrics[key] = None

    # --- Improved prompt for LLM/agent ---
    prompt = f"""
You are a financial analyst. 
Analyze the following financial document text and return JSON only with the keys:
- summary: 2-3 sentence overview
- metrics: {{ revenue, net_income, operating_income, eps }}
- recommendation: short risk/opportunity note

If a metric is missing, use null.
Ensure output is valid JSON only.

Text:
{text[:4000]}
"""

    try:
        response = financial_analyst(prompt=prompt, context=text)
        # Parse JSON only if response is a string
        if isinstance(response, str):
            insights = json.loads(response)
        else:
            insights = response
    except Exception as e:
        # Fallback if agent fails
        insights = {
            "summary": text[:300] + "...",
            "metrics": metrics,
            "recommendation": "Fallback: deterministic extraction only.",
            "error": str(e)
        }

    return {
        "file": file_path,
        "metrics": metrics,
        "insights": insights
    }
