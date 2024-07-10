---
title: Installing on Windows
tag: installation, windows
---

Installing Baston on Windows requires going through the command line. I'll guide you all along and take special attention to the details. Skip them if you're already familiar with the installation of Python packages and/or programming in Python in general. Before you begin the installation process, here are some important recommendations for Windows users:

1. **Use PowerShell**: While Command Prompt works, PowerShell offers a more robust experience. It's preinstalled on Windows 10 and later versions.

2. **Run as Administrator**: Some operations may require elevated privileges. Right-click on PowerShell or Command Prompt and select "Run as administrator" when needed.


## Installing Python

Python is the programming language that **Baston** is built on. You need to have Python installed on your system to run Baston. Baston requires Python 3.11 or later. I encourage you to install the latest version of Python, which is 3.12 at the time of writing this documentation.

1. Download and install [Python 3.11](https://www.python.org/downloads/windows/) or later. During installation, make sure to check the box that says "Add Python to PATH".
2. Check if Python is installed by opening Command Prompt and running `python --version`. You should see the version of Python you installed. 

>[!info]-**Beginners:** Name of the Python command
> On Windows, the Python command is typically just `python`. However, if you have multiple versions installed, you might need to use `py` or `python3`. Make sure to use the correct command when running Python. It is extremely common to have multiple versions of Python installed on your system. Just make sure to use the right one, *all the time*.

>[!info]-**Advanced:** Pyenv can be useful
> Pyenv is a tool that allows you to manage multiple versions of Python on your system. It is very useful when you need to switch between different versions of Python. You can install it by following the instructions on the [Pyenv GitHub page](https://github.com/pyenv/pyenv). This is what I use on my system, and I highly recommend it. However, make sure not to use it as an alternative for virtual environments.


## Installing Baston 
This is the easiest part. You can install Baston using `pip`, the Python package manager. Open Command Prompt and run the following command:

```bash
python -m pip install baston
```

If everything goes well, you should see a message saying that Baston was successfully installed. You can now use Baston in your Python environment. Please close your Command Prompt and open it again to make sure that the changes take effect.

### Testing your installation

Open a new Command Prompt and run the following command:

```bash
python -m baston
```

You should see the Baston prompt, without any error messages. You can now start using Baston in your Python environment. Follow the [[Getting Started]] guide to learn how to use Baston.

