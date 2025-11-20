"""
Google Drive API utilities for folder and file operations.
"""

import os
from googleapiclient.discovery import build, Resource
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

FOLDER_MIME = "application/vnd.google-apps.folder"



def authenticate(scopes):
    """
    Handle OAuth2 authentication and return the credentials object.
    
    Args:
        scopes: List of permission scopes required.
        
    Returns:
        Authenticated Credentials object.
    """
    # Navigate to parent directory where token.json lives
    # This handles cases where script is run from different directories
    # We assume utilities.py is in the project root or one level deep, 
    # but credentials are always in project root.
    
    # Find project root by looking for credentials.json
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = current_dir
    
    # Simple heuristic: check if credentials.json is in current dir, if not check parent
    if not os.path.exists(os.path.join(project_root, 'credentials.json')):
        parent_dir = os.path.dirname(current_dir)
        if os.path.exists(os.path.join(parent_dir, 'credentials.json')):
            project_root = parent_dir
            
    token_path = os.path.join(project_root, 'token.json')
    credentials_path = os.path.join(project_root, 'credentials.json')

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds


def get_child_folder_id(service, drive_id, parent_id, child_name):
    """Return the ID of a child folder named `child_name` under `parent_id`."""
    res = service.files().list(
        corpora="drive",
        driveId=drive_id,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        q=(
            f"'{parent_id}' in parents and "
            f"mimeType='{FOLDER_MIME}' and "
            f"name = '{child_name}' and trashed=false"
        ),
        fields="files(id, name, parents)"
    ).execute()
    matches = res.get("files", [])
    if not matches:
        raise FileNotFoundError(f"Folder not found: '{child_name}' under {parent_id}")
    return matches[0]["id"]


def resolve_path_to_folder_id(service, drive_id, path):
    """
    Resolve a nested folder path like 'Reports/2024/April' (relative to drive root)
    into a folder ID. For Shared drives, the drive root is the folder with ID==drive_id.
    """
    parent_id = drive_id  # root of Shared drive
    parts = [p for p in path.split("/") if p]  # ignore empty segments
    for name in parts:
        parent_id = get_child_folder_id(service, drive_id, parent_id, name)
    return parent_id


def list_files_in_folder(service, drive_id, folder_id, page_size=100):
    """
    Return a list of file dictionaries with metadata from folder_id.
    Includes pagination to retrieve *all* results.
    """
    files = []
    page_token = None
    while True:
        res = service.files().list(
            corpora="drive",
            driveId=drive_id,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            q=f"'{folder_id}' in parents and trashed=false",
            pageSize=page_size,
            pageToken=page_token,
            # Adjust fields as needed:
            fields=(
                "nextPageToken, "
                "files(id, name, mimeType, size, modifiedTime, owners(displayName))"
            ),
            orderBy="folder,name_natural"  # optional: friendly sort
        ).execute()

        files.extend(res.get("files", []))
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return files


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


def get_labels_catalog(labels_service):
    """
    Get the complete catalog of all available labels with their metadata.
    This should be called once and cached for efficiency.

    Args:
        labels_service: Authenticated Google Drive Labels v2 service

    Returns:
        Dictionary indexed by label_id containing full label metadata including
        displayName, field names, and selection choices.
    """
    try:
        response = labels_service.labels().list(view='LABEL_VIEW_FULL').execute()
        labels = response.get('labels', [])

        catalog = {}
        for label in labels:
            label_id = label.get('id')
            catalog[label_id] = {
                'id': label_id,
                'displayName': label.get('properties', {}).get('title', 'Unknown'),
                'description': label.get('properties', {}).get('description', ''),
                'fields': {}
            }

            # Index fields by field_id
            for field in label.get('fields', []):
                field_id = field.get('id')
                field_info = {
                    'displayName': field.get('properties', {}).get('displayName', 'Unknown'),
                    'choices': {}
                }

                # Index selection choices if available
                selection_options = field.get('selectionOptions', {})
                for choice in selection_options.get('choices', []):
                    choice_id = choice.get('id')
                    field_info['choices'][choice_id] = {
                        'displayName': choice.get('properties', {}).get('displayName', 'Unknown'),
                        'description': choice.get('properties', {}).get('description', '')
                    }

                catalog[label_id]['fields'][field_id] = field_info

        return catalog
    except Exception as e:
        return {}


def get_file_labels(drive_service, file_id, labels_catalog):
    """
    Get all labels applied to a file with their display names and field values.

    Args:
        drive_service: Authenticated Google Drive v3 service
        file_id: The ID of the file to get labels for
        labels_catalog: Pre-fetched labels catalog from get_labels_catalog()

    Returns:
        List of label dictionaries with display names and field values.
        Returns empty list if file has no labels or on error.
    """
    try:
        response = drive_service.files().listLabels(fileId=file_id).execute()
        labels = response.get('labels', [])

        result = []
        for label in labels:
            label_id = label.get('id')

            # Lookup label metadata from catalog
            label_metadata = labels_catalog.get(label_id, {})
            label_info = {
                'id': label_id,
                'displayName': label_metadata.get('displayName', 'Unknown'),
                'fields': []
            }

            # Extract field values from the label
            fields = label.get('fields', {})
            for field_id, field_values in fields.items():
                # Lookup field metadata from catalog
                field_metadata = label_metadata.get('fields', {}).get(field_id, {})
                field_info = {
                    'id': field_id,
                    'displayName': field_metadata.get('displayName', 'Unknown'),
                    'values': []
                }

                # Process different field types
                if 'selection' in field_values:
                    # Selection field - lookup choice displayNames
                    selections = field_values.get('selection', [])
                    choices_metadata = field_metadata.get('choices', {})
                    for choice_id in selections:
                        choice_info = choices_metadata.get(choice_id, {})
                        field_info['values'].append({
                            'id': choice_id,
                            'displayName': choice_info.get('displayName', choice_id)
                        })
                elif 'text' in field_values:
                    field_info['values'] = field_values.get('text')
                elif 'integer' in field_values:
                    field_info['values'] = field_values.get('integer')
                elif 'dateString' in field_values:
                    field_info['values'] = field_values.get('dateString')
                elif 'user' in field_values:
                    field_info['values'] = field_values.get('user')

                if field_info['values']:
                    label_info['fields'].append(field_info)

            result.append(label_info)

        return result
    except Exception as e:
        # If file doesn't have labels or there's an error, return empty list
        return []