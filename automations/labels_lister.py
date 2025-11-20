"""List Drive labels - simplified standalone script."""

import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from googleapiclient.discovery import build
from utilities import authenticate
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.labels"
]



def list_labels():
    """List all Drive labels."""
    creds = authenticate(SCOPES)
    labels_api = build("drivelabels", "v2", credentials=creds)
    return labels_api.labels().list(view="LABEL_VIEW_FULL").execute()

def print_colored_json(data):
    """Print JSON data with syntax highlighting."""
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    colored_json = highlight(json_str, JsonLexer(), TerminalFormatter())
    print(colored_json)

if __name__ == "__main__":
    labels_data = list_labels()
    print_colored_json(labels_data)