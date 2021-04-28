"""
This file defines the interfaces of "Command" and three types of "Commanders".
"""
from queue import Queue
from typing import Dict, Iterable, List

__all__ = [
    "BaseCommand",
    "BaseCommander",
    "BaseAsyncCommander",
]


class BaseCommand:
    """
    The is the base class for commands which could be displayed (`__str__`),
    executed (`__run__`) or copied (`copy_clipboard`) by `yc`.
    """

    score: int  # Used for sorting. Higher score means higher preference.

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
        raise NotImplementedError()


class BaseCommander:
    """
    `BaseCommander` is a class which implements a `order` method. The `order`
    method takes a list of keywords as input, then return an iterable object
    which puts a set of `BaseCommand` objects into a command queue.
    """

    def order(self, keywords: List[str], queue: Queue) -> None:
        raise NotImplementedError()


class BaseAsyncCommander:
    """
    `BaseAsyncCommander` is a class which implements a **async** `order` method
    which has the same interface as `BaseCommander`'s.
    """

    async def order(self, keywords: List[str], queue: "Queue[BaseCommand]") -> None:
        raise NotImplementedError()
