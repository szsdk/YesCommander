import re
import tty
import sys
import term
import termios
from getkey import keys
from tcolorpy import tcolor

__all__ = ["Window", "TextBox", "ListBox", "ListBoxData", "LabelBox", "StyledStr"]


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
        self._widgets = []

    def clear(self):
        term.pos(*self.origin)
        for _ in range(self.height):
            term.clearLine()
            term.down(1)
        term.pos(*self.origin)

    def addWidget(self, widget):
        self._widgets.append(widget)

    def draw(self):
        self.clear()
        for w in self._widgets:
            w.draw()


class TextBox:
    def __init__(self, parent: Window, line):
        self.text = ""
        self._line = line + parent.origin[0]
        self.parent = parent
        self.parent.addWidget(self)

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

    def getSelection(self):
        if len(self.commands) == 0:
            return None
        return self.commands[self._selected]


class StyledStr:
    def __init__(self, s, color=None, bg_color=None, styles=None):
        self.s = s
        self.color = color
        self.bg_color = bg_color
        styles = styles if styles is not None else []
        self.bold = "bold" in styles

    @property
    def styles(self):
        styles = []

        if self.bold:
            styles.append("bold")
        return styles

    def render(self):
        return tcolor(
            self.s, color=self.color, bg_color=self.bg_color, styles=self.styles
        )

    def __str__(self):
        return self.render()

    def splitlines(self):
        return [
            StyledStr(s, color=self.color, bg_color=self.bg_color, styles=self.styles)
            for s in self.s.splitlines()
        ]


class LabelBox:
    def __init__(self, parent, origin, width, height):
        self.parent = parent
        self.parent.addWidget(self)
        self.origin = origin
        self.width = width
        self.height = height
        self.text = []
        self.bg_color = "#DDDDDD"

    def setText(self, text):
        self.text = text

    def clear(self):
        for i in range(self.height):
            term.pos(self.origin[0] + i, self.origin[1])
            term.write(tcolor(" " * self.width, bg_color=self.bg_color))

    def draw(self):
        self.clear()
        term.pos(*self.origin)
        line = self.origin[0]
        for t in self.text:
            if isinstance(t, str):
                t = StyledStr(t, bg_color=self.bg_color)
            for l in t.splitlines():
                term.pos(line, self.origin[1])
                l.bg_color = self.bg_color
                term.write(l.render())
                line += 1


class ListBox:
    MARKER = "●"

    def __init__(self, listbox_data, parent: Window, line, height):
        self._line = line + parent.origin[0]
        self._data = listbox_data
        self.height = height
        self.parent = parent
        self.parent.addWidget(self)

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
                    f"\r"
                    + tcolor(f"{self.MARKER} {cmd.str_command()}", styles=["bold"])
                )
            else:
                term.write(f"\r{self.MARKER} {cmd.str_command()}")
