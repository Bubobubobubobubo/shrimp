---
title: Configuration File
tag: configuration, technical
---

Shrimp uses a configuration file (`JSON` based) to store settings and user preferences. This file is created automatically when you run the Shrimp shell for the first time. It will also be updated if there is any missing configuration option in the current file. This file is stored in a special directory on your system, which is OS specific.

## Where is the configuration file?

The configuration file is stored in the following locations based on the operating system you are using:

- **Linux:** `~/.config/shrimp/config.json` 
- **Windows:** `%APPDATA%\shrimp\config.json`
- **MacOS:** `~/Library/Application Support/shrimp/config.json`

> [!note] Additional tip:
> This folder is hidden by default on most systems. You can access it by typing the path in the file manager or by using the terminal. Alternatively, you can use the `open_config_folder()` function. It will open the folder in the default file manager.

## How to edit the configuration file?

You can edit the configuration file using any text editor. Just make sure to follow the JSON format and to save the file correctly. Shrimp will not work if the configuration file is not correct, which is a good indicator that something is wrong!