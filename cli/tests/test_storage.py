import json
import os
import pytest
from duelist import storage


def test_storage_load_nonexistent(tmp_path):
    target = tmp_path / "assignments.json"
    data = storage.load(filepath=str(target))
    assert data == []


def test_storage_save_and_load(tmp_path):
    target = tmp_path / "assignments.json"
    items = [
        {"id": 1, "title": "Math Quiz", "class": "Math", "due": "2026-11-01", "done": False, "added": "2026-10-25"},
        {"id": 2, "title": "History Paper", "class": "History", "due": "2026-11-05", "done": True, "added": "2026-10-25"},
    ]
    storage.save(items, filepath=str(target))
    loaded = storage.load(filepath=str(target))
    assert len(loaded) == 2
    assert loaded[0]["title"] == "Math Quiz"
    assert loaded[1]["done"] is True


def test_storage_corrupt_file_handling(tmp_path):
    target = tmp_path / "assignments.json"
    target.write_text("{corrupted: json data...", encoding="utf-8")

    loaded = storage.load(filepath=str(target))
    assert loaded == []
    # Verify backup exists
    bak_file = tmp_path / "assignments.json.bak"
    assert bak_file.exists()
    assert bak_file.read_text(encoding="utf-8") == "{corrupted: json data..."


def test_storage_next_id():
    assert storage.next_id([]) == 1
    assert storage.next_id([{"id": 1}, {"id": 3}]) == 4
    assert storage.next_id({"assignments": [{"id": 10}, {"id": 5}]}) == 11
