import os
import json
import streamlit as st
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import config

def authenticate():
    """Authenticates using user OAuth tokens from either Streamlit Secrets or a local file."""
    creds = None
    
    # 1. Cloud Deployment: Try to load the OAuth token from Streamlit Secrets
    try:
        if "google_oauth_token" in st.secrets:
            token_info = dict(st.secrets["google_oauth_token"])
            creds = Credentials.from_authorized_user_info(token_info, config.SCOPES)
    except Exception:
        pass
        
    # 2. Local Fallback: Try to load from the local token.json
    if not creds and os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', config.SCOPES)

    # 3. Refresh or Generate token (Only works locally with credentials.json)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', config.SCOPES)
            creds = flow.run_local_server(port=0)
        # Save token for next time
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Build services
    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)
    
    return drive_service, docs_service

if __name__ == '__main__':
    # Test auth
    print("Testing authentication...")
    drive, docs = authenticate()
    print("Authentication successful!")
