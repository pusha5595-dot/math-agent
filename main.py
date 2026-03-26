import time
import os
import config
from auth_manager import authenticate
from drive_manager import get_or_create_folder, list_pdf_files, download_pdf, move_file
from gemini_extractor import extract_pdf_data
from docs_generator import create_google_doc, generate_doc_from_data

def process_pdfs():
    print("Initiating Math PDF pipeline...")
    
    # 1. Authenticate to Google APIs
    drive_service, docs_service = authenticate()
    
    # 2. Setup/Find Folders
    print("Locating necessary Drive folders...")
    input_folder_id = config.INPUT_FOLDER_ID
    docs_folder_id = config.DOCS_FOLDER_ID
    processed_folder_id = get_or_create_folder(drive_service, config.PROCESSED_FOLDER_NAME, parent_id=input_folder_id)
    
    print(f"Monitoring folder ID: {input_folder_id}")
    
    # 3. List unprocessed PDFs
    pdfs = list_pdf_files(drive_service, input_folder_id)
    if not pdfs:
        print("No new PDFs found. Waiting for next cycle.")
        return
        
    print(f"Found {len(pdfs)} PDF(s) to process.")
    
    for pdf in pdfs:
        try:
            file_id = pdf['id']
            file_name = pdf['name']
            print(f"\n--- Processing {file_name} ---")
            
            # 4. Download PDF
            local_path = download_pdf(drive_service, file_id, file_name)
            
            # 5. Extract Data using Gemini
            extraction_result = extract_pdf_data(local_path)
            
            # 6. Create Google Doc
            doc_title = f"{file_name.replace('.pdf', '')} - Extracted Math"
            print(f"Creating Google Doc: {doc_title}...")
            doc_id = create_google_doc(docs_service, doc_title, docs_folder_id, drive_service)
            
            # 7. Populate Google Doc
            print("Populating doc with extracted text and Unicode math...")
            generate_doc_from_data(docs_service, doc_id, extraction_result)
            
            print(f"Success! Document created at: https://docs.google.com/document/d/{doc_id}/edit")
            
            # 8. Move PDF to Processed
            print(f"Moving {file_name} to Processed folder...")
            move_file(drive_service, file_id, input_folder_id, processed_folder_id)
            
            # Cleanup local file
            if os.path.exists(local_path):
                os.remove(local_path)
                
            print("--- Finished ---")
            
            # Delay between PDFs to protect Free Tier RPM limits
            print("Waiting 5 seconds to prevent Google AI Studio rate limits...")
            time.sleep(5)
            
        except Exception as e:
            print(f"Error processing {pdf.get('name')}: {str(e)}")

def main():
    if not os.path.exists(".env"):
        print("ERROR: A .env file is required but was not found. Please create one with GEMINI_API_KEY=your_key")
        return
        
    print("Application started. Press Ctrl+C to stop.")
    try:
        while True:
            process_pdfs()
            # Wait 60 seconds before checking again
            print("\nSleeping for 60 seconds...\n")
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nAgent stopped by user.")

if __name__ == '__main__':
    main()
