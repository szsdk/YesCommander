from queue import Queue
from shutil import which

import pytest

import yescommander as yc


class CalculatorSoldier(yc.BaseCommand, yc.BaseCommander):
    def __init__(self):
        self.answer = None
        self._formula = ""
        self.marker = " "
        self.score = 100

    def order(self, keywords, queue):
        formula = "".join(keywords)
        self._formula = formula
        try:
            self.answer = str(eval(formula))
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
        yc.inject_command(str(self.answer))


def test_custom_soldier():
    c = CalculatorSoldier()
    q = Queue()
    c.order(["1+" "3"], q)
    assert c.answer == "4"


# @pytest.mark.skipif(which("googler") is None, reason="Cannot find googler.")
# def test_custom_async():
#     import asyncio
#
#     from yc_googler import GooglerAsyncCommander
#
#     q = Queue()
#     gg = GooglerAsyncCommander()
#     asyncio.run(gg.order(["hello"], q))
#     q.get()
