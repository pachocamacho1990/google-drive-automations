"""Bulk modify labels on all files in a Google Drive folder."""

import sys
import os
import argparse
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from googleapiclient.discovery import build
from utilities import authenticate, get_labels_catalog, resolve_name_to_id, resolve_path_to_folder_id, list_files_in_folder

SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.labels"]
SHARED_DRIVE_ID = "0ACLtKHNaf3uMUk9PVA"  # Hardcoded for now as per project convention

def modify_label(service, file_id, label_id, field_id, choice_id):
    """
    Apply or update a selection-based label on a file.
    """
    body = {
        "labelModifications": [
            {
                "labelId": label_id,
                "fieldModifications": [
                    {
                        "fieldId": field_id,
                        "setSelectionValues": [choice_id]
                    }
                ]
            }
        ]
    }

    try:
        service.files().modifyLabels(fileId=file_id, body=body).execute()
        return True
    except Exception as e:
        print(f"  ❌ Error modifying {file_id}: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bulk modify labels on all files in a folder.')
    parser.add_argument('folder_path', help='Path to the folder (e.g., "Jeeves/2025/sep")')
    parser.add_argument('label_name_or_id', help='The Name or ID of the label to apply')
    parser.add_argument('field_name_or_id', help='The Name or ID of the field to set')
    parser.add_argument('choice_name_or_id', help='The Name or ID of the selection choice')

    args = parser.parse_args()

    # 1. Authenticate
    print("Authenticating...")
    creds = authenticate(SCOPES)
    drive_service = build("drive", "v3", credentials=creds)
    labels_service = build("drivelabels", "v2", credentials=creds)

    # 2. Resolve Folder
    print(f"Resolving folder path: '{args.folder_path}'...")
    try:
        folder_id = resolve_path_to_folder_id(drive_service, SHARED_DRIVE_ID, args.folder_path)
        print(f"  -> Found Folder ID: {folder_id}")
    except Exception as e:
        print(f"❌ Error resolving folder: {e}")
        sys.exit(1)

    # 3. Resolve Label/Field/Choice
    print("Fetching label catalog...")
    catalog = get_labels_catalog(labels_service)
    
    print(f"Resolving label details...")
    label_id = resolve_name_to_id(catalog, args.label_name_or_id, "label")
    label_info = catalog[label_id]
    
    fields_dict = label_info.get('fields', {})
    field_id = resolve_name_to_id(fields_dict, args.field_name_or_id, "field", fields_dict)
    field_info = fields_dict[field_id]
    
    choices_dict = field_info.get('choices', {})
    if not choices_dict:
         print(f"❌ Field '{field_info['displayName']}' does not appear to be a selection field.")
         sys.exit(1)
    choice_id = resolve_name_to_id(choices_dict, args.choice_name_or_id, "choice", choices_dict)
    choice_info = choices_dict[choice_id]

    print(f"  -> Target: Label='{label_info['displayName']}', Field='{field_info['displayName']}', Value='{choice_info['displayName']}'")

    # 4. List Files
    print(f"Listing files in folder...")
    files = list_files_in_folder(drive_service, SHARED_DRIVE_ID, folder_id)
    print(f"  -> Found {len(files)} files.")

    if not files:
        print("No files to update.")
        sys.exit(0)

    # 5. Apply Updates
    print(f"\nStarting bulk update on {len(files)} files...")
    success_count = 0
    
    for i, file in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Updating '{file['name']}'...", end='', flush=True)
        if modify_label(drive_service, file['id'], label_id, field_id, choice_id):
            print(" ✅")
            success_count += 1
        else:
            print(" ❌")

    print(f"\n✅ Completed! Successfully updated {success_count}/{len(files)} files.")
