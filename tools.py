"""
tools.py - helper utilities for extracting text from PDFs and simple parsing.
"""
from typing import Tuple
from PyPDF2 import PdfReader

def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    pages = []
    for p in reader.pages:
        try:
            pages.append(p.extract_text() or "")
        except Exception:
            # older PyPDF2 may throw on some pages; skip safely
            pages.append("")
    return "\n".join(pages)
