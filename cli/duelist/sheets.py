import json
import os
import sys
from typing import List, Dict, Any, Union

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from duelist.status import get_status, get_hex_color, get_rgb_normalized

CREDENTIALS_FILE = os.path.abspath("credentials.json")
CONFIG_FILE = os.path.abspath("config.json")


def _load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_config(config: Dict[str, Any]) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not save config: {e}\n")


def sync_to_sheets(
    assignments: Union[List[Dict[str, Any]], Dict[str, Any]],
    sheet_name: str = "DueList",
    spreadsheet_id: str = None
) -> None:
    """Sync assignments to a Google Sheet with formatting and color-coding."""
    if isinstance(assignments, dict) and "assignments" in assignments:
        items = assignments["assignments"]
    elif isinstance(assignments, list):
        items = assignments
    else:
        items = []

    if not os.path.exists(CREDENTIALS_FILE):
        sys.stderr.write(
            "Error: credentials.json not found.\n"
            "Please create a Google Cloud service account, download its key file to 'credentials.json',\n"
            "and share your Google Sheet with the service account client email address.\n"
        )
        sys.exit(1)

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        sys.stderr.write("Error: Missing Google Sheets libraries. Run: pip install gspread google-auth\n")
        sys.exit(1)

    config = _load_config()
    target_spreadsheet_id = spreadsheet_id or config.get("spreadsheet_id")

    if not target_spreadsheet_id:
        try:
            target_spreadsheet_id = input("Enter your Google Spreadsheet ID (from its URL): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(1)

        if not target_spreadsheet_id:
            sys.stderr.write("Error: Spreadsheet ID is required to sync.\n")
            sys.exit(1)

        config["spreadsheet_id"] = target_spreadsheet_id
        _save_config(config)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(target_spreadsheet_id)
    except Exception as err:
        sys.stderr.write(
            f"Error: Unable to connect to Google Sheets with ID '{target_spreadsheet_id}'.\n"
            f"Details: {err}\n"
            "Ensure the spreadsheet is shared with the client email found in credentials.json.\n"
        )
        sys.exit(1)

    try:
        ws = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        try:
            ws = spreadsheet.add_worksheet(title=sheet_name, rows=max(len(items) + 50, 100), cols=6)
        except Exception as e:
            sys.stderr.write(f"Error creating worksheet '{sheet_name}': {e}\n")
            sys.exit(1)

    # Clear worksheet contents
    try:
        ws.clear()
    except Exception as e:
        sys.stderr.write(f"Error clearing worksheet '{sheet_name}': {e}\n")
        sys.exit(1)

    headers = ["ID", "Title", "Class", "Due Date", "Status", "Date Added"]
    rows = [headers]

    sorted_items = sorted(items, key=lambda x: str(x.get("due", "")))
    for a in sorted_items:
        st = get_status(a)
        rows.append([
            a.get("id", ""),
            a.get("title", ""),
            a.get("class", ""),
            a.get("due", ""),
            st.value,
            a.get("added", "")
        ])

    try:
        ws.update("A1", rows)
    except Exception as e:
        sys.stderr.write(f"Error updating cells: {e}\n")
        sys.exit(1)

    sheet_id = ws.id
    requests = []

    # 1. Header formatting: bold, white text, dark background #4A4E69, center alignment, frozen row
    header_bg = get_rgb_normalized("#4A4E69")
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "bold": True,
                        "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}
                    },
                    "backgroundColor": header_bg,
                    "horizontalAlignment": "CENTER",
                }
            },
            "fields": "userEnteredFormat(textFormat,backgroundColor,horizontalAlignment)",
        }
    })

    # Freeze header row
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {
                    "frozenRowCount": 1
                }
            },
            "fields": "gridProperties.frozenRowCount"
        }
    })

    # 2. Row background coloring from status
    for i, a in enumerate(sorted_items, start=1):
        st = get_status(a)
        hex_color = get_hex_color(st)
        row_bg = get_rgb_normalized(hex_color)
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": i,
                    "endRowIndex": i + 1,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": row_bg,
                    }
                },
                "fields": "userEnteredFormat.backgroundColor",
            }
        })

    # 3. Auto-resize columns
    requests.append({
        "autoResizeDimensions": {
            "dimensions": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 0,
                "endIndex": 6
            }
        }
    })

    try:
        spreadsheet.batch_update({"requests": requests})
    except Exception as e:
        sys.stderr.write(f"Warning: Could not apply cell formatting: {e}\n")

    spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{target_spreadsheet_id}"
    print(f"✔ Successfully synced {len(sorted_items)} assignment(s) to '{sheet_name}'.")
    print(f"Spreadsheet URL: {spreadsheet_url}")
