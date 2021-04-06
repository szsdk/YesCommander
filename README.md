# YesCommander

This is a python-based bash command snippet tool.

## Install

```
python3 setup.py install
```

## Usage

### Search in command line

```bash
sc [KEY_WORDS]
```

example:

```bash
sc ls
```

### Search with an interactive interface

Input 
```
sc
```
in the command line directly.

## Interface

### `Command` class

- `def __contains__(self, input_words)`
- `def str_command(self)`
- `def run(self)`
- `def duplicate(self)`

### `commands`

The list, `commands`, in `sc_rc.py` consists of objects which are `Command` or
`Command`'s subclass.

Well, not exactly. To simplify the `sc_rc.py`, you could also put a 2-tuple or
3-tuple into `commands`, which will be converted into `Command` object
automatically in `sc`.

## Free your imagination

### `TextFile` class

### Beautify

#### emoji
