"""
Unit and integration tests for DueSync Daily Email Digest.
All network operations are strictly mocked (smtplib).
No real email addresses or passwords used.
"""

from datetime import date, timedelta
import email
from email.message import EmailMessage
import io
import json
import os
import smtplib
import socket
import ssl
import sys
import pytest

from duelist import digest, digest_config, render_email, channels, tracker
from duelist.digest import (
    DigestData,
    build_digest_data,
    format_display_date,
    format_short_date,
    truncate_title,
)
from duelist.digest_config import (
    clean_app_password,
    mask_email,
    validate_email_address,
)
from duelist.channels.base import ChannelError
from duelist.channels.email import EmailChannel
from duelist.render_email import (
    clean_header_value,
    render_email_package,
    render_html,
    render_plain_text,
    render_subject,
)


# ---------------------------------------------------------------------------
# 1. Digest Content & Urgency Categorization Tests
# ---------------------------------------------------------------------------

def test_digest_content_categorization():
    ref_today = date(2026, 10, 26)
    tasks = [
        {"id": 1, "title": "Today Task", "class": "CS 101", "due": "2026-10-26", "done": False},
        {"id": 2, "title": "Tomorrow Task", "class": "Physics", "due": "2026-10-27", "done": False},
        {"id": 3, "title": "One Day Overdue Task", "class": "Math", "due": "2026-10-25", "done": False},
        {"id": 4, "title": "Three Days Overdue Task", "class": "English", "due": "2026-10-23", "done": False},
        {"id": 5, "title": "Done Task Due Today", "class": "Bio", "due": "2026-10-26", "done": True},
        {"id": 6, "title": "Future Task (3 days away)", "class": "History", "due": "2026-10-29", "done": False},
    ]

    data = build_digest_data(tasks, today=ref_today, labels="english")

    assert data.is_empty is False
    assert data.today_section is not None
    assert data.today_section.count == 1
    assert data.today_section.items[0].status_label == "due today"

    assert data.tomorrow_section is not None
    assert data.tomorrow_section.count == 1

    assert data.overdue_section is not None
    assert data.overdue_section.count == 2
    # Verify '1 day overdue' vs 'N days overdue'
    assert any(it.status_label == "1 day overdue" for it in data.overdue_section.items)
    assert any(it.status_label == "3 days overdue" for it in data.overdue_section.items)

    # Active and completed count checks
    assert data.active_count == 5
    assert data.completed_count == 1

    plain = render_plain_text(data)
    assert "[ Today · 1 ]" in plain
    assert "Today Task" in plain
    assert "[ Tomorrow · 1 ]" in plain
    assert "Tomorrow Task" in plain
    assert "[ Overdue · 2 ]" in plain
    assert "1 day overdue" in plain
    assert "3 days overdue" in plain
    assert "Done Task" not in plain
    assert "Future Task" not in plain
    assert "Sent by duelist · 5 active, 1 completed" in plain


def test_digest_truncation_at_ten_items_and_counts():
    ref_today = date(2026, 10, 26)
    # Generate 12 tasks today, 11 tomorrow, 14 overdue
    tasks = []
    for i in range(12):
        tasks.append({"id": 100 + i, "title": f"Today Task {i:02d}", "class": "CS", "due": "2026-10-26", "done": False})
    for i in range(11):
        tasks.append({"id": 200 + i, "title": f"Tomorrow Task {i:02d}", "class": "Math", "due": "2026-10-27", "done": False})
    for i in range(14):
        tasks.append({"id": 300 + i, "title": f"Overdue Task {i:02d}", "class": "Eng", "due": "2026-10-20", "done": False})

    data = build_digest_data(tasks, today=ref_today)
    plain = render_plain_text(data)

    assert data.today_section.count == 12
    assert len(data.today_section.items) == 10
    assert data.today_section.has_more == 2
    assert "[ Today · 12 ]" in plain
    assert "+2 more" in plain

    assert data.tomorrow_section.count == 11
    assert data.tomorrow_section.has_more == 1
    assert "[ Tomorrow · 11 ]" in plain
    assert "+1 more" in plain

    assert data.overdue_section.count == 14
    assert data.overdue_section.has_more == 4
    assert "[ Overdue · 14 ]" in plain
    assert "+4 more" in plain


def test_digest_long_titles_truncation_and_empty_class():
    ref_today = date(2026, 10, 26)
    long_title = "This is a very long assignment title that clearly exceeds sixty characters in total length"
    tasks = [
        {"id": 1, "title": long_title, "class": "CS 101", "due": "2026-10-26", "done": False},
        {"id": 2, "title": "Short Title", "class": "", "due": "2026-10-26", "done": False},
    ]

    data = build_digest_data(tasks, today=ref_today)
    expected_truncated = long_title[:57] + "..."

    assert any(it.title == expected_truncated for it in data.today_section.items)
    plain = render_plain_text(data)
    assert expected_truncated in plain
    # No stray separator for empty class
    assert "• Short Title        due today" in plain or "• Short Title" in plain


def test_digest_empty_case():
    ref_today = date(2026, 10, 26)
    tasks = [
        {"id": 1, "title": "Done Task", "due": "2026-10-26", "done": True},
        {"id": 2, "title": "Next Month Task", "due": "2026-11-26", "done": False},
    ]

    data = build_digest_data(tasks, today=ref_today)
    assert data.is_empty is True
    assert data.today_section is None
    assert data.tomorrow_section is None
    assert data.overdue_section is None

    plain = render_plain_text(data)
    assert "All clear today ✅" in plain

    html_out = render_html(data)
    assert "All clear today" in html_out
    assert "✅" in html_out


def test_digest_hinglish_labels_and_date_format():
    ref_today = date(2026, 10, 26)
    tasks = [
        {"id": 1, "title": "Lab 1", "due": "2026-10-26", "done": False},
        {"id": 2, "title": "Lab 2", "due": "2026-10-27", "done": False},
    ]

    data = build_digest_data(tasks, today=ref_today, labels="hinglish")
    assert data.date_display == "Mon, 26 Oct 2026"
    assert data.today_section.heading_name == "Aaj"
    assert data.tomorrow_section.heading_name == "Kal"

    plain = render_plain_text(data)
    assert "[ Aaj · 1 ]" in plain
    assert "[ Kal · 1 ]" in plain


def test_digest_month_end_and_year_end_boundaries():
    ref_nye = date(2026, 12, 31)
    tasks = [
        {"id": 1, "title": "New Year Eve Task", "due": "2026-12-31", "done": False},
        {"id": 2, "title": "New Year Day Task", "due": "2027-01-01", "done": False},
        {"id": 3, "title": "Yesterday Task", "due": "2026-12-30", "done": False},
    ]

    data = build_digest_data(tasks, today=ref_nye, labels="english")
    assert data.today_section.items[0].title == "New Year Eve Task"
    assert data.tomorrow_section.items[0].title == "New Year Day Task"
    assert data.overdue_section.items[0].title == "Yesterday Task"
    assert data.overdue_section.items[0].status_label == "1 day overdue"


# ---------------------------------------------------------------------------
# 2. Rendering, Security, and Subject Sanitization Tests
# ---------------------------------------------------------------------------

def test_render_email_package_text_and_html():
    ref_today = date(2026, 10, 26)
    tasks = [
        {"id": 1, "title": "Chemistry Lab", "class": "Chemistry", "due": "2026-10-26", "done": False},
        {"id": 2, "title": "Physics Practical", "class": "Physics", "due": "2026-10-27", "done": False},
        {"id": 3, "title": "Maths Quiz", "class": "Maths", "due": "2026-10-20", "done": False},
    ]

    data = build_digest_data(tasks, today=ref_today)
    subject, plain_text, html_body = render_email_package(data)

    assert "DueSync · 1 due today, 1 tomorrow · 1 overdue" in subject
    assert "[ Today · 1 ]" in plain_text
    assert "<!DOCTYPE html>" in html_body
    assert "max-width:600px" in html_body
    assert "#F4F3F9" in html_body  # page background
    assert "#14645B" in html_body  # header strip teal
    assert "#FFC53D" in html_body  # yellow accent
    assert "#2FC48D" in html_body  # today mint
    assert "#F59E0B" in html_body  # tomorrow amber
    assert "#F2546F" in html_body  # overdue coral


def test_html_security_and_escaping():
    ref_today = date(2026, 10, 26)
    dangerous_title = "Lab <img src=x onerror=alert(1)> & <script>evil()</script>"
    dangerous_class = "Course <b onmouseover=hack()>101</b>"
    tasks = [
        {"id": 1, "title": dangerous_title, "class": dangerous_class, "due": "2026-10-26", "done": False},
    ]

    data = build_digest_data(tasks, today=ref_today)
    _, _, html_body = render_email_package(data)

    # Must be escaped
    assert "<script>" not in html_body
    assert "<img src=x" not in html_body
    assert "&lt;script&gt;evil()&lt;/script&gt;" in html_body
    assert "&lt;img src=x" in html_body
    assert "&lt;b onmouseover=hack()&gt;" in html_body


def test_header_injection_prevention():
    injected_subject = "Task \r\nBcc: evil@attacker.com\nSubject: Hacked"
    cleaned = clean_header_value(injected_subject, max_len=100)
    assert "\r" not in cleaned
    assert "\n" not in cleaned
    assert "Bcc: evil@attacker.com" in cleaned  # linearized as plain text, no injection


# ---------------------------------------------------------------------------
# 3. Address Validation & Masking Tests
# ---------------------------------------------------------------------------

def test_email_validation():
    assert validate_email_address("you@example.com") is True
    assert validate_email_address("student.due.sync@college.edu") is True

    # Rejection of invalid or injection attempts
    assert validate_email_address("you@example.com\nBcc: victim@example.com") is False
    assert validate_email_address("you@example.com,other@example.com") is False
    assert validate_email_address("you @example.com") is False
    assert validate_email_address("plainaddress") is False
    assert validate_email_address("missingdomain@") is False
    assert validate_email_address("@missinguser.com") is False
    assert validate_email_address("user@domainnodot") is False
    assert validate_email_address("") is False
    assert validate_email_address(None) is False


def test_email_masking_and_app_password_cleaning():
    masked = mask_email("student@gmail.com")
    assert masked == "s••••@gmail.com"

    masked_short = mask_email("a@college.edu")
    assert masked_short == "a••••@college.edu"

    assert mask_email(None) == "Not configured"
    assert mask_email("") == "Not configured"

    # Password whitespace stripping
    pasted = "abcd efgh ijkl mnop"
    cleaned = clean_app_password(pasted)
    assert cleaned == "abcdefghijklmnop"


# ---------------------------------------------------------------------------
# 4. State Management & Flags (--dry-run, --preview, --if-not-sent-today, --force)
# ---------------------------------------------------------------------------

def test_dry_run_and_preview_do_not_send_or_write_state(tmp_path, monkeypatch, capsys):
    assignments_file = tmp_path / "assignments.json"
    monkeypatch.setenv("DUELIST_DATA", str(assignments_file))
    assignments_file.write_text(json.dumps([
        {"id": 1, "title": "Active Task", "due": date.today().isoformat(), "done": False}
    ]), encoding="utf-8")

    parser = tracker.build_parser()

    # 1. Preview
    args_preview = parser.parse_args(["digest", "preview"])
    exit_code = tracker.cmd_digest(args_preview)
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Active Task" in out

    state_file = tmp_path / "digest_state.json"
    assert not state_file.exists()

    # 2. Preview --html
    html_target = tmp_path / "preview.html"
    args_preview_html = parser.parse_args(["digest", "preview", "--html", str(html_target)])
    exit_code_html = tracker.cmd_digest(args_preview_html)
    assert exit_code_html == 0
    assert html_target.exists()
    assert "<!DOCTYPE html>" in html_target.read_text(encoding="utf-8")
    assert not state_file.exists()

    # 3. Dry-run
    args_dry = parser.parse_args(["digest", "--dry-run"])
    exit_code_dry = tracker.cmd_digest(args_dry)
    assert exit_code_dry == 0
    assert not state_file.exists()


def test_if_not_sent_today_and_force(tmp_path, monkeypatch, capsys):
    assignments_file = tmp_path / "assignments.json"
    monkeypatch.setenv("DUELIST_DATA", str(assignments_file))
    today_iso = date.today().isoformat()

    state_file = tmp_path / "digest_state.json"
    state_file.write_text(json.dumps({"last_sent": today_iso}), encoding="utf-8")

    parser = tracker.build_parser()
    args_if_not_sent = parser.parse_args(["digest", "--if-not-sent-today"])

    # Must exit quietly with code 0 without sending
    exit_code = tracker.cmd_digest(args_if_not_sent)
    assert exit_code == 0
    out = capsys.readouterr().out
    assert out.strip() == ""

    # With --force, proceeds to send (or dry-run)
    args_force = parser.parse_args(["digest", "--if-not-sent-today", "--force", "--dry-run"])
    exit_code_force = tracker.cmd_digest(args_force)
    assert exit_code_force == 0


def test_successful_send_writes_last_sent(tmp_path, monkeypatch):
    assignments_file = tmp_path / "assignments.json"
    monkeypatch.setenv("DUELIST_DATA", str(assignments_file))
    today_iso = date.today().isoformat()

    class MockChannel:
        def send(self, data, config):
            return None

    monkeypatch.setattr(channels, "get_channel", lambda name: MockChannel())

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "digest": {
            "channel": "email",
            "email": {
                "from": "you@example.com",
                "to": "you@example.com",
            }
        }
    }), encoding="utf-8")

    parser = tracker.build_parser()
    args = parser.parse_args(["digest"])
    exit_code = tracker.cmd_digest(args)
    assert exit_code == 0

    state_file = tmp_path / "digest_state.json"
    assert state_file.exists()
    state_data = json.loads(state_file.read_text(encoding="utf-8"))
    assert state_data.get("last_sent") == today_iso


def test_failed_send_does_not_write_last_sent(tmp_path, monkeypatch):
    assignments_file = tmp_path / "assignments.json"
    monkeypatch.setenv("DUELIST_DATA", str(assignments_file))

    class FailingChannel:
        def send(self, data, config):
            raise ChannelError("Connection refused by SMTP", exit_code=2)

    monkeypatch.setattr(channels, "get_channel", lambda name: FailingChannel())

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "digest": {
            "channel": "email",
            "email": {"from": "you@example.com", "to": "you@example.com"}
        }
    }), encoding="utf-8")

    parser = tracker.build_parser()
    args = parser.parse_args(["digest"])
    exit_code = tracker.cmd_digest(args)
    assert exit_code == 2

    state_file = tmp_path / "digest_state.json"
    assert not state_file.exists()


# ---------------------------------------------------------------------------
# 5. SMTP Channel Integration Tests (Mocked smtplib)
# ---------------------------------------------------------------------------

def test_smtp_channel_starttls_and_ssl_flow(monkeypatch):
    monkeypatch.setenv("DUELIST_SMTP_PASSWORD", "mock secret app pass")
    monkeypatch.setenv("DUELIST_SMTP_USER", "sender@example.com")

    captured = {
        "starttls_called": False,
        "login_user": None,
        "login_pass": None,
        "sent_msg": None,
        "quit_called": False,
    }

    class MockSMTP:
        def __init__(self, host="", port=0, *args, **kwargs):
            captured["host"] = host
            captured["port"] = port
            captured["timeout"] = kwargs.get("timeout", 15)

        def ehlo(self):
            return 250, b"OK"

        def starttls(self, context=None):
            captured["starttls_called"] = True
            captured["ssl_context"] = context
            return 220, b"Ready"

        def login(self, user, password):
            captured["login_user"] = user
            captured["login_pass"] = password
            return 235, b"Authenticated"

        def send_message(self, msg):
            captured["sent_msg"] = msg
            return {}

        def quit(self):
            captured["quit_called"] = True
            return 221, b"Bye"

        def close(self):
            pass

    monkeypatch.setattr(smtplib, "SMTP", MockSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", MockSMTP)

    data = build_digest_data([
        {"id": 1, "title": "Homework", "due": date.today().isoformat(), "done": False}
    ])
    cfg = {
        "email": {
            "provider": "gmail",
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "security": "starttls",
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "from_name": "DueSync",
        }
    }

    channel = EmailChannel()
    channel.send(data, cfg)

    assert captured["host"] == "smtp.gmail.com"
    assert captured["port"] == 587
    assert captured["starttls_called"] is True
    assert captured["login_user"] == "sender@example.com"
    assert captured["login_pass"] == "mocksecretapppass"  # Spaces stripped!
    assert captured["sent_msg"] is not None
    assert captured["sent_msg"]["To"] == "recipient@example.com"
    assert captured["quit_called"] is True


def test_smtp_channel_error_handling(monkeypatch):
    # 1. Missing password
    monkeypatch.delenv("DUELIST_SMTP_PASSWORD", raising=False)
    data = build_digest_data([])
    cfg = {
        "email": {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "smtp_host": "smtp.gmail.com",
        }
    }
    channel = EmailChannel()

    with pytest.raises(ChannelError) as exc_missing:
        channel.send(data, cfg)
    assert exc_missing.value.exit_code == 1
    assert "DUELIST_SMTP_PASSWORD" in exc_missing.value.message

    # 2. Authentication failure (535)
    monkeypatch.setenv("DUELIST_SMTP_PASSWORD", "bad_pass")

    class MockSMTPAuthFail:
        def __init__(self, host="", port=0, *args, **kwargs):
            pass
        def ehlo(self):
            pass
        def starttls(self, context=None):
            pass
        def login(self, user, password):
            raise smtplib.SMTPAuthenticationError(535, b"Authentication credentials invalid")
        def close(self):
            pass

    monkeypatch.setattr(smtplib, "SMTP", MockSMTPAuthFail)
    monkeypatch.setattr(smtplib, "SMTP_SSL", MockSMTPAuthFail)
    with pytest.raises(ChannelError) as exc_auth:
        channel.send(data, cfg)
    assert exc_auth.value.exit_code == 2
    assert "App Password" in exc_auth.value.message

    # 3. Recipient refused
    class MockSMTPRecipRefused:
        def __init__(self, host="", port=0, *args, **kwargs):
            pass
        def ehlo(self):
            pass
        def starttls(self, context=None):
            pass
        def login(self, user, password):
            pass
        def send_message(self, msg):
            raise smtplib.SMTPRecipientsRefused({"recipient@example.com": (550, b"User unknown")})
        def close(self):
            pass

    monkeypatch.setattr(smtplib, "SMTP", MockSMTPRecipRefused)
    monkeypatch.setattr(smtplib, "SMTP_SSL", MockSMTPRecipRefused)
    with pytest.raises(ChannelError) as exc_recip:
        channel.send(data, cfg)
    assert exc_recip.value.exit_code == 2
    assert "refused" in exc_recip.value.message

    # 4. Timeout error
    class MockSMTPTimeout:
        def __init__(self, host="", port=0, *args, **kwargs):
            raise socket.timeout("timed out")
        def close(self):
            pass

    monkeypatch.setattr(smtplib, "SMTP", MockSMTPTimeout)
    monkeypatch.setattr(smtplib, "SMTP_SSL", MockSMTPTimeout)
    with pytest.raises(ChannelError) as exc_to:
        channel.send(data, cfg)
    assert exc_to.value.exit_code == 2
    assert "timed out" in exc_to.value.message.lower()
