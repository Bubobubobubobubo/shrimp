---
title: Installing on MacOS
tag: installation, macos
---

Installing Shrimp on MacOS is very straightforward. I'll guide you through the process and take a special attention to the details. Skip them if you're already familiar with the installation of Python packages and/or programming in Python in general.

## Installing Python

Python is the programming language that **Shrimp** is built on. You need to have Python installed on your system to run Shrimp. Shrimp requires Python 3.11 or later. I encourage you to install the latest version of Python, which is 3.12 at the time of writing this documentation.

1. Install [Python 3.11](https://www.python.org/downloads/) or later. Use [brew](https://brew.sh/) to install it if you know how to use it.
2. Check if Python is installed by running `python3 --version` in your terminal. You should see the version of Python you installed. Do not use `python`, as it may refer to Python 2.x or to another version of Python used by your system.

>[!info]-**Beginners:** Name of the Python command
> Sometimes, the Python command is named `python3`, sometimes it is named `python`. Make sure to use the right command when running Python. It is extremely common to have multiple versions of Python installed on your system. Just make sure to use the right one, _all the time_.

>[!info]-**Advanced:** Pyenv can be useful
> Pyenv is a tool that allows you to manage multiple versions of Python on your system. It is very useful when you need to switch between different versions of Python. You can install it by following the instructions on the [Pyenv GitHub page](https://github.com/pyenv/pyenv). This is what I use on my system, and I highly recommend it. However, make sure not to use it as an alternative for virtual environments.


## Installing Shrimp

This is the easiest part. You can install Shrimp using `pip`, the Python package manager. Run the following command in your terminal:

```bash
python -m pip install shrimp
```

If everything goes well, you should see a message saying that Shrimp was successfully installed. You can now use Shrimp in your Python environment. Please close your terminal and open it again to make sure that the changes take effect.

## Testing your installation

Open a fresh terminal and run the following command:

```bash
python -m shrimp
```

You should see the Shrimp prompt, without any error messages. You can now start using Shrimp in your Python environment. Follow the [Getting Started](/getting-started) guide to learn how to use Shrimp.