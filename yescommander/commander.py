"""
This file includes most basic `Commander` classes.
"""
from __future__ import annotations

import asyncio
import json
import math
import os
from pathlib import Path
from pprint import pprint
from queue import Queue
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from .core import BaseAsyncCommander, BaseCommand, BaseCommander
from .theme import theme
from .xdg import cache_path

__all__ = [
    "CalculatorSoldier",
    "Commander",
    "DebugSoldier",
    "FileSoldier",
    "RunSoldier",
    "Soldier",
    "RunAsyncCommander",
    "inject_command",
    "copy_command",
    "file_viewer",
    "update_file_viewer",
]


file_viewer = {"default": "vim %s"}
# This `file_viewer` stores commands to open different types of files.


def update_file_viewer(mode: str = "cache"):
    def w(func):
        def c():
            viewer_cache = cache_path / "viewer.json"
            if mode == "cache":
                if viewer_cache.exists():
                    with viewer_cache.open() as fp:
                        file_viewer.update(json.load(fp))
                    return
            elif mode == "ignore":
                pass
            else:
                raise ValueError('mode could only be "cache" or "ignore".')
            file_viewer.update(func())
            viewer_cache.parent.mkdir(parents=True, exist_ok=True)
            with viewer_cache.open("w") as fp:
                json.dump(file_viewer, fp)

        return c

    return w


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


def copy_command(command) -> None:
    import pyperclip  # type: ignore

    content = command.copy_clipboard()
    if len(content) > 0:
        pyperclip.copy(content)
        print("Copied")
    return content


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
    `FileSoldier` would give an order to open a file with its corresponding viewer defined in
    `file_viewer` if given keywords are matched with this file's default keywords or its name.
    """

    def __init__(
        self,
        keywords: List[str],
        filename: str,
        description: str,
        filetype: str,
        score: int = 50,
        dir: Optional[Path] = None,
    ):

        self.keywords = keywords
        self.filename = str(filename)
        self.description = str(description)
        self.filetype = str(filetype)
        self.score = score
        self.dir = dir  # Change to this path

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
        if self.dir is not None:
            ans["dir"] = str(self.dir)
        if len(self.keywords) > 0:
            ans["keywords"] = " ".join(self.keywords)
        return ans

    def copy_clipboard(self) -> str:
        return self.filename

    def result(self) -> None:
        prev_cwd = Path.cwd()
        dir = prev_cwd if self.dir is None else self.dir
        os.chdir(dir)
        os.system(self._open() % self.filename)
        os.chdir(prev_cwd)


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
    `Commander` object is in charge of a list of `BaseCommander` objects.
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


class DebugSoldier(BaseCommand, BaseCommander):
    def __init__(self) -> None:
        self.info: Dict[str, Any] = {"theme": theme.to_dict()}
        self.score = -1000

    def order(self, keywords: List[str], queue) -> None:
        if len(keywords) == 1 and keywords[0] == "debug":
            queue.put(self)

    def __str__(self) -> str:
        return "Debug"

    def preview(self) -> Dict[str, str]:
        return {"print debug infomation": ""}

    def result(self) -> None:
        pprint(self.info)


class CalculatorSoldier(BaseCommand, BaseCommander):
    def __init__(self):
        self.answer = None
        self._formula = ""
        self.marker = " "
        self.score = 100
        self._ns = None

    @property
    def ns(self):
        if self._ns is None:
            self._ns = vars(math).copy()
            self._ns.update(vars())
        return self._ns

    def order(self, keywords, queue):
        formula = "".join(keywords)
        self._formula = formula
        try:
            self.answer = str(eval(formula, self.ns))
            queue.put(self)
        except:  # noqa: E722
            pass

    def __str__(self):
        return self._formula + "=" + str(self.answer)

    def copy_clipboard(self):
        return str(self.answer)

    def preview(self):
        return {"answer": str(self.answer)}

    def result(self):
        inject_command(str(self.answer))
