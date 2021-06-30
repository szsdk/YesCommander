import threading
import time
from pathlib import Path

import pytest
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from yescommander import xdg

xdg.config_path = Path(__file__).parent / "yc_config"
import yc_app


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
