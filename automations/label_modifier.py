"""Modify (add/update) a label on a Google Drive file - standalone script."""

import sys
import os
import argparse
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from googleapiclient.discovery import build
from utilities import authenticate, get_labels_catalog

SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.labels"]

def modify_label(file_id, label_id, field_id, choice_id):
    """
    Apply or update a selection-based label on a file.
    
    Args:
        file_id: ID of the file to modify
        label_id: ID of the label to apply
        field_id: ID of the field to set
        choice_id: ID of the selection choice (value)
    """
    creds = authenticate(SCOPES)
    service = build("drive", "v3", credentials=creds)

    # Construct the modification body
    # This structure is specific to the Drive API v3 modifyLabels endpoint
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
        results = service.files().modifyLabels(fileId=file_id, body=body).execute()
        return results
    except Exception as e:
        print(f"Error modifying label: {e}")
        return None

def resolve_name_to_id(catalog, name, type_desc, context_dict=None):
    """
    Resolve a name to an ID using the catalog.
    If name matches an ID directly, return it.
    Otherwise, search for a matching displayName (case-insensitive).
    """
    # 1. Check if it's already an ID (simple heuristic: usually long strings)
    # But we also check if it exists as a key in the context
    search_dict = context_dict if context_dict else catalog
    
    if name in search_dict:
        return name

    # 2. Search by display name
    matches = []
    for id_val, data in search_dict.items():
        if data.get('displayName', '').lower() == name.lower():
            matches.append(id_val)
    
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"❌ Ambiguous {type_desc} name: '{name}'. Matches: {matches}")
        sys.exit(1)
    
    # 3. If no match found, maybe it's an ID that wasn't in the top-level keys 
    # (though for catalog/fields/choices it should be).
    # We'll assume if it looks like an ID, it might be one we missed or raw input.
    # But for safety, if we can't find it by name and it's not a key, we warn.
    print(f"❌ Could not find {type_desc} with name or ID: '{name}'")
    sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Modify a label on a Google Drive file.')
    parser.add_argument('file_id', help='The ID of the file to modify')
    parser.add_argument('label_name_or_id', help='The Name or ID of the label to apply')
    parser.add_argument('field_name_or_id', help='The Name or ID of the field to set')
    parser.add_argument('choice_name_or_id', help='The Name or ID of the selection choice')

    args = parser.parse_args()

    # Authenticate to get catalog
    print("Authenticating and fetching catalog...")
    creds = authenticate(SCOPES)
    labels_service = build("drivelabels", "v2", credentials=creds)
    catalog = get_labels_catalog(labels_service)
    
    # Resolve Label
    print(f"Resolving label '{args.label_name_or_id}'...")
    label_id = resolve_name_to_id(catalog, args.label_name_or_id, "label")
    label_info = catalog[label_id]
    print(f"  -> Found Label: {label_info['displayName']} ({label_id})")

    # Resolve Field
    print(f"Resolving field '{args.field_name_or_id}'...")
    fields_dict = label_info.get('fields', {})
    field_id = resolve_name_to_id(fields_dict, args.field_name_or_id, "field", fields_dict)
    field_info = fields_dict[field_id]
    print(f"  -> Found Field: {field_info['displayName']} ({field_id})")

    # Resolve Choice
    print(f"Resolving choice '{args.choice_name_or_id}'...")
    choices_dict = field_info.get('choices', {})
    if not choices_dict:
         print(f"❌ Field '{field_info['displayName']}' does not appear to be a selection field or has no choices.")
         sys.exit(1)
         
    choice_id = resolve_name_to_id(choices_dict, args.choice_name_or_id, "choice", choices_dict)
    choice_info = choices_dict[choice_id]
    print(f"  -> Found Choice: {choice_info['displayName']} ({choice_id})")

    print(f"\nModifying file {args.file_id}...")
    
    result = modify_label(args.file_id, label_id, field_id, choice_id)
    
    if result:
        print("✅ Label modified successfully!")
        print(json.dumps(result, indent=2))
    else:
        print("❌ Failed to modify label.")
        sys.exit(1)
