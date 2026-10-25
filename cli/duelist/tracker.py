import argparse
import os
import shlex
import sys
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from dateutil import parser as dateparser

from duelist import storage
from duelist.export import generate_summary, generate_summary_md
from duelist.sheets import sync_to_sheets
from duelist.status import (
    Status,
    get_status,
    get_terminal_color,
    format_colored_text,
    is_color_enabled
)

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from colorama import init as colorama_init
    colorama_init()
except Exception:
    pass


def parse_due_date(due_str: str, today: Optional[date] = None) -> date:
    """
    Parse a flexible due date string into a date object.
    Supports relative phrases ('today', 'tomorrow', 'next week') and handles
    year-rollover for yearless dates (e.g. if 'June 20' is in the past, roll to next year).
    Raises ValueError on unparseable input.
    """
    if today is None:
        today = date.today()

    cleaned = due_str.strip().lower()

    if cleaned in ("today", "tonight"):
        return today
    if cleaned in ("tomorrow", "tmrw"):
        return today + timedelta(days=1)
    if cleaned in ("in a week", "next week"):
        return today + timedelta(days=7)

    # Handle 'next <weekday>' (e.g. 'next friday')
    weekdays = {
        "monday": 0, "mon": 0,
        "tuesday": 1, "tue": 1,
        "wednesday": 2, "wed": 2,
        "thursday": 3, "thu": 3,
        "friday": 4, "fri": 4,
        "saturday": 5, "sat": 5,
        "sunday": 6, "sun": 6,
    }
    if cleaned.startswith("next ") and cleaned[5:].strip() in weekdays:
        target_wd = weekdays[cleaned[5:].strip()]
        days_ahead = (target_wd - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return today + timedelta(days=days_ahead)

    # Standard date parsing via dateutil
    # Default to current year, month 1, day 1 to detect missing year
    sentinel_year = 1900
    default_dt = dateparser.parse(f"{sentinel_year}-01-01")
    parsed_dt = dateparser.parse(due_str, default=default_dt)

    if parsed_dt.year == sentinel_year:
        # Date string did not specify a year; default to current year
        candidate_date = date(today.year, parsed_dt.month, parsed_dt.day)
        # If the candidate date has already passed this year, roll over to next year
        if candidate_date < today:
            candidate_date = date(today.year + 1, parsed_dt.month, parsed_dt.day)
        return candidate_date

    return parsed_dt.date()


def _truncate(text: str, max_len: int) -> str:
    """Truncate text cleanly with an ellipsis if it exceeds max_len."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def print_table(assignments: List[Dict[str, Any]], force_no_color: bool = False) -> None:
    """Print formatted ASCII table of assignments with color highlights and legend."""
    if not assignments:
        print("No assignments yet. Add one with: duelist add \"Title\" --class \"Class\" --due \"Date\"")
        return

    col_id_w = 4
    col_title_w = 30
    col_class_w = 18
    col_due_w = 12
    col_status_w = 10

    header = f"{'ID':<{col_id_w}} {'Title':<{col_title_w}} {'Class':<{col_class_w}} {'Due':<{col_due_w}} {'Status':<{col_status_w}}"
    divider = "-" * len(header)
    print(header)
    print(divider)

    sorted_list = sorted(assignments, key=lambda x: str(x.get("due", "")))
    for a in sorted_list:
        aid = str(a.get("id", ""))
        title = _truncate(str(a.get("title", "")), col_title_w)
        cls = _truncate(str(a.get("class", "")), col_class_w)
        due = str(a.get("due", ""))
        status = get_status(a)

        row_text = f"{aid:<{col_id_w}} {title:<{col_title_w}} {cls:<{col_class_w}} {due:<{col_due_w}} {status.value:<{col_status_w}}"
        color_code = get_terminal_color(status, force_no_color=force_no_color)
        print(format_colored_text(row_text, color_code))

    print(divider)
    print("Legend: Green = Done  |  Red = Overdue  |  Yellow = Due Soon (<= 3 days)")


def cmd_add(args) -> int:
    try:
        due_date = parse_due_date(args.due)
        due_str = due_date.isoformat()
    except (ValueError, OverflowError, TypeError) as err:
        sys.stderr.write(f"Error: Could not parse due date '{args.due}': {err}\n")
        return 1

    clean_title = args.title.strip()
    if not clean_title:
        sys.stderr.write("Error: Assignment title cannot be empty.\n")
        return 1

    clean_class = (args.cls or "").strip()

    assignments = storage.load()
    assignment = {
        "id": storage.next_id(assignments),
        "title": clean_title,
        "class": clean_class,
        "due": due_str,
        "done": False,
        "added": date.today().isoformat(),
    }
    assignments.append(assignment)
    storage.save(assignments)

    cls_info = f" ({clean_class})" if clean_class else ""
    print(f"✔ Added #{assignment['id']} · {clean_title}{cls_info} · due {due_str}")
    return 0


def cmd_list(args) -> int:
    assignments = storage.load()
    no_color = getattr(args, "no_color", False)
    print_table(assignments, force_no_color=no_color)
    return 0


def cmd_upcoming(args) -> int:
    assignments = storage.load()
    today = date.today()
    cutoff = today + timedelta(days=7)

    upcoming = []
    for a in assignments:
        if a.get("done", False):
            continue
        due_str = a.get("due")
        if not due_str:
            continue
        try:
            due_date = date.fromisoformat(due_str)
            if today <= due_date <= cutoff:
                upcoming.append(a)
        except ValueError:
            continue

    if not upcoming:
        print("Nothing due in the next 7 days.")
    else:
        no_color = getattr(args, "no_color", False)
        print_table(upcoming, force_no_color=no_color)
    return 0


def cmd_done(args) -> int:
    assignments = storage.load()
    for a in assignments:
        if a.get("id") == args.id:
            a["done"] = True
            storage.save(assignments)
            print(f"✔ Marked #{args.id} \"{a.get('title')}\" as done.")
            return 0

    sys.stderr.write(f"Error: No assignment found with ID {args.id}.\n")
    return 1


def cmd_remove(args) -> int:
    assignments = storage.load()
    before_len = len(assignments)
    assignments = [a for a in assignments if a.get("id") != args.id]

    if len(assignments) == before_len:
        sys.stderr.write(f"Error: No assignment found with ID {args.id}.\n")
        return 1

    storage.save(assignments)
    print(f"✔ Removed assignment #{args.id}.")
    return 0


def cmd_export(args) -> int:
    assignments = storage.load()
    out_format = args.format.lower()
    try:
        if out_format == "md":
            path = generate_summary_md(assignments, output_path=args.output)
        else:
            path = generate_summary(assignments, output_path=args.output)
        print(f"✔ Summary saved to: {path}")
        return 0
    except Exception as e:
        sys.stderr.write(f"Error generating export: {e}\n")
        return 1


def cmd_sync(args) -> int:
    assignments = storage.load()
    sheet_name = getattr(args, "sheet", "DueList") or "DueList"
    spreadsheet_id = getattr(args, "spreadsheet_id", None)
    sync_to_sheets(assignments, sheet_name=sheet_name, spreadsheet_id=spreadsheet_id)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="duelist",
        description="DueSync CLI (duelist): Stay ahead of every deadline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  duelist add \"Binary Search Lab\" --class \"CS 101\" --due \"June 20\"\n"
               "  duelist list\n"
               "  duelist upcoming\n"
               "  duelist done 1\n"
               "  duelist export --format md\n"
               "  duelist sync\n"
    )
    parser.add_argument("--no-color", action="store_true", help="Disable colored terminal output")
    sub = parser.add_subparsers(dest="command", metavar="command")

    # add
    p_add = sub.add_parser("add", help="Add a new assignment")
    p_add.add_argument("title", help="Assignment title")
    p_add.add_argument("--class", dest="cls", default="", metavar="CLASS", help="Course or subject name")
    p_add.add_argument("--due", required=True, help="Due date (e.g. 'June 20', '2026-11-05', 'next friday')")
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = sub.add_parser("list", help="List all assignments sorted by deadline")
    p_list.set_defaults(func=cmd_list)

    # upcoming
    p_up = sub.add_parser("upcoming", help="Show pending assignments due in the next 7 days")
    p_up.set_defaults(func=cmd_upcoming)

    # done
    p_done = sub.add_parser("done", help="Mark an assignment complete by ID")
    p_done.add_argument("id", type=int, help="Assignment ID")
    p_done.set_defaults(func=cmd_done)

    # remove
    p_rm = sub.add_parser("remove", help="Delete an assignment by ID")
    p_rm.add_argument("id", type=int, help="Assignment ID")
    p_rm.set_defaults(func=cmd_remove)

    # export
    p_export = sub.add_parser("export", help="Export summary report (.docx or .md)")
    p_export.add_argument("--format", choices=["docx", "md"], default="docx", help="Output format (default: docx)")
    p_export.add_argument("--output", default=None, metavar="FILE", help="Custom output file path")
    p_export.set_defaults(func=cmd_export)

    # sync
    p_sync = sub.add_parser("sync", help="Synchronize assignments to Google Sheets")
    p_sync.add_argument("--sheet", default="DueList", help="Worksheet tab title (default: DueList)")
    p_sync.add_argument("--spreadsheet-id", default=None, help="Target Google Spreadsheet ID")
    p_sync.set_defaults(func=cmd_sync)

    return parser


def run_repl(parser: argparse.ArgumentParser) -> None:
    print("=" * 60)
    print(" DueSync CLI (duelist) · Stay ahead of every deadline.")
    print(" Type a command (e.g. 'list', 'add --help') or 'help' or 'exit'.")
    print("=" * 60)

    while True:
        try:
            line = input("duelist> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not line:
            continue
        if line in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if line == "help":
            parser.print_help()
            continue

        try:
            tokens = shlex.split(line)
        except ValueError as err:
            print(f"Command syntax error: {err}")
            continue

        try:
            args = parser.parse_args(tokens)
        except SystemExit:
            continue

        if not args.command:
            parser.print_help()
            continue

        try:
            args.func(args)
        except Exception as e:
            print(f"Error: {e}")


def main() -> None:
    parser = build_parser()

    if len(sys.argv) == 1:
        run_repl(parser)
    else:
        try:
            args = parser.parse_args()
        except SystemExit as e:
            sys.exit(e.code)

        if not args.command:
            parser.print_help()
            sys.exit(1)

        exit_code = args.func(args)
        sys.exit(exit_code if exit_code is not None else 0)


if __name__ == "__main__":
    main()
