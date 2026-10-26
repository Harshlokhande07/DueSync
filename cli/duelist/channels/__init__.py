"""
Channels registry for DueSync daily digest delivery.
"""

from typing import Dict, Type

from duelist.channels.base import BaseChannel, ChannelError
from duelist.channels.dry_run import DryRunChannel
from duelist.channels.email import EmailChannel

_CHANNEL_REGISTRY: Dict[str, Type[BaseChannel]] = {
    "dry_run": DryRunChannel,
    "dryrun": DryRunChannel,
    "email": EmailChannel,
    "smtp": EmailChannel,
}


def get_channel(name: str) -> BaseChannel:
    """Retrieve an initialized channel instance by name."""
    normalized = (name or "").strip().lower()
    channel_cls = _CHANNEL_REGISTRY.get(normalized, DryRunChannel)
    return channel_cls()


__all__ = [
    "BaseChannel",
    "ChannelError",
    "DryRunChannel",
    "EmailChannel",
    "get_channel",
]
