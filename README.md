# YesCommander

This is a python-based bash command snippet tool.

## Install

```
python3 setup.py install
```

## Usage

### Search with an interactive interface

Input 
```
yc
```
in the command line directly.

## Interface

### `BaseCommand` class

- `def __contains__(self, keywords)->bool`
- `def str_command(self)->str`
- `def run(self)->None`
- `def copy_clipboard(self)->str`
- `def preview(self)`


### `Commander` class

- `def match(self, keywords)`

### List `commands`

The list, `commands`, in `yc_rc.py` consists of a bunch of `BaseCommand` objects.

## Free your imagination

### `TextFile` class

### Beautify

#### emoji
