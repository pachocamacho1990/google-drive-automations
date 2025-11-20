# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Philosophy: Simple > Complex

**ALWAYS follow this principle:**
- **Simple > Complex** - If you can choose between simple and complex, ALWAYS choose simple
- **No frameworks** - Don't build abstractions until you have 3+ concrete use cases
- **No inheritance** - Prefer composition and copy-modify pattern
- **Standalone scripts** - Each automation should be self-contained
- **Direct execution** - Avoid wrapper layers and indirection
- **Build only what you need** - Don't build for imaginary future requirements

**When adding new automations:**
1. Copy existing working script
2. Modify for new requirements
3. Keep it standalone and direct
4. No base classes or frameworks

## Build/Environment Commands
- **Setup**: `./setup.sh` - Creates Python venv and installs all dependencies
- **Activate Environment**: `source venv/bin/activate` - Required before running any Python code
- **Run Labels Automation**: `source venv/bin/activate && python automations/labels_lister.py` - Lists all Drive Labels with metadata
- **Run Folder Lister**: `source venv/bin/activate && python automations/folder_lister.py "folder/path"` - Lists files with their applied labels
- **Test Utilities**: `source venv/bin/activate && python -c "from utilities import *; print('✅ Utilities loaded')"` - Verify utilities import

## Architecture Overview

### Authentication Flow Architecture
The project uses **OAuth2 User Authentication** (not service account):

**Google Cloud Project:**
- Project ID: `atomic-elixir-377814`
- Enabled APIs: Google Drive API v3, Drive Labels API v2

**Two-Stage Authentication:**
1. **Initial Setup**: OAuth2 flow via `credentials.json` (OAuth2 Client from Google Cloud Console)
   - First run opens browser for user authorization
   - User grants access to Drive + Labels scopes
2. **Persistent Auth**: Tokens stored in `token.json` for automatic refresh
   - Contains: access_token, refresh_token, client_id, client_secret
   - Auto-refreshes when expired (no browser needed)
   - Subsequent runs are fully automated

### Service Architecture
- **automations/labels_lister.py**: Script that uses shared auth to create service object
- **automations/folder_lister.py**: Lists files in folders with their Drive Labels
- **automations/label_modifier.py**: Modifies labels on files, uses catalog for name resolution
- **automations/bulk_label_modifier.py**: Iterates folder and applies labels to all files
- **automations/file_downloader.py**: Downloads files, handling binary vs Workspace formats
- **utilities.py**: Shared authentication logic + pure functions for API operations
- **Shared Drive Focus**: All operations designed to work with shared drive ID `0ACLtKHNaf3uMUk9PVA`

### Security Notes
- **credentials.json**: OAuth2 Client credentials (should be in .gitignore)
- **token.json**: User access tokens (NEVER commit to git - contains sensitive tokens)
- Both files are required for authentication but must remain private

### Import Dependencies
- **automations/labels_lister.py**: Imports `authenticate` from `utilities`
- **automations/folder_lister.py**: Imports `authenticate` and helper functions from `utilities`
- **automations/label_modifier.py**: Imports `authenticate` and `get_labels_catalog` from `utilities`
- **automations/bulk_label_modifier.py**: Imports `authenticate` and helpers from `utilities`
- **automations/file_downloader.py**: Imports `authenticate` from `utilities`
- **utilities.py**: Requires Google API client libraries, handles auth flow

### Key Constants and Configuration
- `SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.labels"]` in automations/labels_lister.py:13-16
- `FOLDER_MIME = "application/vnd.google-apps.folder"` in utilities.py:7
- `SHARED_DRIVE_ID = "0ACLtKHNaf3uMUk9PVA"` in automations/folder_lister.py:24

### Utility Functions Design Pattern
All utility functions follow the pattern: `function_name(service, drive_id, ...)` where:
- `service`: Authenticated Google Drive service object
- `drive_id`: Target shared drive ID
- Additional parameters specific to operation

The utilities handle Shared Drive-specific parameters (`corpora="drive"`, `includeItemsFromAllDrives=True`, `supportsAllDrives=True`) automatically.