"""
This file includes most basic `Commander` classes.
"""
from __future__ import annotations

import asyncio
import os
from queue import Queue
from typing import Any, Dict, List, Type, TypeVar, Union

from .core import BaseAsyncCommander, BaseCommand, BaseCommander

__all__ = [
    "Soldier",
    "FileSoldier",
    "RunSoldier",
    "Commander",
    "RunAsyncCommander",
    "inject_command",
    "file_viewer",
]


file_viewer = {"default": "vim %s"}


def find_kws_cmd(input_words: List[str], keywords: List[str], command: str) -> bool:
    for k in input_words:
        findQ = False
        for kw in keywords:
            if k in kw:
                findQ = True
        if findQ or (k in command):
            continue
        return False
    return True


def inject_command(cmd: str) -> None:
    """
    Inject `cmd` to command line.
    """
    import fcntl
    import sys
    import termios

    for c in cmd:
        fcntl.ioctl(sys.stdin, termios.TIOCSTI, c.encode())


T = TypeVar("T", bound="Soldier")


class Soldier(BaseCommand, BaseCommander):
    """
    `Soldier` class is the simplest `Commander` which inherit from both `BaseCommand` and `BaseCommander`.
    In its `match` function, it yields itself.
    """

    def __init__(
        self, keywords: List[str], command: str, description: str, score: int = 50
    ) -> None:
        self.keywords = keywords
        self.command = command
        self.description = description
        self.score = score

    def order(self, keywords: List[str], queue: "Queue[BaseCommand]") -> None:
        if find_kws_cmd(keywords, self.keywords, self.command):
            queue.put(self)

    def __str__(self) -> str:
        return self.command

    def copy_clipboard(self) -> str:
        return str(self)

    def preview(self) -> Dict[str, str]:
        ans = {"command": str(self)}
        if len(self.description) > 0:
            ans["description"] = self.description
        if len(self.keywords) > 0:
            ans["keywords"] = " ".join(self.keywords)
        return ans

    def result(self) -> None:
        inject_command(self.command)

    @classmethod
    def from_dict(
        cls: Type[T], dic: Dict[str, Union[List[str], str]], **kwargs: Any
    ) -> T:
        ans = {"keywords": [], "command": "", "description": "", "score": 50}
        ans.update(dic)
        ans.update(kwargs)
        return cls(**ans)  # type: ignore


class FileSoldier(BaseCommand, BaseCommander):
    """
    `FileSoldier` would give an order to open a file with its corresponding viewer defined in `file_viewer`
    if given keywords are matched with default keywords or the name of the file.
    """

    def __init__(
        self,
        keywords: List[str],
        filename: str,
        description: str,
        filetype: str,
        score: int = 50,
    ):

        self.keywords = keywords
        self.filename = str(filename)
        self.description = str(description)
        self.filetype = str(filetype)
        self.score = score

    def order(self, keywords: List[str], queue: "Queue[BaseCommand]") -> None:
        if find_kws_cmd(keywords, self.keywords, self.filename):
            queue.put(self)

    def _open(self) -> str:
        if self.filetype in file_viewer:
            return file_viewer[self.filetype]
        return file_viewer["default"]

    def __str__(self) -> str:
        return f"edit {self.filename}"

    def preview(self) -> Dict[str, str]:
        ans = {
            "file": self.filename,
            "file type": self.filetype,
            "open with": self._open(),
        }
        if self.description != "":
            ans["description"] = self.description
        if len(self.keywords) > 0:
            ans["keywords"] = " ".join(self.keywords)
        return ans

    def copy_clipboard(self) -> str:
        return self.filename

    def result(self) -> None:
        os.system(self._open() % self.filename)


class RunSoldier(Soldier):
    """
    `RunSoldier` inherits from the `Soldier`. But instead of injecting command to termianl,
    `RunSoldier` will direct run the given command.
    """

    def result(self) -> None:
        if isinstance(self.command, str):
            os.system(self.command)
        else:
            self.command()

    def __str__(self) -> str:
        if isinstance(self.command, str):
            ans = "run: " + self.command
        else:
            ans = self.command.__doc__
        return ans.splitlines()[0]

    def copy_clipboard(self) -> str:
        return ""


class Commander(BaseCommander):
    """
    `Commander` object is in charge of a list of other `BaseCommander` objects.
    """

    def __init__(self, commanders: List[BaseCommander]) -> None:
        self._commanders = commanders

    def order(self, keywords: List[str], queue: "Queue[BaseCommand]") -> None:
        for cmdr in self._commanders:
            cmdr.order(keywords, queue)

    def recruit(self, cmd: BaseCommander) -> None:
        self._commanders.append(cmd)


class RunAsyncCommander(BaseCommander):
    def __init__(self, commands: List[BaseAsyncCommander]) -> None:
        self._commands = commands

    async def _order(self, keywords: List[str], queue: "Queue[BaseCommand]") -> None:
        for c in asyncio.as_completed(
            [cmd.order(keywords, queue=queue) for cmd in self._commands]
        ):
            await c

    def order(self, keywords: List[str], queue: "Queue[BaseCommand]") -> None:
        asyncio.run(self._order(keywords, queue))

    def recruit(self, cmd: BaseAsyncCommander) -> None:
        self._commands.append(cmd)
