import textwrap
from tcolorpy import tcolor


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
        return [styled_str_from(s, self) for s in self.s.splitlines()]


def styled_str_from(text, base):
    return StyledStr(text, color=base.color, bg_color=base.bg_color, styles=base.styles)


def wrap(text: StyledStr, width=70, *args, **kargs):
    return [
        styled_str_from(t, text, *args, **kargs) for t in textwrap.wrap(text.s, width)
    ]


def shorten(text: StyledStr, width, **kargs):
    return styled_str_from(textwrap.shorten(text.s, width=width, **kargs), text)
