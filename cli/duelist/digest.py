"""
DueSync Daily Digest Data Generator
Pure functions for filtering assignments and generating structured digest models.
Performs zero rendering, network calls, or filesystem operations.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class DigestTaskItem:
    id: int
    title: str
    cls: str
    due: str
    status_label: str  # "due today", "1 day overdue", "2 days overdue", or ""
    days_overdue: int = 0


@dataclass
class DigestSection:
    heading_name: str  # "Today", "Tomorrow", "Overdue" or "Aaj", "Kal", "Overdue"
    count: int
    items: List[DigestTaskItem]
    has_more: int = 0  # count - 10 if count > 10 else 0


@dataclass
class DigestData:
    date_display: str  # e.g. "Mon, 26 Oct 2026"
    date_short: str    # e.g. "Mon 26 Oct"
    date_obj: date
    labels: str        # "english" or "hinglish"
    today_section: Optional[DigestSection]
    tomorrow_section: Optional[DigestSection]
    overdue_section: Optional[DigestSection]
    total_relevant: int
    active_count: int
    completed_count: int
    is_empty: bool


def get_current_date() -> date:
    """Injectable provider for current date (local timezone)."""
    return date.today()


def truncate_title(title: str, max_len: int = 60) -> str:
    """Truncate title cleanly to max_len with an ellipsis if it exceeds the limit."""
    cleaned = (title or "").strip()
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 3] + "..."


def format_display_date(d: date) -> str:
    """Format full display date: e.g. 'Mon, 26 Oct 2026'."""
    return f"{d.strftime('%a')}, {d.day} {d.strftime('%b %Y')}"


def format_short_date(d: date) -> str:
    """Format short date: e.g. 'Mon 26 Oct'."""
    return f"{d.strftime('%a')} {d.day} {d.strftime('%b')}"


def build_digest_data(
    tasks: List[Dict[str, Any]],
    today: Optional[date] = None,
    labels: str = "english",
    send_when_empty: bool = True,
) -> DigestData:
    """
    Build structured DigestData from tasks list.

    Rules:
    - Incomplete tasks only for Today, Tomorrow, Overdue.
    - Today: incomplete with due == today.isoformat().
    - Tomorrow: incomplete with due == tomorrow.isoformat().
    - Overdue: incomplete with due < today.isoformat(). Each has 'N days overdue' ('1 day overdue' for 1).
    - Completed tasks are never included in sections.
    - Each section is sorted by due date, then title.
    - Max 10 tasks shown per section, then '+N more'.
    - Titles longer than 60 chars truncated with ellipsis.
    - Footer displays total active and completed counts.
    """
    if today is None:
        today = get_current_date()

    today_iso = today.isoformat()
    tomorrow_iso = (today + timedelta(days=1)).isoformat()

    active_count = sum(1 for t in tasks if not t.get("done", False))
    completed_count = sum(1 for t in tasks if t.get("done", False))

    incomplete = [t for t in tasks if not t.get("done", False)]

    today_raw: List[Dict[str, Any]] = []
    tomorrow_raw: List[Dict[str, Any]] = []
    overdue_raw: List[Dict[str, Any]] = []

    for t in incomplete:
        due = t.get("due")
        if not due:
            continue
        if due == today_iso:
            today_raw.append(t)
        elif due == tomorrow_iso:
            tomorrow_raw.append(t)
        elif due < today_iso:
            overdue_raw.append(t)

    # Sort each section by due date, then by title
    today_raw.sort(key=lambda x: (x.get("due") or "", (x.get("title") or "").strip().lower()))
    tomorrow_raw.sort(key=lambda x: (x.get("due") or "", (x.get("title") or "").strip().lower()))
    overdue_raw.sort(key=lambda x: (x.get("due") or "", (x.get("title") or "").strip().lower()))

    # Build today items
    today_items: List[DigestTaskItem] = []
    for t in today_raw[:10]:
        today_items.append(
            DigestTaskItem(
                id=t.get("id", 0),
                title=truncate_title(t.get("title") or "Untitled", max_len=60),
                cls=(t.get("class") or "").strip(),
                due=today_iso,
                status_label="due today",
                days_overdue=0,
            )
        )

    # Build tomorrow items
    tomorrow_items: List[DigestTaskItem] = []
    for t in tomorrow_raw[:10]:
        tomorrow_items.append(
            DigestTaskItem(
                id=t.get("id", 0),
                title=truncate_title(t.get("title") or "Untitled", max_len=60),
                cls=(t.get("class") or "").strip(),
                due=tomorrow_iso,
                status_label="",
                days_overdue=0,
            )
        )

    # Build overdue items
    overdue_items: List[DigestTaskItem] = []
    for t in overdue_raw[:10]:
        due_str = t.get("due", today_iso)
        try:
            due_date = date.fromisoformat(due_str)
            days = max(1, (today - due_date).days)
        except Exception:
            days = 1

        label = "1 day overdue" if days == 1 else f"{days} days overdue"
        overdue_items.append(
            DigestTaskItem(
                id=t.get("id", 0),
                title=truncate_title(t.get("title") or "Untitled", max_len=60),
                cls=(t.get("class") or "").strip(),
                due=due_str,
                status_label=label,
                days_overdue=days,
            )
        )

    is_hinglish = labels.strip().lower() == "hinglish"
    today_heading = "Aaj" if is_hinglish else "Today"
    tomorrow_heading = "Kal" if is_hinglish else "Tomorrow"
    overdue_heading = "Overdue"

    today_sec = (
        DigestSection(
            heading_name=today_heading,
            count=len(today_raw),
            items=today_items,
            has_more=max(0, len(today_raw) - 10),
        )
        if today_raw
        else None
    )

    tomorrow_sec = (
        DigestSection(
            heading_name=tomorrow_heading,
            count=len(tomorrow_raw),
            items=tomorrow_items,
            has_more=max(0, len(tomorrow_raw) - 10),
        )
        if tomorrow_raw
        else None
    )

    overdue_sec = (
        DigestSection(
            heading_name=overdue_heading,
            count=len(overdue_raw),
            items=overdue_items,
            has_more=max(0, len(overdue_raw) - 10),
        )
        if overdue_raw
        else None
    )

    total_relevant = len(today_raw) + len(tomorrow_raw) + len(overdue_raw)
    is_empty = total_relevant == 0

    return DigestData(
        date_display=format_display_date(today),
        date_short=format_short_date(today),
        date_obj=today,
        labels=labels,
        today_section=today_sec,
        tomorrow_section=tomorrow_sec,
        overdue_section=overdue_sec,
        total_relevant=total_relevant,
        active_count=active_count,
        completed_count=completed_count,
        is_empty=is_empty,
    )
