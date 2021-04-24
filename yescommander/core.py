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
    """
    `BaseCommander` is a class which implements a `order` method. The `order`
    method takes a list of keywords as input, then return an iterable object
    which generates a set of `BaseCommand` object.
    """

    def order(self, keywords: List[str]) -> Iterable[BaseCommand]:
        raise NotImplementedError()


class BaseLazyCommander:
    """
    `BaseLazyCommander` is a class which implements a `order` method. The
    `order` method takes a list of keywords and a `Queue` object as input.
    Instead of returning commands, generated commands should be put into the
    queue.
    """

    def order(self, keywords: List[str], queue: Queue[BaseCommand]) -> None:
        raise NotImplementedError()


class BaseAsyncCommander:
    """
    `BaseAsyncCommander` is a class which implements a **async** `order` method
    which has the same interface as `BaseLazyCommander`'s.
    """

    async def order(self, keywords: List[str], queue: Queue[BaseCommand]) -> None:
        raise NotImplementedError()
