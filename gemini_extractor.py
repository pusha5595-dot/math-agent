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
    options: List[str] = Field(default=[], description="The 4 options for the question, converted to Unicode.")
    correct_answer: str = Field(default="", description="The correct option from the choices provided.")
    explanation: str = Field(default="", description="The detailed, exact explanation and solution for the question, strictly using Unicode math.")

class ExtractionResult(BaseModel):
    exam_name: Optional[str] = Field(description="Name of the exam, if identifiable from the document headers/footers.")
    questions: List[QuestionModel] = Field(description="List of extracted questions.")

def _extract_chunk(pdf_path: str) -> ExtractionResult:
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
                    max_output_tokens=8192, # Max length allowed to pull all 100+ questions
                )
            )
            
            # Extract text (handling markdown wrappers if mistakenly provided)
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            import json_repair
            data = json_repair.loads(raw_text.strip())
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

def extract_pdf_data(pdf_path: str) -> ExtractionResult:
    """Splits massive PDFs into small 5-page chunks, processes them, and stitches the full JSON array together."""
    from PyPDF2 import PdfReader, PdfWriter
    import os
    import time
    
    print(f"Checking massive PDF scale: {pdf_path}...")
    try:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
    except Exception as e:
        print(f"Failed to read chunks. Reverting to single bulk extraction. Error: {e}")
        return _extract_chunk(pdf_path)
        
    chunk_size = 5 # Extracts 5 pages at a time to conquer token limits
    
    # If the PDF is already small enough, skip chunking to save time
    if total_pages <= chunk_size:
        return _extract_chunk(pdf_path)
        
    print(f"Auto-Splitter Engaged: Slicing {total_pages} page PDF into chunks of {chunk_size} pages...")
        
    all_questions = []
    exam_name = None
    
    # Process each PDF chunk seamlessly
    for i in range(0, total_pages, chunk_size):
        writer = PdfWriter()
        end = min(i + chunk_size, total_pages)
        for j in range(i, end):
            writer.add_page(reader.pages[j])
            
        chunk_filename = f"{pdf_path}_chunk_{i//chunk_size}.pdf"
        with open(chunk_filename, "wb") as f:
            writer.write(f)
            
        print(f"Dispatching chunk {i//chunk_size + 1}: Pages {i+1} to {end}...")
        try:
            chunk_result = _extract_chunk(chunk_filename)
            if chunk_result:
                all_questions.extend(chunk_result.questions)
                if not exam_name and chunk_result.exam_name:
                    exam_name = chunk_result.exam_name
        except Exception as e:
            print(f"Error processing chunk {i//chunk_size + 1}: {e}")
            
        # Hard cleanup
        if os.path.exists(chunk_filename):
            os.remove(chunk_filename)
            
        # Protect RPM quotas between chunks
        time.sleep(8)
        
    print(f"Stitch Complete! United {len(all_questions)} total questions from {total_pages} pages into one master JSON.")
    return ExtractionResult(exam_name=exam_name, questions=all_questions)
