# Baston

Baston is a very new project, started on June 29 2024. The end goal is to provide a simple and efficient framework for _live coding_ with Python: MIDI, OSC, etc. I'm trying to keep it as simple as possible and to make it easy to use. For this very reason, Ableton Link synchronisation is a must. `Baston` uses the same LinkClock package as [Sardine](https://sardine.raphaelforment.fr) but implements a different approach to the problem (_threaded_ clock vs _asyncio_ clock).

## Installation

To install this package in dev mode, please run the following command (Unix/MacOS):

```shell
python -m pip install -e .
```

It should install the required dependencies (specified in `pyproject.toml`). Please note that I am targetting Python 3.11+ for an eventual release. 

### Usage

`Baston` can be used both as a library and imported as a module:
- `from baston import *`: will import all `__init__.py` without `__main__.py`.
- `python -m baston`: will import both consequently, start a new interpreter.

The central piece is the `clock` object that will let you schedule recursive functions. I use them as temporal primitives to build different systems, etc... The `env` (`Environment`) object is used to dispatch messages between all system components.

## Temporal recursion

To create a recursive function, study the following example:

```python

# Your regular Python function, with a final call to the scheduler
def demo_function(count: int = 0):
    print(f"Hello, I am recursive: {count})
    clock.add(demo_function, time=clock.beat + 1, count=count + 1)

# Start playing on the next bar
clock.add(demo_function, time=clock.next_bar())

# Start playing on the next beat
clock.add(demo_function, time=clock.next_beat())

# Start playing anytime really...
clock.add(demo_function, time=clock.beat + 2.23712)
```

There are multiple methods to stop a recursive function:

```python
# clear all functions running on the scheduler
clock.clear()
```

```python
# each *args will be removed from the scheduler
clock.remove(any, number, of, funcs)
```

If you peek into the `__init__.py` file, you will also see the prototype of a decorator (`@fight` because `baston` means `rumble` in french). This decorator is planned to automatically add a function to the scheduler as soon as the function is evaluated by the user. I would love to implement the opposite decorator, a `@stop` one, idk..
 

## Left to be implemented

This project is only a few hours old so there is still some work to do! The basics are here. Here is what I have in mind for the next steps:
- compensate for I/O late messages or any potential drifting (is there any? I think so)
- solid/robust `play` and `pause` methods that can be activated both local and remote. They are implemented already, play with them and see if they are to your liking.
- resetting the `beat/bar` count when `play` is pressed. Always a pain to implement correctly with Ableton Link.

Please report any issue you might encounter, I will be happy to help you out. I am also open to any suggestion or feature request. I would be delighted to collaborate with you on developing a solid synchronisation scheduling/sync mechanism for Python! It is long overdue...
