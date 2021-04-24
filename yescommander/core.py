from queue import Queue
from typing import Dict, Iterable, List

__all__ = [
    "file_viewer",
    "BaseCommand",
    "BaseCommander",
    "BaseLazyCommander",
    "BaseAsyncCommander",
    "inject_command",
]


def inject_command(cmd: str) -> None:
    import fcntl
    import sys
    import termios

    for c in cmd:
        fcntl.ioctl(sys.stdin, termios.TIOCSTI, c.encode())


class BaseCommand:
    score: int

    def copy_clipboard(self) -> str:
        return ""

    def preview(self) -> Dict[str, str]:
        return {}

    def result(self) -> None:
        ...

    def str_command(self) -> str:
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


file_viewer = {"default": "vim %s"}
