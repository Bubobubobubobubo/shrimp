---
title: Shrimp's native REPL
tag: configuration, editors
---

#shrimp comes with a built-in REPL (Read, Eval, Print, Loop) interface. There are two versions of it:
- **python**: the native Python Read Eval Print Loop, which is the default! It is the interpreter program that runs when you type `python` in your terminal, the same that normally executes your scripts.
- **ptpython**: a more advanced REPL with syntax highlighting, autocompletion, and other features. It can be configured more extensively from the [configuration file](/configuration/config_file/configuration_tour#editor).

Both should only be used directly for rapid prototyping and testing. For live coding performances, it is recommended to use a text editor with a #shrimp plugin or whatever can help you send Python code to a live REPL. You will continue to interact with the REPL but only indirectly to send code to it.