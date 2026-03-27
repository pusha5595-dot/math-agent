import os
from pydantic import BaseModel, Field
from typing import List, Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv
import config

load_dotenv()

def get_api_key():
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY")

# Setup GenAI Client
api_key = get_api_key()
client = genai.Client(api_key=api_key)

class QuestionModel(BaseModel):
    question_text: str = Field(description="The full math question text, with all math converted to Unicode.")
    options: List[str] = Field(description="The 4 options for the question, converted to Unicode.")
    correct_answer: str = Field(description="The correct option from the choices provided.")
    explanation: str = Field(description="The detailed, exact explanation and solution for the question, strictly using Unicode math.")

class ExtractionResult(BaseModel):
    exam_name: Optional[str] = Field(description="Name of the exam, if identifiable from the document headers/footers.")
    questions: List[QuestionModel] = Field(description="List of extracted questions.")

def extract_pdf_data(pdf_path: str) -> ExtractionResult:
    """Uploads PDF to Gemini, processes with structured prompt, and returns parsed Pydantic object."""
    print(f"Uploading {pdf_path} to Gemini...")
    pdf_file = client.files.upload(file=pdf_path)
    print("Upload complete. Analyzing document...")

    import time
    import json
    
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=[pdf_file, config.SYSTEM_PROMPT],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractionResult,
                    temperature=0.2, # Low temperature for more deterministic extraction
                )
            )
            
            # Extract text (handling markdown wrappers if mistakenly provided)
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            data = json.loads(raw_text.strip())
            result = ExtractionResult(**data)
            print("Analysis and JSON parsing complete.")
            return result
            
        except Exception as e:
            # Catch quotas (429/503) or strict JSON parsing decode errors (unterminated strings)
            err_msg = str(e).lower()
            if ("429" in err_msg or "error" in err_msg or "expecting" in err_msg or "unterminated" in err_msg or "503" in err_msg) and attempt < 2:
                delay = 10 * (2 ** attempt)
                print(f"Format/API Error caught! Waiting {delay}s before AI retries (Attempt {attempt+1}/3)... Error: {e}")
                time.sleep(delay)
            else:
                raise # Reraise if max attempts reached
