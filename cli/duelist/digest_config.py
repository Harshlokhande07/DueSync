"""
DueSync Digest Configuration & State Management
Handles email address validation and masking, config.json presets, and digest_state.json persistence.
"""

import json
import os
import re
import tempfile
from typing import Any, Dict, Optional, Tuple

CONFIG_FILE = "config.json"
STATE_FILE = "digest_state.json"

PROVIDER_PRESETS = {
    "gmail": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "security": "starttls",
    },
    "outlook": {
        "smtp_host": "smtp.office365.com",
        "smtp_port": 587,
        "security": "starttls",
    },
    "custom": {
        "smtp_host": "",
        "smtp_port": 587,
        "security": "starttls",
    },
}


def validate_email_address(email: Optional[str]) -> bool:
    """
    Validate that an address is a safe, single email address.
    Rejects spaces, commas, newlines, multiple @ symbols, or header injection attempts.
    """
    if not email:
        return False
    # Check for forbidden control or separator characters
    if any(ch in email for ch in ("\r", "\n", "\t", ",", " ", ";", "<", ">", '"')):
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    local_part, domain = parts
    if not local_part or not domain:
        return False
    # Domain must contain at least one dot and characters on both sides of the dot
    domain_parts = domain.split(".")
    if len(domain_parts) < 2 or not all(domain_parts):
        return False
    return True


def mask_email(email: Optional[str]) -> str:
    """
    Mask email for safe display (e.g. 's••••@gmail.com').
    """
    if not email or not email.strip():
        return "Not configured"
    cleaned = email.strip()
    if "@" not in cleaned:
        return "••••"
    local_part, domain = cleaned.split("@", 1)
    if not local_part:
        return f"••••@{domain}"
    first_char = local_part[0]
    return f"{first_char}••••@{domain}"


def clean_app_password(password: Optional[str]) -> str:
    """Strip whitespace from a pasted App Password (e.g. 'abcd efgh ijkl mnop')."""
    if not password:
        return ""
    return password.replace(" ", "").strip()


def get_data_dir() -> Optional[str]:
    """Retrieve parent directory for data/config/state based on DUELIST_DATA."""
    data_env = os.environ.get("DUELIST_DATA")
    if data_env:
        if os.path.isdir(data_env):
            return data_env
        return os.path.dirname(os.path.abspath(data_env))
    return None


def get_config_path() -> str:
    """Retrieve config file path (supports DUELIST_DATA dir/file if set)."""
    parent = get_data_dir()
    if parent:
        return os.path.join(parent, CONFIG_FILE)
    return CONFIG_FILE


def get_state_path() -> str:
    """Retrieve digest state file path."""
    parent = get_data_dir()
    if parent:
        return os.path.join(parent, STATE_FILE)
    return STATE_FILE


def load_full_config() -> Dict[str, Any]:
    """Load the full config.json file."""
    path = get_config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_digest_config() -> Dict[str, Any]:
    """Load digest settings from config.json with safe defaults."""
    full = load_full_config()
    digest_cfg = full.get("digest", {})
    email_cfg = digest_cfg.get("email", {})

    defaults_email = {
        "provider": "gmail",
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "security": "starttls",
        "from": "you@example.com",
        "to": "you@example.com",
        "from_name": "DueSync",
    }
    for k, v in defaults_email.items():
        if k not in email_cfg:
            email_cfg[k] = v

    defaults_digest = {
        "channel": "email",
        "send_time": "08:00",
        "labels": "english",
        "send_when_empty": True,
        "email": email_cfg,
    }
    for k, v in defaults_digest.items():
        if k not in digest_cfg:
            digest_cfg[k] = v

    digest_cfg["email"] = email_cfg
    return digest_cfg


def save_digest_config(digest_cfg: Dict[str, Any]) -> None:
    """Atomically save updated digest configuration to config.json."""
    full = load_full_config()
    full["digest"] = digest_cfg

    path = get_config_path()
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", dir=parent, delete=False, encoding="utf-8") as tf:
        json.dump(full, tf, indent=2)
        temp_name = tf.name

    os.replace(temp_name, path)


def load_digest_state() -> Dict[str, Any]:
    """Load digest_state.json file."""
    path = get_state_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_digest_state(last_sent_iso: str) -> None:
    """Atomically update last_sent in digest_state.json."""
    state = {"last_sent": last_sent_iso}
    path = get_state_path()
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", dir=parent, delete=False, encoding="utf-8") as tf:
        json.dump(state, tf, indent=2)
        temp_name = tf.name

    os.replace(temp_name, path)
