"""
This file defines the interfaces of "Command" and three types of "Commanders".
"""
from queue import Queue
from typing import Dict, Iterable, List

__all__ = [
    "BaseCommand",
    "BaseCommander",
    "BaseLazyCommander",
    "BaseAsyncCommander",
]


class BaseCommand:
    score: int

    def copy_clipboard(self) -> str:
        """
        Return the string to be copied.
        """
        return ""

    def preview(self) -> Dict[str, str]:
        """
        Return a dictionary for previewing
        """
        return {}

    def result(self) -> None:
        """
        Action to be performed for the command.
        """
        ...

    def __str__(self) -> str:
        """
        Return the string for listing.
        """
        return ""


class BaseCommander:
    def match(self, keywords: List[str]) -> Iterable[BaseCommand]:
        raise NotImplementedError()


class BaseLazyCommander:
    def match(self, keywords: List[str], queue: Queue[BaseCommand]) -> None:
        raise NotImplementedError()


class BaseAsyncCommander:
    async def match(self, keywords: List[str], queue: Queue[BaseCommand]) -> None:
        raise NotImplementedError()
