import os
from datetime import date, timedelta
from enum import Enum
from typing import Dict, Any, Optional

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False


class Status(str, Enum):
    OVERDUE = "Overdue"
    DUE_SOON = "Due Soon"
    PENDING = "Pending"
    DONE = "Done"


# Color mapping constants
HEX_COLORS = {
    Status.OVERDUE: "#FF6B6B",
    Status.DUE_SOON: "#FFD93D",
    Status.PENDING: "#FFFFFF",
    Status.DONE: "#6BCB77",
}

RGB_COLORS = {
    Status.OVERDUE: (255, 107, 107),
    Status.DUE_SOON: (255, 217, 61),
    Status.PENDING: (255, 255, 255),
    Status.DONE: (107, 203, 119),
}


def is_color_enabled(force_no_color: bool = False) -> bool:
    """Return True if terminal color output should be enabled."""
    if force_no_color or not HAS_COLORAMA:
        return False
    # Honor standard NO_COLOR environment variable
    if os.environ.get("NO_COLOR"):
        return False
    return True


def get_status(assignment: Dict[str, Any], today: Optional[date] = None) -> Status:
    """Classify the assignment status using date granularity."""
    if assignment.get("done", False):
        return Status.DONE

    if today is None:
        today = date.today()

    due_val = assignment.get("due")
    if not due_val:
        return Status.PENDING

    if isinstance(due_val, str):
        due_date = date.fromisoformat(due_val)
    elif isinstance(due_val, date):
        due_date = due_val
    else:
        return Status.PENDING

    if due_date < today:
        return Status.OVERDUE
    elif today <= due_date <= today + timedelta(days=3):
        return Status.DUE_SOON
    else:
        return Status.PENDING


def get_terminal_color(status: Status, force_no_color: bool = False) -> str:
    """Return colorama Fore code for a status, or empty string if colors disabled."""
    if not is_color_enabled(force_no_color):
        return ""

    if status == Status.DONE:
        return Fore.GREEN
    elif status == Status.OVERDUE:
        return Fore.RED
    elif status == Status.DUE_SOON:
        return Fore.YELLOW
    return ""


def format_colored_text(text: str, color_code: str) -> str:
    """Wrap text in colorama color and RESET if color is provided."""
    if not color_code:
        return text
    return f"{color_code}{text}{Style.RESET_ALL}"


def get_hex_color(status: Status) -> str:
    """Return hex color string for sheets or styling."""
    return HEX_COLORS.get(status, "#FFFFFF")


def get_rgb_normalized(hex_color: str) -> Dict[str, float]:
    """Convert hex string (e.g. #FF6B6B) to 0.0-1.0 float RGB dict for Google Sheets API."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return {"red": r, "green": g, "blue": b}
