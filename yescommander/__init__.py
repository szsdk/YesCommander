import json
import os
import itertools as it
import re
import sys
from tcolorpy import tcolor
from pathlib import Path

from .gui import *

__all__ = [
        'Command',
        'TextFile',
        'CommandRegister',
        'BaseCommand',
        ]


def inject_command(cmd):
    import fcntl, termios
    for c in cmd:
        fcntl.ioctl(sys.stdin, termios.TIOCSTI, c)

class CommandRegister(type):
    register = set()

    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)
        x._snake_name = CommandRegister.convert(name)
        cls.register.add(x)
        return x

    @staticmethod
    def convert(name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class BaseCommand(metaclass=CommandRegister):
    def __init__(self, key_words, command, description):
        if not isinstance(key_words, list):
            key_words = [key_words]
        self.key_words   = key_words
        self.command     = command
        self.description = description

    def __contains__(self, input_words):
        if not isinstance(input_words, list):
            input_words = [input_words]
        for k in input_words:
            findQ = False
            for kw in self.key_words:
                if k in kw:
                    findQ = True
            if findQ or (k in self.command):
                continue
            return False
        return True

    def str_command(self):
        return self.command

    copy = str_command

    def preview(self):
        return {'cmd': self.str_command(), "description":self.description, "key words": self.key_words}

    def result(self):
        raise NotImplementedError

def escape_all(s):
    s = "\\".join(s)
    return f"\\{s}"

class Command(BaseCommand):
    def result(self):
        inject_command(self.command)

def _from_tuple(t, *args, **kargs):
    if len(t) == 2:
        return Command(*t, "", *args, **kargs)
    elif len(t) == 3:
        return Command(t[0], t[1], t[2], *args, **kargs)
    else:
        raise ValueError("the len of command tuple should be 2 or 3")


def _from_dict(dic):
    kws = dic.get('keywords', [])
    cmd = dic.get('command')
    des = dic.get('description', '')
    return Command(kws, cmd, des)


def command(src, *args, **kargs):
    if isinstance(src, dict):
        return _from_dict(src)
    elif isinstance(src, tuple):
        return _from_tuple(src, *args, **kargs)


class TextFile(BaseCommand):
    editor = 'vim %s'
    def __init__(self, key_words, filename, description, *args, **kargs):
        super(TextFile, self).__init__(key_words, str(filename), description,
                )

    def result(self):
        os.system(self.editor % self.command)

class RunCommand(BaseCommand):
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

    def copy(self):
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
                if keywords in cmd:
                    ans.append(cmd)
            else:
                ans.extend(cmd.match(keywords))
        return ans

    def append(self, cmd):
        self._commands.append(cmd)

def commander(input_cmds):
    "initialize `_COMMANDS` list"
    "1. convert 2-tuple or 3-tuple elements in the `sc_rc.commands` into a"
    "`Command` object"
    "2. add `edit_cfg` for editting config file `sc_rc.py`"
    commands = []
    for i, arg in enumerate(input_cmds, 1):
        if isinstance(arg, tuple):
            cmd = command(arg)
        elif isinstance(arg, BaseCommand):
            cmd = arg
        cmd.index = i
        commands.append(cmd)
    return Commander(commands)


class CmdCommander(BaseCommander):
    def __init__(self, folder):
        self._cmds = {p.stem:p for p in Path(folder).rglob("*.json")}

    def match(self, keywords):
        if keywords[0] not in self._cmds:
            return []
        
        with self._cmds[keywords[0]].open() as fp:
            jcmds = json.load(fp)
        ans = []
        kw = keywords[1:]
        for cmd in map(command, jcmds):
            if kw in cmd:
                ans.append(cmd)
        return ans
