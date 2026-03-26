import os
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import config

def authenticate():
    """Shows basic usage of the Drive v3 API with a Service Account."""
    creds = None
    
    # Verify if we are running in Streamlit Cloud where st.secrets is populated
    try:
        if "gcp_service_account" in st.secrets:
            creds_info = dict(st.secrets["gcp_service_account"])
            creds = service_account.Credentials.from_service_account_info(creds_info, scopes=config.SCOPES)
    except Exception:
        pass
        
    # If not loaded from secrets, fallback to local JSON file
    if not creds:
        service_account_file = 'service_account.json'
        if not os.path.exists(service_account_file):
            raise FileNotFoundError(f"Missing {service_account_file}. Please create a Google Service Account in GCP, download the JSON key, and place it in the root directory.")
        creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=config.SCOPES)

    # Build services
    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)
    
    return drive_service, docs_service

if __name__ == '__main__':
    # Test auth
    print("Testing authentication...")
    drive, docs = authenticate()
    print("Authentication successful!")
