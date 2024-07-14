# Shrimp

Shrimp is a very new project, started on June 29 2024. The end goal is to provide a simple and efficient framework for _live coding_ music with Python: MIDI, OSC, etc. I'm trying to keep it as simple as possible and to make it easy to use for everyone. Shrimp uses Ableton Link for synchronisation with other softwares and devices. It comes with a timing system and a pattern scheduling system.  Check out the tutorials section!

**Features**:
- networked clock (_Ableton Link_) for synchronisation and sequencing in time.
- pattern scheduling system for easy and efficient time-reactive code.
- MIDI and OSC support for live coding music. More protocols to come.
- State of the art REPL (_Read, Eval, Print, Loop_) with goodies (history, vi mode).
- easy to use and to understand, with a focus on simplicity and efficiency.

![](images/shrimp_shell.png)

## Installation

To install this package in dev mode, please run the following command (Unix/MacOS):

```shell
python -m pip install -e .
```

It should install the required dependencies (specified in `pyproject.toml`). Please note that I am targetting Python 3.11+ for an eventual release. Make sure you have the required version of Python installed on your machine. Use [pyenv](https://github.com/pyenv/pyenv) or virtual environments if you know how to use them.

### Usage

`Shrimp` can be used both as a library and imported as a module:
- `from shrimp import *`: will import all `__init__.py` without `__main__.py`.
- `python -m shrimp`: will import both consequently, start a new interpreter.

The central piece is the `clock` instance that will let you schedule recursive functions easily. You can use this mechanism to build time-reactive code, data sequences, etc. Importing Shrimp as a library is like importing Shrimp without its interactive REPL (_Read, Eval, Print, Loop_).

### Learning

There are tutorials available in the `tutorials/` folder. The tutorials are using Python Notebook as a convenient way to mingle text and code. You can run them using Jupyter Notebook or Jupyter Lab. You can also pre-visualize them on GitHub, how convenient!

The `examples/` folder contains examples of using Shrimp as a library. You can run each example using your Python interpreter. The examples are meant to be simple and to the point. They are also meant to be easy to understand and to modify.

### Contributing

Please report any issue you might encounter, I will be happy to help you out. I am also open to any suggestion or feature request. I am looking for contributors to work on this project :smile:.

I am developing free and open source software on my own. Please consider supporting me on [Ko-fi](https://ko-fi.com/I2I2RSBHF) if you like my work. It will help me to keep going and to improve my projects. Thank you!
<br>
<p align="center">
  <a href='https://ko-fi.com/I2I2RSBHF' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi3.png?v=3' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>
</p>
