from datetime import date, timedelta
from duelist.status import Status, get_status, get_hex_color, get_rgb_normalized


def test_status_completed():
    ref_today = date(2026, 10, 25)
    # Even if overdue by date, if done is True, status is DONE
    task = {"due": "2026-10-20", "done": True}
    assert get_status(task, today=ref_today) == Status.DONE


def test_status_overdue():
    ref_today = date(2026, 10, 25)
    task = {"due": "2026-10-24", "done": False}
    assert get_status(task, today=ref_today) == Status.OVERDUE


def test_status_due_today():
    ref_today = date(2026, 10, 25)
    # Task due today is Due Soon, NOT Overdue
    task = {"due": "2026-10-25", "done": False}
    assert get_status(task, today=ref_today) == Status.DUE_SOON


def test_status_due_within_three_days():
    ref_today = date(2026, 10, 25)
    # exactly 3 days away
    task_3d = {"due": "2026-10-28", "done": False}
    assert get_status(task_3d, today=ref_today) == Status.DUE_SOON

    # 4 days away is Pending
    task_4d = {"due": "2026-10-29", "done": False}
    assert get_status(task_4d, today=ref_today) == Status.PENDING


def test_status_colors():
    assert get_hex_color(Status.OVERDUE) == "#FF6B6B"
    assert get_hex_color(Status.DUE_SOON) == "#FFD93D"
    assert get_hex_color(Status.DONE) == "#6BCB77"

    rgb = get_rgb_normalized("#FF6B6B")
    assert round(rgb["red"], 2) == 1.0
