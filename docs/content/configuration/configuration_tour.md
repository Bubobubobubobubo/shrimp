---
title: 2) Configuration Tour
tag: configuration, technical
---

Let's break down the configuration file in detail and study each section. Please note that you are also able to alter the configuration of everything at runtime but the default values will always fallback to those set in this file.

## Clock

This section is used to configure the clock settings in #shrimp. The clock is used to control the tempo of the music and the time grain of the sequencer.

```json title="config.json"
"clock": {
    "default_tempo": 135,
    "time_grain": 0.01,
    "delay": 0
}
```

- `default_tempo` (`float`): The default clock tempo. It can also be changed at runtime.
- `time_grain` (`float`): The time grain of the clock.
- `delay` (`int`): clock delay in milliseconds, useful for syncing. It can also be negative.

> [!faq]- What is the time grain?
> The time grain determines how often events are processed in the sequencer. A smaller time grain will result in more precise timing but will also require more CPU resources. A larger time grain will result in less precise timing but will require fewer CPU resources. The time grain is a floating-point number that represents the time in seconds between each clock tick. The default time grain is 0.01 seconds.
>
> Play with it if you need to but be aware that it can have a significant impact on performance!



## Editor

This section is used to configure the REPL (Read, Eval, Print, Loop) settings in #shrimp.

```json title="config.json"
"editor": {
    "default_shell": "ptpython",
    "vim_mode": false,
    "print_above": false,
    "greeter": true
}
```

- `default_shell` (`string`): The default shell to use in the REPL. The available options are `ptpython`, `ipython`, and `python`.
    - `vim_mode` (`bool`): Enable or disable the vim mode for the `ptpython` REPL.
    - `print_above` (`bool`): Print the output above the input in the REPL.


> [!note]- Differences between `python` and `ptpython`?
> - `python` is the default REPL, with no special features like history or special keybindings. It is the most basic REPL available, but also the most reliable!
> - `ptpython` is a more advanced REPL that includes features like multiline editing, tab completion, history, and special keybindings. It is a good choice if you are familiar with IPython and want to use its features in #shrimp.


- `greeter` (`bool`): Enable or disable the greeter message.

> [!note]- What is the greeter?
> The greeter is the banner you see when you start the REPL. It contains the version number and some useful information about the software. It is also composed by various information about available OSC and MIDI ports.

## Audio Engine

The audio engine section is used to configure the audio engine used internally by Shrimp, [signalflow](https://signalflow.dev). It is only available for MacOS for the moment. It will be available for Linux and Windows as well soon enough.

```json title="config.json"
"audio_engine": {
    "sample_rate": 44100,
    "cpu_limit": 50,
    "output_buffer_size": 256,
    "input_buffer_size": 256,
    "output_backend_name": "auto"
}
```

- `sample_rate` (`int`): The sample rate of the audio engine.
- `cpu_limit` (`int`): The maximum percentage of CPU that the audio engine can use.
- `output_buffer_size` (`int`): The size of the output buffer in samples.
- `input_buffer_size` (`int`): The size of the input buffer in samples.
- `output_backend_name` (`string`): The name of the output backend to use.

>[!faq]- What are the available output backends?
> The available output backends are `jack`, `alsa`, `pulseaudio`, `coreaudio`, `wasapi` and `dummy`.
> Check the [signalflow documentation](https://signalflow.dev/graph/config/) for more information.