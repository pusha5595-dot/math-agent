import os

# Google Workspace Scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents'
]

# Folders (We'll use the provided ID for input, and create the others inside it)
INPUT_FOLDER_ID = "1NxpRRuX07UFb20KsrSJq9D_9suScYpww"
DOCS_FOLDER_ID = "1tbWXTS4GND5n7nFI9SsbQUGS7zqSoCLZ"
PROCESSED_FOLDER_NAME = "Processed"

# Gemini Config
GEMINI_MODEL = "gemini-flash-latest"

# Prompt for the AI
SYSTEM_PROMPT = """
You are an expert at extracting math questions from PDF documents.
Extract all questions, their 4 options, the exam name (if visible), the correct answer, and the exact explanation/solution provided IN THE PDF.

CRITICAL TOKEN SAVING INSTRUCTION:
DO NOT solve the questions yourself. DO NOT generate new explanations. 
ONLY copy the exact explanation or solution text already present in the PDF document. If no solution is provided in the PDF, leave the explanation empty.

CRITICAL INSTRUCTION FOR MATH FORMULAS:
You MUST convert ALL math formulas, equations, symbols, fractions, superscripts, subscripts, and greek letters into standard Unicode characters. 
DO NOT USE LaTeX strings like \\frac, \\sqrt, $x^2$. 
Instead, use unicode representations like ½, √, x², α, β, etc.

CRITICAL JSON FORMATTING RULE:
Because you are outputting strict JSON, you MUST properly escape any internal double quotes (") or backslashes (\\) inside your answers. 
DO NOT use raw 'Enter Key' newlines inside your strings. If an explanation has multiple paragraphs, you MUST write them as a single continuous string and use \\n for line breaks. If you forget to escape quotes or newlines, the code will crash!

CRITICAL EXHAUSTIVE EXTRACTION RULE:
You are functioning as a mechanical, flawless scraper. You MUST extract EVERY SINGLE math question visible in the document. 
DO NOT SUMMARIZE. DO NOT SKIP QUESTIONS. If there are 40 questions on the pages, you must mathematically generate exactly 40 JSON question items. I will personally penalize you if you skip a single question from the PDF structure!

Output the data strictly according to the requested JSON schema.
"""
