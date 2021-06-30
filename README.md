# YesCommander

This is a python-based command snippet tool.

## Install

```
pip install .
```

## Tutorial

### First step

```
yc
```
In the first time run this command, this command will write an example configure file, `yc_rc.py`
to `YesCommander`'s configure directory, `~/.config/yescommander`. The goal of this `yc_rc.py` is
to generate a `chief_commander` object.

Check the example `yc_rc.py` with
```
cat ~/.config/yescommander/yc_rc.py
```
The example config file looks like this:
```python
from typing import List

import yescommander as yc

commanders: List[yc.BaseCommander] = [
    yc.Soldier(keywords=["change"], command="chown user:group file", description=""),
    yc.Soldier.from_dict(
        {
            "keywords": ["ls", "seconds"],
            "command": "ls --time-style=full-iso -all",
            "description": "show time in nano second",
        }
    ),
]
chief_commander = yc.Commander(commanders)
```
Then run `yc` in command line again, you will get two command candidates to be
selected which are defined in `yc_rc.py`.

An useful snippet of using `commands.json` to compile your custom command collection looks like
this:
```python
import yescommander as yc
from pathlib import Path
config_folder = Path(__file__).parent
with (config_folder / "commands.json").open() as fp:
    commanders = [yc.Soldier.from_dict(c, score=100) for c in json.load(fp)]
chief_commander = yc.Commander(commanders)
```

**Trick:** since `yc_rc.py` is totally executable, a quick way to check the correctness of
`yc_rc.py` is directly running it.

### Layout and Shortcut

The layout of the `yc` consists of three parts:
1. searching textbox
2. command listbox
3. preview

There is a global variable `theme` in the `yescommander` library. You could try to put the
following code into your `yc_rc.py` to prettify your `yc` program.
```python
yc.theme.highlight_color = "#c84646"
yc.theme.marker_color = "#e18d01"
yc.RunSoldier.marker = " "
yc.theme.default_marker = "⚒ "
yc.theme.searchbox.prompt = "▶ "
yc.theme.preview.title_color = "#80986e"
yc.theme.preview.bg_color = "#e3d7b9"
yc.theme.preview.frame_color = "#838383"
yc.theme.preview.frame = False
yc.theme.color_depth = 24
```
The full definition of the `theme` variable is in `yescommander/theme.py`.

The shortcuts controlling `yc` are listed as following:

* Navigate:
    - `ctrl-j`/`down`/`tab`: select the next command
    - `ctrl-k`/`up`/`shift-tab`: select the previous command
    - `ctrl-n`: select the forth next command
    - `ctrl-p`: select the forth previous command
    - `ctrl-d`: view the next page
    - `ctrl-u`: view the previous page
* Execute
    - `enter`: execute a command
* Copy
    - `ctrl-y`: copy the command
* Exit
    - `escape`/`ctrl-c`: exit

## Basic of the package
This package consists of two parts: a python library `yescommander` and a terminal graphic
inference (TUI) application, `yc`. Its main idea could be summaried in one sentence:
> a commander gives commands.

The `yc` is just a interface for viewing and executing these commands given by `chief_commander`
defined by users in their `yc_rc.py` file.

The library mainly defines four protocol classes:
1. `BaseCommand`
2. `BaseCommander`
3. `BaseAsyncCommander`

### `BaseCommand`
Commands are objects which could be displayed (`__str__`), executed (`__run__`) or copied
(`copy_clipboard`) by `yc`. They inherit from the
base class `BaseCommand`.
```python
class BaseCommand:
    score: int  # Used for sorting. Higher score means higher preference.

    def copy_clipboard(self) -> str:
        """
        Return the string to be copied.
        """
        return ""

    def preview(self) -> Dict[str, str]:
        """
        Return a dictionary for previewing
        """
        return {}

    def result(self) -> None:
        """
        Action to be performed for the command.
        """
        ...

    def __str__(self) -> str:
        """
        Return the string for listing.
        """
        return ""
```

### `BaseCommander`
Commanders are objects implementing the `order` method (`BaseCommander`). This `order` method takes
a list of keywords as input, then yields commands. The `chief_commander` should be a
`BaseCommander`.
```python
class BaseCommander:
    """
    `BaseCommander` is a class which
    """

    def order(self, keywords: List[str]) -> Iterable[BaseCommand]:
        raise NotImplementedError()
```

### Execution mechanism and `BaseAsyncCommander`

A subprocess is forked to call all commanders in the `chief_commander` in order whenever the
seaching text is changed. There is a thread in the main process listening the `queue` which is
passed around over all commanders.

A common senario is that some long time IO operations are needed for a commander to generate
commands. For example, a google searching commander needs fetch information from the internet to
give commands, which may take few seconds. To cover the delay, the async mechanism of python is
utilized. The `BaseAsyncCommander` is defined as following
```python
class BaseAsyncCommander:
    """
    `BaseAsyncCommander` is a class which implements a **async** `order` method
    which has the same interface as `BaseCommander`'s.
    """

    async def order(self, keywords: List[str], queue: "Queue[BaseCommand]") -> None:
        raise NotImplementedError()
```

# TODO
- add examples: calculator, googler
- add mechanism about main function
