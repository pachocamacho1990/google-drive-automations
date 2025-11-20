# Google Drive Automation Actions

Automate Google Drive operations with Python using OAuth2 authentication and Drive Labels API.

A lightweight, framework-free Python toolkit for automating Google Drive operations.

## What are Drive Labels?
**Drive Labels** are metadata tags that you can attach to your Google Drive files to organize and classify them beyond simple folders. Think of them as "sticky notes" with structured data.

-   **Examples**: "Confidentiality" (Public/Internal/Restricted), "Status" (Draft/Final), "Department" (HR/Engineering).
-   **Why use them?**: They allow you to search, filter, and apply policies to files regardless of where they live in your folder structure.
-   **How this tool helps**: This toolkit lets you programmatically **list**, **read**, and **modify** these labels, enabling powerful automation workflows.

## Quick Start

```bash
./setup.sh                                      # Setup virtual environment
source venv/bin/activate && python automations/labels_lister.py  # List labels
```

## Project Structure - **Simple & Direct**

```
drive-automation-actions/
├── automations/
│   ├── labels_lister.py   # Standalone script: lists labels
│   ├── folder_lister.py   # Standalone script: lists files with labels
│   └── label_modifier.py  # Standalone script: modifies labels (names or IDs)
├── utilities.py           # Shared auth & helper functions
├── credentials.json       # OAuth2 client configuration (from Google Cloud Console)
├── token.json            # OAuth2 tokens (auto-generated on first run)
├── requirements.txt      # Dependencies with pinned versions
└── setup.sh             # Environment setup script
```

## Philosophy: **Simple > Complex**

**No frameworks. No inheritance. No abstractions.**
Each automation is a **standalone script** that does one thing well.

## Core Components

### Automations

#### labels_lister.py
- **Purpose**: List all available Drive Labels with full metadata
- **Standalone**: API calls + colored JSON output (uses shared auth)
- **Usage**: `python automations/labels_lister.py`

#### folder_lister.py
- **Purpose**: List files in a folder with their applied labels
- **Features**: Shows label displayNames, field names, and values
- **Usage**: `python automations/folder_lister.py "folder/path"`
- **Optimization**: Caches label catalog (1 API call instead of N)

#### label_modifier.py
- **Purpose**: Apply or update a label on a file
- **Features**: Supports human-readable names for labels, fields, and values (auto-resolves to IDs)
- **Usage**: `python automations/label_modifier.py <file_id> "Label Name" "Field Name" "Value Name"`
- **Example**: `python3.12 automations/label_modifier.py "1zOU5JWp_1lkB93IfDN9c5X95-tcDBxlG" "Clasificación de información/datos" "Categoria" "Información Interna"`

### Utilities (utilities.py)
- `authenticate(scopes)` - Shared OAuth2 authentication logic
- `get_child_folder_id(service, drive_id, parent_id, child_name)` - Find folder by name
- `resolve_path_to_folder_id(service, drive_id, path)` - Navigate folder paths
- `list_files_in_folder(service, drive_id, folder_id)` - List files with pagination
- `get_labels_catalog(labels_service)` - Get all labels metadata (for caching)
- `get_file_labels(drive_service, file_id, labels_catalog)` - Get file labels with displayNames

## Usage Examples

```python
from utilities import resolve_path_to_folder_id, list_files_in_folder

# Use utilities in your own automation scripts
folder_id = resolve_path_to_folder_id(service, drive_id, "Reports/2024")
files = list_files_in_folder(service, drive_id, folder_id)
```

## Setup Requirements

### 1. Google Cloud Project
- **Project ID**: `atomic-elixir-377814`
- **Authentication Method**: OAuth2 User Authentication (not service account)

### 2. OAuth2 Credentials Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to project `atomic-elixir-377814`
3. Enable APIs: Google Drive API + Drive Labels API
4. Create OAuth2 Client ID (Desktop Application type)
5. Download credentials → Save as `credentials.json` in project root

### 3. Python Environment
Run `./setup.sh` to create isolated virtual environment with dependencies

### 4. First-Time Authentication
- On first script execution, browser opens automatically
- User authorizes access to Google Drive + Labels
- `token.json` generated automatically (contains access + refresh tokens)
- Subsequent runs use `token.json` (no browser required)

## Security

**⚠️ Important: Never commit these files to git:**
- `credentials.json` - Contains OAuth2 client credentials
- `token.json` - Contains user access tokens and refresh tokens

Add them to `.gitignore` to prevent accidental commits.

## Dependencies

- `google-api-python-client==2.182.0` - Core Google API client
- `google-auth==2.40.3` - Authentication framework
- `google-auth-oauthlib==1.2.1` - OAuth2 flow
- `google-auth-httplib2==0.2.0` - HTTP transport
- `pikepdf==9.11.0` - PDF processing utility
- `pygments==2.18.0` - JSON syntax highlighting

## Creating New Automations - **Keep It Simple**

### Pattern: Copy & Modify
1. **Copy** `automations/labels_lister.py`
2. **Modify** the logic for your needs
3. **Run** directly

### Template
```python
"""My automation - does one thing well."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from googleapiclient.discovery import build
from utilities import authenticate

SCOPES = ["https://www.googleapis.com/auth/drive"]  # Add scopes as needed

def my_automation():
    """Do my specific task."""
    creds = authenticate(SCOPES)
    service = build("drive", "v3", credentials=creds)
    # Your logic here
    return {"result": "success"}

if __name__ == "__main__":
    print(my_automation())
```

**That's it.** No inheritance. No abstractions. Just **copy, modify, run**.