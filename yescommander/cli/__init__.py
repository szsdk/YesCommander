#!/usr/bin/env python

"""
This is the terminal interface of YesCommander.
"""

from __future__ import annotations

import time

STARTUP_t0 = time.time()
import multiprocessing
import sys

import yescommander as yc

from .. import copy_command, file_viewer, xdg
from ..commander import DebugSoldier
from ..theme import theme
from .utils import init_config_folder

multiprocessing.set_start_method("fork")
sys.path.insert(0, str(xdg.config_path))

load_rc_t0 = time.time()
try:
    import yc_rc
except ModuleNotFoundError as e:
    if "yc_rc" in str(e):
        init_config_folder()
    else:
        raise e
load_rc_t = time.time() - load_rc_t0

load_app_t0 = time.time()
from .app import init_app

load_app_t = time.time() - load_app_t0


def cli_main(chief_commander) -> None:
    app = init_app(chief_commander)

    debug_cmd = DebugSoldier()
    chief_commander.recruit(debug_cmd)
    debug_cmd.info["theme"] = theme.to_dict()
    debug_cmd.info.update(
        {
            "config file": str(xdg.config_path / "yc_rc.py"),
            "loading time (s)": {"cli app": load_app_t, "yc_rc": load_rc_t},
            "terminal size": app.terminal_size,
            "file type viewer": file_viewer,
            "layout mode": app.layout_mode,
        }
    )
    debug_cmd.info["loading time (s)"]["total"] = time.time() - STARTUP_t0

    command, action = app.run()
    if command is None:
        return
    if action == "run":
        return command.result()
    if action == "copy":
        return copy_command(command)


def _main():
    if hasattr(yc_rc, "main"):
        yc_rc.cli_main()
    else:
        cli_main(yc_rc.chief_commander)
