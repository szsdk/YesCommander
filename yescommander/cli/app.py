import multiprocessing
import shutil
import sys
import threading
import time
from functools import partial
from queue import Empty
from typing import Any, Dict, List, Optional, Tuple, cast

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.layout.containers import (
    AnyContainer,
    Container,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.widgets import Frame

from .. import BaseCommand, theme, xdg


class Preview(Window):
    def __init__(
        self,
        width: int,
        height: Optional[int] = None,
        debug_mode: bool = False,
        **kargs: Any,
    ) -> None:
        super().__init__(
            content=FormattedTextControl(),
            width=width,
            height=height,
            wrap_lines=True,
            **kargs,
        )
        self.debug_mode = debug_mode

    def update(self, cmd: BaseCommand) -> None:
        ans = []
        for k, v in cmd.preview().items():
            ans.extend(
                [(theme.preview.title_color, k), ("", "\n"), ("", v), ("", "\n")]
            )
        if self.debug_mode:
            ans.extend(
                [
                    (theme.preview.title_color, "score (debug)"),
                    ("", "\n"),
                    ("", str(cmd.score)),
                    ("", "\n"),
                ]
            )
        cast(FormattedTextControl, self.content).text = FormattedText(ans)


class ListBoxData:
    def __init__(self) -> None:
        self.commands: List[BaseCommand] = []
        self._selected: int = 0

    def isSelected(self, i: int) -> bool:
        if self._selected is None:
            return False
        return self._selected == i

    def selectNext(self, num=1) -> None:
        self._selected = 0 if len(self) == 0 else (self._selected + num) % len(self)

    def selectPrevious(self, num=1) -> None:
        self.selectNext(-num)

    def getSelected(self) -> int:
        if self._selected == -1 and len(self.commands) > 0:
            self._selected = 0
        else:
            self._selected = min(self._selected, len(self.commands) - 1)
        return self._selected

    def __len__(self) -> int:
        return len(self.commands)

    def __getitem__(self, idx: int) -> BaseCommand:
        return self.commands[idx]

    def getSelection(self) -> Optional[BaseCommand]:
        if len(self.commands) == 0:
            return None
        return self.commands[self.getSelected()]

    def sorted(self) -> None:
        self.commands = sorted(self.commands, key=lambda x: x.score, reverse=True)


class ListBox(Window):
    def __init__(
        self, width: int, height: int, data: Optional[ListBoxData] = None, **kargs: Any
    ) -> None:
        super().__init__(
            content=FormattedTextControl(), width=width, height=height, **kargs
        )
        self._selected = 0
        if data is None:
            self.data = ListBoxData()
        else:
            self.data = data

    def get_start_end(self) -> Tuple[int, int]:
        selectedIndex = self.data.getSelected()
        height = cast(int, self.height)
        halfHeight = height // 2
        if selectedIndex < halfHeight:
            start, end = 0, min(height, len(self.data))
        elif selectedIndex + halfHeight >= len(self.data):
            start, end = max(0, len(self.data) - height), len(self.data)
        else:
            start = max(0, selectedIndex - halfHeight)
            end = min(start + height, len(self.data))
        return start, end

    def update(self) -> None:
        t = []
        self.data.sorted()
        selected_idx = self.data.getSelected()
        for i in range(*self.get_start_end()):
            cmd = self.data[i]
            t.append(
                (
                    theme.marker_color,
                    cmd.marker if hasattr(cmd, "marker") else theme.default_marker,  # type: ignore
                )
            )
            try:
                s = str(cmd).splitlines()[0]
            except NotImplementedError:
                s = cmd.formatted_str()  # type: ignore
                # This is an undocumented method.
            if isinstance(s, FormattedText):
                t.extend(s)
            else:
                t.append(
                    (
                        f"{theme.highlight_color} bold underline"
                        if selected_idx == i
                        else "",
                        s,
                    )
                )
            t.append(("", "\n"))
        self.content.text = FormattedText(t)  # type: ignore


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(
        self, app: "YCApplication", chief_commander, *args: Any, **kwargs: Any
    ) -> None:
        super(StoppableThread, self).__init__(*args, **kwargs)
        self.chief_commander = chief_commander
        self._stop_event = threading.Event()
        self._app = app

    def stop(self) -> None:
        self._stop_event.set()

    def stopped(self) -> bool:
        return self._stop_event.is_set()

    def run(self) -> None:

        searching_text = self._app.textbox_buffer.text
        keywords = searching_text.strip().split(" ")
        if len(searching_text.strip()) == 0:
            self._app.update([])
            return

        queue: "multiprocessing.Queue[BaseCommand]" = multiprocessing.Queue()
        proc = multiprocessing.Process(
            target=self.chief_commander.order, args=(keywords, queue)
        )
        proc.start()
        cmds = []
        while not self.stopped():
            updated = False
            try:
                for i in range(30):
                    cmds.append(queue.get(False))
                    updated = True
            except Empty:
                if not proc.is_alive():
                    time.sleep(0.1)
                pass
            if updated:
                self._app.update(cmds)
        proc.terminate()


class YCApplication(Application[None]):
    def __init__(self, chief_commander, width: int, height: int, **kargs: Any) -> None:
        self.textbox_buffer = Buffer(
            on_text_changed=self.searching_text_changed,
            multiline=False,
        )  # Editable buffer.
        self.textbox = Window(
            content=BufferControl(buffer=self.textbox_buffer),
            height=1,
            get_line_prefix=self.get_line_prefix,
        )
        self.debug_mode = "--debug" in sys.argv
        self.listdata = ListBoxData()
        self._chief_commander = chief_commander
        self._max_num = 2
        self.terminal_size = (width, height)
        root_container = self._init_ui(width, height)
        super().__init__(
            layout=Layout(root_container),
            full_screen=False,
            key_bindings=kb,
            erase_when_done=True,
            **kargs,
        )
        self._draw_thread = StoppableThread(self, self._chief_commander)

    def get_line_prefix(self, line_num, wrap_count):
        num_cmds = len(self.listdata)
        if num_cmds == 0:
            prompt = theme.searchbox.prompt
        else:
            idx = str(self.listdata.getSelected() + 1)
            num_cmds = str(num_cmds)
            self._max_num = max(self._max_num, len(idx), len(num_cmds))
            prompt = f"{idx.rjust(self._max_num)}/{num_cmds.ljust(self._max_num)} {theme.searchbox.prompt}"
        return FormattedText([(theme.highlight_color, prompt)])

    def _init_show_preview(self) -> AnyContainer:
        if not theme.preview.frame:
            return self.preview
        self.preview.width = cast(int, self.preview.width) - 2
        self.preview.height = cast(int, self.preview.height) - 2
        return Frame(
            self.preview,
            style=f"bg:{theme.preview.bg_color} fg:{theme.preview.frame_color}",
        )

    def _init_narrow(self, width: int, height: int) -> Container:
        if height < theme.narrow_height:
            raise RuntimeError(
                f"This terminal is too short {height} < {theme.narrow_height}"
            )

        self.preview = Preview(
            width=width,
            height=theme.preview.narrow_height,
            style=f"bg:{theme.preview.bg_color} fg:{theme.preview.fg_color}",
            debug_mode=self.debug_mode,
        )
        self.listbox = ListBox(
            width=width,
            height=theme.narrow_height - self.preview.height,
            data=self.listdata,
            style=f"bg:{theme.listbox.bg_color}",
        )
        root_container = HSplit([self._init_show_preview(), self.textbox, self.listbox])
        self.layout_mode = "narrow"
        return root_container

    def _init_wide(self, width: int, height: int) -> Container:
        if height < theme.wide_height:
            raise RuntimeError(
                f"This terminal is too short {height} < {theme.wide_height}"
            )
        self.preview = Preview(
            width=int(0.6 * width),
            height=theme.wide_height,
            style=f"bg:{theme.preview.bg_color} fg:{theme.preview.fg_color}",
            debug_mode=self.debug_mode,
        )
        self.listbox = ListBox(
            width=width - cast(int, self.preview.width),
            height=theme.wide_height - 1,
            data=self.listdata,
            style=f"bg:{theme.listbox.bg_color}",
        )

        root_container = HSplit(
            [
                self.textbox,
                VSplit([self.listbox, self._init_show_preview()]),
            ]
        )
        self.layout_mode = "wide"
        return root_container

    def _init_ui(self, width: int, height: int) -> Container:
        if width < theme.max_narrow_width:
            return self._init_narrow(width, height)
        else:
            return self._init_wide(width, height)

    def searching_text_changed(self, buf: Buffer) -> None:
        self._draw_thread.stop()
        if self._draw_thread.is_alive():
            self._draw_thread.join()
        self._draw_thread = StoppableThread(self, self._chief_commander)
        self._draw_thread.start()

    def update(self, commands: Optional[List[BaseCommand]] = None) -> None:
        if commands is not None:
            self.listdata.commands = commands
        self.listbox.update()
        selection = self.listdata.getSelection()
        if selection is not None:
            self.preview.update(selection)
        self.invalidate()

    def stop_draw(self) -> None:
        self._draw_thread.stop()


_color_depth = {
    24: ColorDepth.DEPTH_24_BIT,
    8: ColorDepth.DEPTH_8_BIT,
    4: ColorDepth.DEPTH_4_BIT,
    1: ColorDepth.DEPTH_1_BIT,
}


kb = KeyBindings()


def select_next_kernel(event: KeyPressEvent, n=1) -> None:
    app = cast(YCApplication, event.app)
    app.listdata.selectNext(n)
    app.update()
    app.invalidate()


def _exit_cmd(event, action, empty_result=False):
    app = cast(YCApplication, event.app)
    app.stop_draw()
    result = None if empty_result else app.listbox.data.getSelection()
    app.exit(result=(result, action))


def bind_keys(app):
    kb.add("c-d")(partial(select_next_kernel, n=app.listbox.height))
    kb.add("c-u")(partial(select_next_kernel, n=-app.listbox.height))
    kb.add("c-n")(partial(select_next_kernel, n=4))
    kb.add("c-p")(partial(select_next_kernel, n=-4))
    kb.add("enter")(partial(_exit_cmd, action="run"))
    kb.add("c-y")(partial(_exit_cmd, action="copy"))

    exit_ = partial(_exit_cmd, action="", empty_result=True)
    for keys in ["c-c", "escape"]:
        kb.add(keys)(exit_)

    next_1 = partial(select_next_kernel, n=1)
    for keys in ["c-j", "down", "tab"]:
        kb.add(keys)(next_1)

    previous_1 = partial(select_next_kernel, n=-1)
    for keys in ["c-k", "up", "s-tab"]:
        kb.add(keys)(previous_1)


def init_app(chief_commander, input=None, output=None):
    terminal_size = shutil.get_terminal_size((80, 20))

    app = YCApplication(
        chief_commander,
        terminal_size.columns,
        terminal_size.lines,
        color_depth=_color_depth[theme.color_depth],
        input=input,
        output=output,
    )
    app.ttimeoutlen = 0.01
    app.timeoutlen = 0.01
    bind_keys(app)

    return app
