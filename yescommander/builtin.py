import math
from pprint import pprint
from typing import Any, Dict, List, Optional, Tuple, cast

from . import BaseCommand, BaseCommander, file_viewer, inject_command, theme


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
