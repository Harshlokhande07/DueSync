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
from duelist import digest, digest_config, render_email, channels
from duelist.channels.base import ChannelError

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


def cmd_digest_setup(args) -> int:
    cfg = digest_config.load_digest_config()
    email_cfg = cfg.get("email", {})
    print("DueSync Email Digest Setup")
    print("-" * 35)

    # 1. Preset provider
    current_p = email_cfg.get("provider", "gmail")
    print(f"Current provider preset: {current_p}")
    p_choice = input(f"Choose provider (1=gmail [default], 2=outlook, 3=custom) [{current_p}]: ").strip()
    if p_choice == "2":
        chosen_p = "outlook"
    elif p_choice == "3":
        chosen_p = "custom"
    elif p_choice == "1" or not p_choice:
        chosen_p = "gmail"
    else:
        chosen_p = p_choice.lower()

    if chosen_p == "gmail":
        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        security = "starttls"
    elif chosen_p == "outlook":
        smtp_host = "smtp.office365.com"
        smtp_port = 587
        security = "starttls"
    else:
        curr_host = email_cfg.get("smtp_host", "")
        smtp_host = input(f"Enter SMTP host [{curr_host}]: ").strip() or curr_host
        curr_port = str(email_cfg.get("smtp_port", 587))
        port_str = input(f"Enter SMTP port [{curr_port}]: ").strip() or curr_port
        try:
            smtp_port = int(port_str)
        except ValueError:
            smtp_port = 587
        curr_sec = email_cfg.get("security", "starttls")
        sec_choice = input(f"Security mode (1=starttls [default], 2=ssl) [{curr_sec}]: ").strip()
        security = "ssl" if sec_choice == "2" else "starttls"

    # 2. Sender and Recipient addresses
    curr_from = email_cfg.get("from", "")
    masked_from = digest_config.mask_email(curr_from) if curr_from else "none"
    from_addr = input(f"Sender email address [{masked_from}]: ").strip()
    if not from_addr:
        from_addr = curr_from
    if from_addr and not digest_config.validate_email_address(from_addr):
        sys.stderr.write(f"Error: '{from_addr}' is not a valid email address.\n")
        return 1

    curr_to = email_cfg.get("to", from_addr)
    masked_to = digest_config.mask_email(curr_to) if curr_to else "none"
    to_addr = input(f"Recipient email address (press Enter for sender address) [{masked_to}]: ").strip()
    if not to_addr:
        to_addr = curr_to or from_addr
    if to_addr and not digest_config.validate_email_address(to_addr):
        sys.stderr.write(f"Error: '{to_addr}' is not a valid email address.\n")
        return 1

    # 3. Send time
    current_time = cfg.get("send_time", "08:00")
    send_time = input(f"Preferred send time (HH:MM) [{current_time}]: ").strip() or current_time

    # 4. Labels language
    current_lang = cfg.get("labels", "english")
    l_choice = input(f"Labels language (1=english [Today/Tomorrow, default], 2=hinglish [Aaj/Kal]) [{current_lang}]: ").strip()
    labels = "hinglish" if l_choice == "2" else "english"

    # 5. Send when empty
    current_empty = cfg.get("send_when_empty", True)
    empty_str = "Y" if current_empty else "n"
    e_choice = input(f"Send 'All clear' email when no tasks are due? [Y/n] [{empty_str}]: ").strip().lower()
    send_when_empty = False if e_choice == "n" else True

    email_cfg.update({
        "provider": chosen_p,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "security": security,
        "from": from_addr,
        "to": to_addr,
        "from_name": email_cfg.get("from_name", "DueSync"),
    })
    cfg.update({
        "channel": "email",
        "send_time": send_time,
        "labels": labels,
        "send_when_empty": send_when_empty,
        "email": email_cfg,
    })
    digest_config.save_digest_config(cfg)

    print("\n✔ Setup saved to config.json!")
    print("\nNext step: Set your SMTP password in the environment (never saved to files).")
    if chosen_p == "gmail":
        print("For Gmail:")
        print("  1. Turn on 2-Step Verification in your Google Account.")
        print("  2. Create an App Password: https://myaccount.google.com/apppasswords")
        print("  3. Set the environment variable:")
        print("     Linux/macOS:")
        print("       export DUELIST_SMTP_PASSWORD=\"your 16 character app password\"")
        print("     Windows (PowerShell):")
        print("       $env:DUELIST_SMTP_PASSWORD=\"your 16 character app password\"")
    else:
        print("Set DUELIST_SMTP_PASSWORD:")
        print("  Linux/macOS: export DUELIST_SMTP_PASSWORD=\"<your_password>\"")
        print("  Windows:     $env:DUELIST_SMTP_PASSWORD=\"<your_password>\"")
    return 0


def cmd_digest_preview(args) -> int:
    assignments = storage.load()
    cfg = digest_config.load_digest_config()
    data = digest.build_digest_data(
        assignments,
        labels=cfg.get("labels", "english"),
        send_when_empty=cfg.get("send_when_empty", True),
    )
    plain_text = render_email.render_plain_text(data)
    print(plain_text)

    html_path = getattr(args, "html", None)
    if html_path:
        target_path = html_path if isinstance(html_path, str) else "digest_preview.html"
        html_content = render_email.render_html(data)
        parent = os.path.dirname(os.path.abspath(target_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\n✔ HTML preview written to: {target_path}")

    return 0


def cmd_digest_status(args) -> int:
    cfg = digest_config.load_digest_config()
    email_cfg = cfg.get("email", {})
    state = digest_config.load_digest_state()
    print("DueSync Daily Digest Status")
    print("=" * 35)
    print(f"Channel:        {cfg.get('channel', 'email')} ({email_cfg.get('provider', 'gmail')})")
    print(f"Sender:         {digest_config.mask_email(email_cfg.get('from'))}")
    print(f"Recipient:      {digest_config.mask_email(email_cfg.get('to'))}")
    print(f"Send Time:      {cfg.get('send_time', '08:00')}")
    print(f"Labels:         {cfg.get('labels', 'english')}")
    print(f"Send If Empty:  {cfg.get('send_when_empty', True)}")
    print(f"Last Sent:      {state.get('last_sent', 'Never')}")
    return 0


def cmd_digest_test(args) -> int:
    assignments = storage.load()
    cfg = digest_config.load_digest_config()
    channel_name = cfg.get("channel", "email")

    data = digest.build_digest_data(
        assignments,
        labels=cfg.get("labels", "english"),
        send_when_empty=True,
    )
    channel = channels.get_channel(channel_name)
    try:
        channel.send(data, cfg)
        if channel_name != "dry_run":
            to_addr = cfg.get("email", {}).get("to", "")
            print(f"✔ Test digest successfully sent to {digest_config.mask_email(to_addr)} via {channel_name}.")
        return 0
    except ChannelError as ce:
        sys.stderr.write(f"Error: {ce.message}\n")
        return ce.exit_code
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        return 2


def cmd_digest_send(args) -> int:
    today = date.today()
    cfg = digest_config.load_digest_config()
    force = getattr(args, "force", False)
    if_not_sent = getattr(args, "if_not_sent_today", False)
    dry_run = getattr(args, "dry_run", False)

    state = digest_config.load_digest_state()
    last_sent = state.get("last_sent")

    if if_not_sent and not force:
        if last_sent == today.isoformat():
            # Exits quietly with code 0 if today's digest was already sent
            return 0

    channel_name = "dry_run" if dry_run else cfg.get("channel", "email")

    assignments = storage.load()
    data = digest.build_digest_data(
        assignments,
        today=today,
        labels=cfg.get("labels", "english"),
        send_when_empty=cfg.get("send_when_empty", True),
    )

    if data.is_empty and not cfg.get("send_when_empty", True):
        return 0

    channel = channels.get_channel(channel_name)
    try:
        channel.send(data, cfg)
        if channel_name != "dry_run":
            digest_config.save_digest_state(today.isoformat())
            to_addr = cfg.get("email", {}).get("to", "")
            print(f"✔ Daily digest sent to {digest_config.mask_email(to_addr)} via {channel_name}.")
        return 0
    except ChannelError as ce:
        sys.stderr.write(f"Error: {ce.message}\n")
        return ce.exit_code
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        return 2


def cmd_digest(args) -> int:
    action = getattr(args, "digest_action", None)
    if action == "setup":
        return cmd_digest_setup(args)
    elif action == "test":
        return cmd_digest_test(args)
    elif action == "preview":
        return cmd_digest_preview(args)
    elif action == "status":
        return cmd_digest_status(args)
    else:
        return cmd_digest_send(args)


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
               "  duelist digest\n"
               "  duelist digest preview --html\n"
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

    # digest
    p_digest = sub.add_parser(
        "digest",
        help="Daily email digest of deadlines",
        description="Daily email digest: today's, tomorrow's, and overdue deadlines.",
    )
    p_digest.add_argument("--dry-run", action="store_true", help="Print plain-text digest only without sending")
    p_digest.add_argument("--force", action="store_true", help="Send even if already sent today")
    p_digest.add_argument("--if-not-sent-today", action="store_true", help="Exit quietly if already sent today")
    p_digest.set_defaults(func=cmd_digest)

    d_sub = p_digest.add_subparsers(dest="digest_action", metavar="action")

    p_d_setup = d_sub.add_parser("setup", help="Interactive setup for email digest")
    p_d_setup.set_defaults(func=cmd_digest)

    p_d_test = d_sub.add_parser("test", help="Send a test digest using real data")
    p_d_test.set_defaults(func=cmd_digest)

    p_d_preview = d_sub.add_parser("preview", help="Preview plain-text or HTML digest without sending")
    p_d_preview.add_argument(
        "--html",
        nargs="?",
        const="digest_preview.html",
        default=None,
        metavar="FILE",
        help="Write rendered HTML to file (default: digest_preview.html)",
    )
    p_d_preview.set_defaults(func=cmd_digest)

    p_d_status = d_sub.add_parser("status", help="Show channel, masked addresses, send time, and last sent date")
    p_d_status.set_defaults(func=cmd_digest)

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
