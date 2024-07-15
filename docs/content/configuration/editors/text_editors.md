---
title: Choosing a Text Editor
tag: configuration, editors
---

Shrimp comes with an [REPL](./basic_repl.md) (_Read, Eval, Print, Loop_) that you can use to write and run your code. It is useful to experiment very fast without having to boot multiple software. However, you might want to use a code editor to be more comfortable in the long run. 

Support for Python in code editors is widespread, and you can use any code editor you like. The feature you are looking for is the ability to evaluate code blocks in a separate terminal. Here are some code editors that I recommend:


- [Microsoft VSCode](https://code.visualstudio.com/): the ubiquitous modern code editor by the fear inducing company Microsoft.
- [Vim](https://www.vim.org/) or [Neovim](https://neovim.io/): old school text editor for cool kids and hackers. I highly recommend using Neovim and learning Vim keybindings. This is a life changing experience.
- [Emacs](https://www.gnu.org/software/emacs/): Emacs is everything and optionally a text editor. It is a very powerful and extensible text editor. It is also a Lisp interpreter. You can do pretty much anything with it. It is a bit harder to learn than Vim, but it is worth it.

| <img src="https://code.visualstudio.com/assets/images/code-stable.png" width=200> | <img src="https://upload.wikimedia.org/wikipedia/commons/9/9f/Vimlogo.svg" width=200>   | <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Heckert_GNU_white.svg/langfr-1920px-Heckert_GNU_white.svg.png" width=200>  |
|---|---|---|

## VSCode

I have tried multiple techniques to live code with #shrimp in VSCode. Here are some tips:

- Make use of [Jupyter Notebooks](../editors/jupyter_notebook.md) to write and run your code. They are well supported.
- Map a keybinding to the `Run Selection in Python Terminal` shortcut in the command palette.
- Wait for a dedicated #shrimp extension for VSCode. This might be a thing in the future.

## Vim / Neovim

You will have to configure Vim to send code to a REPL. Neovim has native integration of the `terminal`. Here are some plugins that can help you setting up the perfect environment:

- [vim-slime](https://github.com/jpalardy/vim-slime) is a plugin that allows you to send code from Vim to a REPL (attached or distant). The initial setup can be a bit daunting. Read the instructions carefully and never think about it again.
- [iron.nvim](https://github.com/Vigemus/iron.nvim) is the same thing but more modern and featureful.

## Emacs

Emacs natively support sending various regions of code to an attached REPL. This feature is supported for Python as well in the various modes that have been developed for Python. Here are some of the most popular modes:
- [Elpy](https://elpy.readthedocs.io/en/latest/): Elpy is an Emacs package that brings powerful Python editing to Emacs. It combines and configures a number of other packages, both written in Emacs Lisp as well as Python.
- [jupyter](https://github.com/emacs-jupyter/jupyter) is an Emacs package that allows you to interact with Jupyter kernels. It is a bit more complex to set up than Elpy, but it is worth it if you are already using Jupyter Notebooks.