"""Download a file from Google Drive (handles binary and Workspace files)."""

import sys
import os
import io
import argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from utilities import authenticate

SCOPES = ["https://www.googleapis.com/auth/drive"]

def download_file(file_id, destination_path=None):
    """
    Download a file from Drive.
    If it's a Google Doc/Sheet/Slide, export to PDF.
    If it's a binary file, download directly.
    """
    creds = authenticate(SCOPES)
    service = build("drive", "v3", credentials=creds)

    try:
        # 1. Get file metadata
        file_metadata = service.files().get(fileId=file_id, fields="id, name, mimeType", supportsAllDrives=True).execute()
        name = file_metadata.get('name')
        mime_type = file_metadata.get('mimeType')
        
        print(f"Found file: '{name}' ({mime_type})")

        # 2. Determine download method
        request = None
        final_name = name
        
        if "application/vnd.google-apps" in mime_type:
            # It's a Google Workspace file, export to PDF
            if "folder" in mime_type:
                print("❌ Cannot download a folder.")
                return False
            
            print("  -> Google Workspace file detected. Exporting to PDF...")
            request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
            if not final_name.lower().endswith('.pdf'):
                final_name += '.pdf'
        else:
            # It's a binary file
            print("  -> Binary file detected. Downloading...")
            request = service.files().get_media(fileId=file_id)

        # 3. Determine destination
        if destination_path:
            if os.path.isdir(destination_path):
                save_path = os.path.join(destination_path, final_name)
            else:
                save_path = destination_path
        else:
            save_path = os.path.join(os.getcwd(), final_name)

        # 4. Execute Download
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if status:
                print(f"  -> Download {int(status.progress() * 100)}%.")

        # 5. Save to disk
        with open(save_path, 'wb') as f:
            f.write(fh.getbuffer())

        print(f"✅ Download complete! Saved to: {save_path}")
        return True

    except Exception as e:
        print(f"❌ Error downloading file: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download a file from Google Drive.')
    parser.add_argument('file_id', help='The ID of the file to download')
    parser.add_argument('--dest', help='Destination path or directory (optional)', default=None)

    args = parser.parse_args()

    download_file(args.file_id, args.dest)
