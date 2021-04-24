from __future__ import annotations

import asyncio
import os
from pprint import pformat, pprint
from queue import Queue
from typing import Any, Dict, Iterable, List, Type, TypeVar, Union, cast, no_type_check

from .core import (
    BaseAsyncCommander,
    BaseCommand,
    BaseCommander,
    BaseLazyCommander,
    file_viewer,
    inject_command,
)
from .theme import Theme, theme

__all__ = [
    "Soldier",
    "RunSoldier",
    "FileSoldier",
    "Commander",
    "LazyCommander",
    "RunAsyncCommander",
    "DebugSoldier",
]


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


T = TypeVar("T", bound="Soldier")


class Soldier(BaseCommand, BaseCommander):
    def __init__(
        self, keywords: List[str], command: str, description: str, score: int = 50
    ) -> None:
        self.keywords = keywords
        self.command = command
        self.description = description
        self.score = score

    def match(self, keywords: List[str]) -> Iterable[Soldier]:
        if find_kws_cmd(keywords, self.keywords, self.command):
            yield self

    def str_command(self) -> str:
        return self.command

    def copy_clipboard(self) -> str:
        return self.str_command()

    def preview(self) -> Dict[str, str]:
        ans = {"command": self.str_command()}
        if len(self.description) > 0:
            ans["description"] = self.description
        if len(self.keywords) > 0:
            ans["keywords"] = " ".join(self.keywords)
        return ans

    def result(self) -> None:
        inject_command(self.command)

    @classmethod
    def from_dict(cls: Type[T], dic: Dict[str, Union[List[str], str]]) -> T:
        kws = cast(List[str], dic.get("keywords", []))
        cmd = cast(str, dic.get("command"))
        des = cast(str, dic.get("description", ""))
        return cls(kws, cmd, des)


class DebugSoldier(BaseCommand, BaseCommander):
    def __init__(self) -> None:
        self.info: Dict[str, Any] = {"theme": theme}
        self.score = -1000

    def match(self, keywords: List[str]) -> Iterable[DebugSoldier]:
        if len(keywords) == 1 and keywords[0] == "debug":
            yield self

    def str_command(self) -> str:
        return "Debug"

    def preview(self) -> Dict[str, str]:
        return {"print debug infomation": ""}

    def result(self) -> None:
        ans = {}
        for k, v in self.info.items():
            ans[k] = v.to_dict() if isinstance(v, Theme) else v
        pprint(ans)


class FileSoldier(BaseCommand, BaseCommander):
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

    def match(self, keywords: List[str]) -> Iterable[FileSoldier]:
        if find_kws_cmd(keywords, self.keywords, self.filename):
            yield self

    def _open(self) -> str:
        if self.filetype in file_viewer:
            return file_viewer[self.filetype]
        print(
            f"Warning: cannot find viewer for filetype: {self.filetype}, opening with `{file_viewer['default']}`"
        )
        return file_viewer["default"]

    def str_command(self) -> str:
        return f"edit {self.filename}"

    def preview(self) -> Dict[str, str]:
        ans = {
            "file": self.filename,
            "file type": self.filetype,
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
    def result(self) -> None:
        if isinstance(self.command, str):
            os.system(self.command)
        else:
            self.command()

    def str_command(self) -> str:
        if isinstance(self.command, str):
            ans = "run: " + self.command
        else:
            ans = self.command.__doc__
        return ans.splitlines()[0]

    def copy_clipboard(self) -> str:
        return ""


class Commander(BaseCommander):
    def __init__(self, commands: List[BaseCommander]) -> None:
        self._commands = commands

    def match(self, keywords: List[str]) -> Iterable[BaseCommand]:
        for cmdr in self._commands:
            for cmd in cmdr.match(keywords):
                yield cmd

    def append(self, cmd: BaseCommander) -> None:
        self._commands.append(cmd)


class LazyCommander(BaseLazyCommander):
    def __init__(self, commands: Iterable[BaseAsyncCommander]) -> None:
        self._commands = commands

    def match(self, keywords: List[str], queue: Queue[BaseCommand]) -> None:
        for c in self._commands:
            c.match(keywords, queue=queue)


class RunAsyncCommander(BaseLazyCommander):
    def __init__(self, commands: Iterable[BaseAsyncCommander]) -> None:
        self._commands = commands

    async def _match(self, keywords: List[str], queue: Queue[BaseCommand]) -> None:
        for c in asyncio.as_completed(
            [cmd.match(keywords, queue=queue) for cmd in self._commands]
        ):
            await c

    def match(self, keywords: List[str], queue: Queue[BaseCommand]) -> None:
        asyncio.run(self._match(keywords, queue))
