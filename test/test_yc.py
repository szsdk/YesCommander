from pathlib import Path
from queue import Queue

import yescommander as yc
from yescommander import xdg

xdg.config_path = Path(__file__).parent / "yc_config"
import threading
import time

import pytest
import yc_app
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput


def _typing_down(inp, n, end):
    inp.send_text("ls")
    time.sleep(0.2)
    for i in range(n):
        time.sleep(0.05)
        inp.send_text("\x0a")
    time.sleep(0.05)
    inp.send_text(end)


@pytest.mark.parametrize(
    "n, end, action, cmd_str",
    [(i, "\r", "run", f"cmd {i}") for i in range(3)]
    + [(i, "\x19", "copy", f"cmd {i}") for i in range(3)]
    + [(i, "\x03", "", "None") for i in range(3)]
    + [(i, "\x1B", "", "None") for i in range(3)],
)
def test_basic(n, end, action, cmd_str):
    inp = create_pipe_input()
    app = yc_app.init_app(input=inp, output=DummyOutput())
    t1 = threading.Thread(target=_typing_down, args=(inp, n, end))
    t1.start()
    command, act = app.run()
    t1.join()
    assert str(command) == cmd_str
    assert act == action
    inp.close()
    del t1


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
