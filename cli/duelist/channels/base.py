"""
Base Channel interface for DueSync digest delivery.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from duelist.digest import DigestData


class ChannelError(Exception):
    """Exception raised when digest dispatch or channel configuration fails."""

    def __init__(self, message: str, exit_code: int = 2):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code

    def __str__(self) -> str:
        return self.message


class BaseChannel(ABC):
    """Abstract interface for all notification channels."""

    @abstractmethod
    def send(self, data: DigestData, config: Dict[str, Any]) -> None:
        """
        Send the digest data through this channel.
        Raises ChannelError on user/configuration error (code 1) or provider/network error (code 2).
        """
        pass
