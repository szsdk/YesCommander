# YesCommander

This is a python-based bash command snippet tool.

## Install

```
pip install .
```

## Tutorial

### First step

```
yc
```
In the first time run this command, this command will write an example
configure file, `yc_rc.py` to `YesCommander`'s configure directory,
`~/.config/yescommander`. The goal of this `yc_rc.py` is to generate two
variables: the `chief_commander` (a `yc.Commander` object) and the
`lazy_commander` (a `yc.LazyCommander` object).

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

# Commanders are charged by `lazy_commander` would be run in a different process.
lazy_commander = yc.LazyCommander([])
```
Then run `yc` in command line again, you will get two command candidates to be
selected which are defined in `yc_rc.py`.

- [ ] add a gif

### Shortcut

The shortcuts controlling `yc` are listed as following:

- `enter`: execute a command
- `ctrl-n`/`down`/`tab`: select the next command
- `ctrl-p`/`up`/`shift-tab`: select the previous command
- `ctrl-d`: view the next page
- `ctrl-u`: view the previous page
- `ctrl-y`: copy the command
- `escape`/`ctrl-c`: exit
