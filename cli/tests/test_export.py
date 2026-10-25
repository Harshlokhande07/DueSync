import os
from datetime import date
from duelist.export import categorize_assignments, generate_summary_md, generate_summary


def test_categorize_assignments():
    ref_today = date(2026, 10, 25)
    tasks = [
        {"id": 1, "title": "Overdue Task", "due": "2026-10-20", "done": False},
        {"id": 2, "title": "This Week Task", "due": "2026-10-28", "done": False},
        {"id": 3, "title": "Later Task", "due": "2026-11-20", "done": False},
        {"id": 4, "title": "Done Task", "due": "2026-10-15", "done": True},
    ]

    overdue, this_week, later, completed = categorize_assignments(tasks, today=ref_today)
    assert len(overdue) == 1
    assert overdue[0]["id"] == 1
    assert len(this_week) == 1
    assert this_week[0]["id"] == 2
    assert len(later) == 1
    assert later[0]["id"] == 3
    assert len(completed) == 1
    assert completed[0]["id"] == 4


def test_generate_summary_md(tmp_path):
    target = tmp_path / "summary.md"
    tasks = [
        {"id": 1, "title": "Lab 1", "class": "Physics", "due": "2026-10-20", "done": False},
        {"id": 2, "title": "Lab 2", "class": "Physics", "due": "2026-10-27", "done": False},
    ]
    out_file = generate_summary_md(tasks, output_path=str(target))
    assert os.path.exists(out_file)
    content = target.read_text(encoding="utf-8")
    assert "# DueList Weekly Summary" in content
    assert "## Overdue" in content
    assert "## Due This Week" in content
    assert "Lab 1" in content
    assert "Lab 2" in content


def test_generate_summary_docx(tmp_path):
    target = tmp_path / "summary.docx"
    tasks = [
        {"id": 1, "title": "Lab 1", "class": "Physics", "due": "2026-10-20", "done": False},
    ]
    out_file = generate_summary(tasks, output_path=str(target))
    assert os.path.exists(out_file)
    assert os.path.getsize(out_file) > 0
