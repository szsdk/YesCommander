from typing import Iterable
import os
import asyncio

__all__ = [
    "file_viewer",
    "BaseCommand",
    "Soldier",
    "RunSoldier",
    "FileSoldier",
    "BaseCommander",
    "Commander",
    "BaseLazyCommander",
    "BaseAsyncCommander",
    "LazyCommander",
    "RunAsyncCommander",
    "DebugSoldier",
    "theme",
    "inject_command",
]


class Theme(dict):
    """dot.notation access to dictionary attributes"""

    def __getattr__(self, attr):
        if attr not in self:
            raise KeyError(attr)
        return dict.get(self, attr)

    __setattr__ = dict.__setitem__  # type: ignore
    __delattr__ = dict.__delitem__  # type: ignore


theme = Theme()
theme.marker_color = ""
theme.preview = Theme()
theme.preview.bg_color = ""
theme.preview.title_color = ""
theme.preview.frame_color = "black"
theme.default_marker = "- "
theme.preview.frame = True
theme.preview.narrow_height = 8  # Used for narrow layout
theme.searchbox = Theme()
theme.searchbox.prompt = "> "
theme.listbox = Theme()
theme.listbox.ratio = 0.4
theme.listbox.highlight_color = ""
theme.listbox.bg_color = ""
theme.max_narrow_width = 80
theme.wide_height = 20
theme.narrow_height = 20
theme.highlight_color = "grey"
theme.color_depth = 24
# TODO: Add more ui size control parameters


def inject_command(cmd):
    import fcntl, termios
    import sys

    for c in cmd:
        fcntl.ioctl(sys.stdin, termios.TIOCSTI, c)


class BaseCommand:
    score: int

    def copy_clipboard(self) -> str:
        ...

    def preview(self) -> dict:
        ...

    def result(self) -> None:
        ...


class BaseCommander:
    def match(self, keywords) -> Iterable[BaseCommand]:
        raise NotImplementedError()


def find_kws_cmd(input_words, keywords, command):
    for k in input_words:
        findQ = False
        for kw in keywords:
            if k in kw:
                findQ = True
        if findQ or (k in command):
            continue
        return False
    return True


class BaseLazyCommander:
    def match(self, keywords, queue) -> None:
        raise NotImplementedError()


class BaseAsyncCommander:
    async def match(self, keywords, queue) -> None:
        raise NotImplementedError()


class Soldier(BaseCommand, BaseCommander):
    def __init__(self, keywords, command, description, score=50):
        if not isinstance(keywords, list):
            keywords = [keywords]
        self.keywords = keywords
        self.command = command
        self.description = description
        self.score = score

    def match(self, input_words):
        if find_kws_cmd(input_words, self.keywords, self.command):
            yield self

    def str_command(self):
        return self.command

    def copy_clipboard(self):
        return self.str_command()

    def preview(self):
        ans = {"command": self.str_command()}
        if len(self.description) > 0:
            ans["description"] = self.description
        if len(self.keywords) > 0:
            ans["keywords"] = " ".join(self.keywords)
        return ans

    def result(self):
        inject_command(self.command)

    @classmethod
    def from_dict(cls, dic):
        kws = dic.get("keywords", [])
        cmd = dic.get("command")
        des = dic.get("description", "")
        return cls(kws, cmd, des)


class DebugSoldier(BaseCommand, BaseCommander):
    def __init__(self):
        self.info = {"theme": theme}
        self.score = -1000

    def match(self, keywords):
        if len(keywords) == 1 and keywords[0] == "debug":
            yield self

    def str_command(self):
        return "Debug"

    def preview(self):
        return {"print debug infomation": ""}

    def result(self):
        from pprint import pprint

        pprint(self.info)


file_viewer = {"default": "vim %s"}


class FileSoldier(BaseCommand, BaseCommander):
    def __init__(
        self, keywords, filename: str, description: str, filetype: str, score=50
    ):

        self.keywords = keywords
        self.filename = str(filename)
        self.description = str(description)
        self.filetype = str(filetype)
        self.score = score

    def match(self, keywords):
        if find_kws_cmd(keywords, self.keywords, self.filename):
            yield self

    def _open(self):
        if self.filetype in file_viewer:
            return file_viewer[self.filetype]
        print(
            f"Warning: cannot find viewer for filetype: {self.filetype}, opening with `{file_viewer['default']}`"
        )
        return file_viewer["default"]

    def str_command(self):
        return f"edit {self.filename}"

    def preview(self):
        ans = {
            "file": self.filename,
            "file type": self.filetype,
        }
        if self.description != "":
            ans["description"] = self.description
        if len(self.keywords) > 0:
            ans["keywords"] = " ".join(self.keywords)
        return ans

    def copy_clipboard(self):
        return self.filename

    def result(self):
        os.system(self._open() % self.filename)


class RunSoldier(Soldier):
    def result(self):
        if isinstance(self.command, str):
            os.system(self.command)
        else:
            self.command()

    def str_command(self):
        if isinstance(self.command, str):
            ans = "run: " + self.command
        else:
            ans = self.command.__doc__
        return ans.splitlines()[0]

    def copy_clipboard(self):
        return ""


class Commander(BaseCommander):
    def __init__(self, commands):
        self._commands = commands

    def match(self, keywords):
        for cmdr in self._commands:
            for cmd in cmdr.match(keywords):
                yield cmd

    def append(self, cmd):
        self._commands.append(cmd)


class LazyCommander(BaseLazyCommander):
    def __init__(self, commands):
        self._commands = commands

    def match(self, keywords, queue):
        for c in self._commands:
            c.match(keywords, queue=queue)


class RunAsyncCommander(BaseLazyCommander):
    def __init__(self, commands):
        self._commands = commands

    async def _match(self, keywords, queue):
        for c in asyncio.as_completed(
            [cmd.match(keywords, queue=queue) for cmd in self._commands]
        ):
            await c

    def match(self, keywords, queue):
        asyncio.run(self._match(keywords, queue))
