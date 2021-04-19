import json
import os
import sys
from pathlib import Path
import concurrent.futures

__all__ = [
    "BaseCommand",
    "Command",
    "command",
    "RunCommand",
    "FileCommand",
    "BaseCommander",
    "Commander",
    "BaseLazyCommander",
    "LazyCommander",
    "RunAsyncCommander",
    "commander",
    "DebugCommand",
    "default_executor",
    "theme",
]

default_executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)


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
# TODO: Add more ui size control parameters


def inject_command(cmd):
    import fcntl, termios

    for c in cmd:
        fcntl.ioctl(sys.stdin, termios.TIOCSTI, c)


class BaseCommand:
    def match(self, keywords) -> bool:
        return False

    def copy_clipboard(self) -> str:
        return ""

    def preview(self) -> dict:
        return {}

    def result(self) -> None:
        ...


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


class Command(BaseCommand):
    def __init__(self, keywords, command, description):
        if not isinstance(keywords, list):
            keywords = [keywords]
        self.keywords = keywords
        self.command = command
        self.description = description

    def match(self, input_words):
        return find_kws_cmd(input_words, self.keywords, self.command)

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


class DebugCommand(BaseCommand):
    def __init__(self):
        self.info = {"theme": theme}

    def match(self, keywords):
        return len(keywords) == 1 and keywords[0] == "debug"

    def str_command(self):
        return "Debug"

    def preview(self):
        return {"print debug infomation": ""}

    def result(self):
        from pprint import pprint

        pprint(self.info)


def _from_tuple(t, *args, **kargs):
    if len(t) == 2:
        return Command(*t, "", *args, **kargs)
    elif len(t) == 3:
        return Command(t[0], t[1], t[2], *args, **kargs)
    else:
        raise ValueError("the len of command tuple should be 2 or 3")


def _from_dict(dic):
    kws = dic.get("keywords", [])
    cmd = dic.get("command")
    des = dic.get("description", "")
    return Command(kws, cmd, des)


def command(src, *args, **kargs):
    if isinstance(src, dict):
        return _from_dict(src)
    elif isinstance(src, tuple):
        return _from_tuple(src, *args, **kargs)


class FileCommand(BaseCommand):
    # editor = "vim %s"
    viewer = {"default": "vim %s"}

    def __init__(self, keywords, filename: str, description: str, filetype: str):

        self.keywords = keywords
        self.filename = str(filename)
        self.description = str(description)
        self.filetype = str(filetype)

    def match(self, keywords):
        return find_kws_cmd(keywords, self.keywords, self.filename)

    def _open(self):
        if self.filetype in self.viewer:
            return self.viewer[self.filetype]
        return self.viewer["default"]

    def str_command(self):
        return f"edit {self.filename}"

    def preview(self):
        ans = {
            "file": self.filename,
            "file type": self.filetype,
            "open command": self._open(),
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


class RunCommand(Command):
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


class BaseCommander:
    def match(self, keywords):
        raise NotImplementedError()


class Commander(BaseCommander):
    def __init__(self, commands):
        self._commands = commands

    def match(self, keywords):
        ans = []
        for cmd in self._commands:
            if isinstance(cmd, BaseCommand):
                if cmd.match(keywords):
                    ans.append(cmd)
            else:
                ans.extend(cmd.match(keywords))
        return ans

    def append(self, cmd):
        self._commands.append(cmd)


class BaseLazyCommander:
    def match(self, keywords, queue):
        raise NotImplementedError()


class LazyCommander(BaseLazyCommander):
    def __init__(self, commands):
        self._commands = commands

    def match(self, keywords, queue):
        for c in self._commands:
            if isinstance(c, BaseLazyCommander):
                c.match(keywords, queue=queue)
            elif isinstance(c, BaseCommand):
                if c.match(keywords):
                    queue.put(c)
        default_executor.shutdown(wait=True)


class RunAsyncCommander(BaseLazyCommander):
    def __init__(self, commands):
        self._commands = commands

    async def _single_match(self, cmd, keywords, queue):
        if isinstance(cmd, BaseLazyCommander):
            await cmd.match(keywords, queue=queue)
        elif isinstance(cmd, BaseCommand):
            if await cmd.match(keywords):
                queue.put(cmd)

    async def _match(self, keywords, queue):
        import asyncio

        for c in asyncio.as_completed(
            [self._single_match(cmd, keywords, queue) for cmd in self._commands]
        ):
            await c

    def match(self, keywords, queue):
        import asyncio

        asyncio.run(self._match(keywords, queue))


def commander(input_cmds):
    commands = []
    for i, arg in enumerate(input_cmds, 1):
        if isinstance(arg, tuple):
            cmd = command(arg)
        elif isinstance(arg, BaseCommand):
            cmd = arg
        cmd.index = i
        commands.append(cmd)
    return Commander(commands)
