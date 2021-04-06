import re
import tty
import sys
import term
import termios
from getkey import keys
from tcolorpy import tcolor

__all__ = ["Window", "TextBox", "ListBox", "ListBoxData"]

def getpos():
    buf = ""
    stdin = sys.stdin.fileno()
    tattr = termios.tcgetattr(stdin)

    try:
        tty.setcbreak(stdin, termios.TCSANOW)
        sys.stdout.write("\x1b[6n")
        sys.stdout.flush()

        while True:
            buf += sys.stdin.read(1)
            if buf[-1] == "R":
                break

    finally:
        termios.tcsetattr(stdin, termios.TCSANOW, tattr)

    # reading the actual values, but what if a keystroke appears while reading
    # from stdin? As dirty work around, getpos() returns if this fails: None
    try:
        matches = re.search(r"\x1b\[(\d*);(\d*)R", buf)
        groups = matches.groups()
    except AttributeError:
        return None

    return (int(groups[0]), int(groups[1]))


class Window:
    def __init__(self, height):
        self.height = height
        for _ in range(height):
            print()
        term.up(height)
        self.origin = getpos()

    def clear(self):
        term.pos(*self.origin)
        for _ in range(self.height):
            term.clearLine()
            term.down(1)
        term.pos(*self.origin)


class TextBox:
    def __init__(self, parent: Window, line):
        self.text = ""
        self._line = line + parent.origin[0]
        self.parent = parent

    def draw(self):
        term.pos(self._line, 0)
        term.clearLine()
        term.write(self.text)

    def key(self, key):
        if key == keys.BACKSPACE:
            if len(self.text) > 0:
                self.text = self.text[:-1]
        else:
            self.text = self.text + key


class ListBoxData:
    def __init__(self):
        self.commands = []
        self._selected = 0

    def isSelected(self, i):
        if self._selected is None:
            return False
        return self._selected == i

    def selectNext(self):
        self._selected = (self._selected + 1) % len(self)

    def selectPrevious(self):
        self._selected = (self._selected - 1) % len(self)

    def getSelected(self):
        return self._selected

    def __len__(self):
        return len(self.commands)

    def __getitem__(self, idx):
        return self.commands[idx]


class ListBox:
    MARKER = "●"
    def __init__(self, listbox_data, parent: Window, line, height):
        self._line = line + parent.origin[0]
        self._data = listbox_data
        self.height = height
        self.parent = parent

    def _clear(self):
        term.pos(self._line - 1, 0)
        for i in range(self.height):
            term.down(1)
            term.clearLine()

    def draw(self):
        self._clear()
        term.pos(self._line - 1, 0)
        # get range
        selectedIndex = self._data.getSelected()
        halfHeight = self.height // 2
        if selectedIndex < halfHeight:
            start, end = 0, min(self.height, len(self._data))
        elif selectedIndex + halfHeight >= len(self._data):
            start, end = max(0, len(self._data) - self.height), len(self._data)
        else:
            start = max(0, selectedIndex - halfHeight)
            end = min(start + self.height, len(self._data))
        for i in range(start, end):
            cmd = self._data[i]
            term.down(1)
            if self._data.isSelected(i):
                term.write(
                    f"\r" + tcolor(f"{self.MARKER} {cmd.str_command()}", styles=["bold"])
                )
            else:
                term.write(f"\r{self.MARKER} {cmd.str_command()}")
        if len(self._data) > 0:
            pv = self._data[selectedIndex].preview()
            line = self._line
            shift_l = 50
            width = 50
            bg_color = "#CCCCCC"
            for l in pv['cmd'].splitlines():
                term.pos(line, shift_l)
                term.write(tcolor(" "*width, bg_color=bg_color))
                term.pos(line, shift_l)
                term.write(tcolor(l, bg_color=bg_color))
                line += 1
            if pv.get('description', '') != '':
                term.pos(line, shift_l)
                term.write(tcolor('description'.ljust(width) + '\n', bg_color=bg_color, color='green'))
                line += 1
                for l in pv['description'].splitlines():
                    term.pos(line, shift_l)
                    term.write(tcolor(" "*width, bg_color=bg_color))
                    term.pos(line, shift_l)
                    term.write(tcolor(l, bg_color=bg_color))
                    line += 1
            if len(pv.get('keywords', [])) > 0:
                term.pos(line, shift_l)
                term.write(tcolor("keywords".ljust(width) + "\n", bg_color=bg_color, color='green'))
                line += 1
                term.pos(line, shift_l)
                term.write(tcolor(", ".join(pv['keywords']), bg_color=bg_color))
