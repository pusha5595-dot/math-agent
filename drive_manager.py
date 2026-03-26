import io
from googleapiclient.http import MediaIoBaseDownload

def get_or_create_folder(drive_service, folder_name, parent_id=None):
    """Finds a folder by name, or creates it if it doesn't exist."""
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
        
    results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    
    if not items:
        # Create folder
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = drive_service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
    else:
        return items[0].get('id')

def list_pdf_files(drive_service, folder_id):
    """Lists all PDF files in the specified folder."""
    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    return results.get('files', [])

def download_pdf(drive_service, file_id, file_name, download_path='.'):
    """Downloads a file from Google Drive."""
    request = drive_service.files().get_media(fileId=file_id)
    file_path = f"{download_path}/{file_name}"
    
    with io.FileIO(file_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Downloading {file_name} {int(status.progress() * 100)}%.")
            
    return file_path

def move_file(drive_service, file_id, origin_folder_id, dest_folder_id):
    """Move a file from one folder to another."""
    # Retrieve the existing parents to remove
    file = drive_service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))
    
    # Move the file to the new folder
    updated_file = drive_service.files().update(
        fileId=file_id,
        addParents=dest_folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()
    
    return updated_file
