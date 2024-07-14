---
title: 2) Jupyter Notebooks
tag: configuration, editors, jupyter
---

## What are Jupyter Notebooks?

A [Jupyter Notebook](https://jupyter.org/) is a special document format that implements an interactive computing environment. It allows you to create and share documents that contain live code, visualizations, formatted text, etc. Notebooks are mostly used for scientific computing, data analysis, and machine learning nowadays. You can use these notebooks to write and manage your code. This is a great way to experiment and to do exploratory programming with Shrimp. I use it a lot to develop and test my ideas.

## Installing Jupyter

To install Jupyter, you need to have Python installed on your system. You can install Jupyter using `pip`, the Python package manager. Run the following command in your terminal:

```bash
python -m pip install notebook
```

If you want the JupyterLab interface, you can install it with the following command:

```bash
python -m pip install jupyterlab
```

This should be enough to get you started with Jupyter. 

### Using notebooks (standalone)

You can now run Jupyter by running the following command in your terminal:

```bash
jupyter notebook
```

This will open a new tab in your default web browser with the Jupyter interface. You can create a new notebook by clicking on the `New` button and selecting `Python 3` from the dropdown menu. You can now write and run your code in the notebook. Just make sure to import to Shrimp in your notebook to use it:

```python
from shrimp import *
```

### Using notebooks in VSCode

[Microsoft VSCode](https://code.visualstudio.com/) is a popular code editor that have native support for Jupyter Notebooks. There are also various Jupyter extensions and plugins to get more features. You can create a new notebook file by creating a `.ipynb` file. Just like before, import Shrimp in your notebook to use it:

```python
from shrimp import *
```
