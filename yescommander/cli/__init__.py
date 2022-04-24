#!/usr/bin/env python

"""
This is the terminal interface of YesCommander.
"""

from __future__ import annotations

import multiprocessing
import shutil
import sys
import threading
import time
from functools import partial
from pprint import pprint
from queue import Empty
from typing import Any, Dict, List, Optional, Tuple, cast

import yescommander as yc
from yescommander import cli, xdg

from .app import init_app
from .utils import copy_cmd

multiprocessing.set_start_method("fork")

sys.path.insert(0, str(xdg.config_path))

from .utils import init_config_folder

load_rc_t0 = time.time()
try:
    import yc_rc
except ModuleNotFoundError as e:
    if "yc_rc" in str(e):
        init_config_folder()
    else:
        raise e
load_rc_t = time.time() - load_rc_t0


def cli_main(chief_commander) -> None:
    app = init_app(chief_commander)
    command, action = app.run()
    if command is None:
        return
    if action == "run":
        return command.result()
    if action == "copy":
        return copy_cmd(command)


def _main():
    if hasattr(yc_rc, "main"):
        yc_rc.cli_main()
    else:
        cli_main(yc_rc.chief_commander)
