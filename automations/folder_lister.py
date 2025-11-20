"""List files in a specific Google Drive folder - standalone script."""

import os
import json
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from googleapiclient.discovery import build
from googleapiclient.discovery import build
from utilities import authenticate, resolve_path_to_folder_id, list_files_in_folder, get_file_labels, get_labels_catalog
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter



SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.labels"
]

# Target Shared Drive ID
SHARED_DRIVE_ID = "0ACLtKHNaf3uMUk9PVA"



def list_folder_files(folder_path):
    """
    List all files in a specific folder path with their labels.

    Args:
        folder_path: Path relative to drive root (e.g., "Reports/2024" or "" for root)

    Returns:
        Dictionary with folder info and list of file metadata with labels
    """
    creds = authenticate(SCOPES)
    drive_service = build("drive", "v3", credentials=creds)
    labels_service = build("drivelabels", "v2", credentials=creds)

    # Get labels catalog once (optimization: single API call)
    print("Loading labels catalog...")
    labels_catalog = get_labels_catalog(labels_service)
    print(f"Loaded {len(labels_catalog)} labels from catalog")

    # Resolve folder path to folder ID
    if folder_path:
        folder_id = resolve_path_to_folder_id(drive_service, SHARED_DRIVE_ID, folder_path)
    else:
        # Empty path means root of shared drive
        folder_id = SHARED_DRIVE_ID

    # List files in the folder
    files = list_files_in_folder(drive_service, SHARED_DRIVE_ID, folder_id)

    # Get labels for each file using the cached catalog
    for file in files:
        file_id = file.get('id')
        if file_id:
            labels = get_file_labels(drive_service, file_id, labels_catalog)
            file['labels'] = labels

    return {
        "folder_path": folder_path or "(root)",
        "folder_id": folder_id,
        "file_count": len(files),
        "files": files
    }

def print_colored_json(data):
    """Print JSON data with syntax highlighting."""
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    colored_json = highlight(json_str, JsonLexer(), TerminalFormatter())
    print(colored_json)

if __name__ == "__main__":
    # Get folder path from command line argument or use root
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        print("Usage: python automations/folder_lister.py <folder_path>")
        print("Example: python automations/folder_lister.py 'Reports/2024'")
        print("Example: python automations/folder_lister.py '' (for root)")
        sys.exit(1)

    try:
        result = list_folder_files(folder_path)
        print_colored_json(result)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
