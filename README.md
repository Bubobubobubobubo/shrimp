# Baston

Baston is a very new project, started on June 29 2024. The end goal is to provide a simple and efficient framework for _live coding_ with Python: MIDI, OSC, etc. I'm trying to keep it as simple as possible, and to make it easy to use. For this reason, Ableton Link synchronisation is a must. `Baston` uses the same LinkClock package as [Sardine](https://sardine.raphaelforment.fr) but implements a different approach to the problem (_threaded_ clock vs _asyncio_ clock).

## Installation

To install this package in dev mode, please run the following command (Unix/MacOS):

```shell
python -m pip install -e .
```

It should install the required dependencies (`pyproject.toml`).

## Usage

`Baston` can be used both as a library and imported as a module:
- `from baston import *`: will import all `__init__.py` without `__main__.py`.
- `python -m baston`: will import both consequently, start a new interpreter.
