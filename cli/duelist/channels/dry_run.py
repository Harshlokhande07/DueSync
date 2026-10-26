"""
Dry-run channel for DueSync daily digest.
Prints plain-text version directly to standard output without sending.
"""

from typing import Any, Dict

from duelist.channels.base import BaseChannel
from duelist.digest import DigestData
from duelist.render_email import render_plain_text


class DryRunChannel(BaseChannel):
    """Outputs plain-text digest directly to stdout without network activity."""

    def send(self, data: DigestData, config: Dict[str, Any]) -> None:
        plain_text = render_plain_text(data)
        print(plain_text)
