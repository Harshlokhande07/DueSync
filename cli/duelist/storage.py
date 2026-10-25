import json
import os
import shutil
import sys
import tempfile
from typing import List, Dict, Any, Union


def get_data_filepath() -> str:
    """Return the resolved path to the assignments data file."""
    env_path = os.environ.get("DUELIST_DATA")
    if env_path:
        return os.path.abspath(env_path)
    return os.path.abspath("assignments.json")


def load(filepath: str = None) -> List[Dict[str, Any]]:
    """
    Load assignments from disk.
    Returns an empty list if the file does not exist.
    If the file contains invalid JSON, backs it up to <filepath>.bak,
    prints an error message to sys.stderr, and returns an empty list.
    """
    path = filepath or get_data_filepath()
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)

            # Support both [{"id": ...}] and {"assignments": [...]}
            if isinstance(data, dict) and "assignments" in data:
                return data["assignments"]
            elif isinstance(data, list):
                return data
            else:
                return []
    except (json.JSONDecodeError, OSError) as err:
        bak_path = f"{path}.bak"
        try:
            shutil.copyfile(path, bak_path)
            sys.stderr.write(
                f"Error: Corrupt data file at '{path}' ({err}). "
                f"Created backup at '{bak_path}'. Starting with empty list.\n"
            )
        except Exception as copy_err:
            sys.stderr.write(
                f"Error: Corrupt data file at '{path}' ({err}). Backup failed: {copy_err}\n"
            )
        return []


def save(data: Union[List[Dict[str, Any]], Dict[str, Any]], filepath: str = None) -> None:
    """
    Save assignments atomically to disk.
    Writes to a temporary file in the same directory, flushes, then replaces target file.
    """
    path = filepath or get_data_filepath()
    target_dir = os.path.dirname(os.path.abspath(path))
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    # Normalize to list
    if isinstance(data, dict) and "assignments" in data:
        items = data["assignments"]
    elif isinstance(data, list):
        items = data
    else:
        items = []

    # Write to temp file in target directory for atomic replace
    tmp_fd, tmp_path = tempfile.mkstemp(dir=target_dir, prefix="assignments_", suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def next_id(data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> int:
    """Return the next available auto-incremented assignment ID."""
    if isinstance(data, dict) and "assignments" in data:
        items = data["assignments"]
    elif isinstance(data, list):
        items = data
    else:
        items = []

    ids = [a["id"] for a in items if isinstance(a, dict) and "id" in a and isinstance(a["id"], int)]
    return max(ids) + 1 if ids else 1
