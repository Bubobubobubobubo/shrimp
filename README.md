# Shrimp

Shrimp is a _very_ new project, started on June 29, 2024. The end goal is to provide a simple and efficient framework for _live coding_ music using Python for different protocols: MIDI, OSC, etc. I'm trying to keep as simple and lightweight as possible. Ideally, I'm striving to make easy to use. Shrimp uses Ableton Link for synchronisation with other softwares and devices. It comes with a timing system and several patterning notations. A documentation website already exists, currently kept private!

**Features**:
- **Time** : networked clock (_Ableton Link_) for synchronisation and sequencing in time.
- **I/O** : basic MIDI and OSC support. More protocols to come.
- **Pattern notations**:
  - [Vortex](https://github.com/tidalcycles/vortex) (renamed internally as _Carousel_)
  - My own system, very very WIP, inspired by SC.

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

### Learning (WIP, out of date)

There are basic tutorials available for the framework itself in the `tutorials/` folder. The tutorials are using Python Notebook as a convenient way to mingle text and code. You can run them using Jupyter Notebook or Jupyter Lab. You can also pre-visualize them on GitHub, how convenient!

The `examples/` folder contains examples of using Shrimp as a library. You can run each example using your Python interpreter. The examples are meant to be simple and to the point. They are also meant to be easy to understand and to modify.



### Credits and License

This software is licensed under the GNU Affero General Public License v3.0. Please refer to the `LICENSE` file for more information.

Many thanks to:
- @thegamecracks for maintaining the [LinkPython-Extern](https://pypi.org/project/LinkPython-extern/) dependency that I use for all my projects.
- The contributors of [Vortex](https://github.com/tidalcycles/vortex) for their work, and other folks from the TOPLAP community.

### Contributing

Please report any issue you might encounter, I will be happy to help you out. I am also open to any suggestion or feature request. I am looking for contributors to work on this project :smile:.

I am developing free and open source software on my own, without any financial support of help. Please consider supporting me on [Ko-fi](https://ko-fi.com/I2I2RSBHF) if you like my work. It will help me to keep going and to improve my projects. Thank you!
<br>
<p align="center">
  <a href='https://ko-fi.com/I2I2RSBHF' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi3.png?v=3' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>
</p>