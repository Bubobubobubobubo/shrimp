---
title: 3) Configuring MIDI
tag: configuration, midi, technical
---

Configuring MIDI in #baston is done through the [configuration](configuration_file.md) file. The MIDI configuration section is located at the top of the `config.json` file. There are some important things to know about MIDI setup, and the process can vary based on your operating system.

## Configuring MIDI

The MIDI configuration section in the `config.json` file will likely look like this the first time you open it:

```json title="config.json"
"midi": {
    "out_ports": [
        {
            "midi": "baston",
            "instruments": [],
            "controllers": []
        }
    ],
    "in_ports": {
        "midi_in": "baston"
    }
}
```

Depending on your OS, the value of the `midi` key might be different by default:
- On **MacOS** and **Linux**, the default value is `"baston"`.
- On **Windows**, the default value is `false`.

This is because MacOS and Linux are allowing Baston to create a virtual MIDI port named `baston`. It is super convenient to identify the port in your other software. Windows does not allow Baston to create a virtual MIDI port, so the default value is `false` (not activated). Please check the [Windows section](#setting-up-on-windows) for more information.

### Output ports

Each output port is an object that look like this:

```json title="Output MIDI Port Object"
{
    "midi": "baston",
    "instruments": [],
    "controllers": []
}
```

- `midi`: The user name and real name of the MIDI output port.
- `instruments`: a list of [MIDI Instruments](midi_instruments.md) that will be defined for this output port.
- `controllers`: a list of [MIDI Controllers](midi_controllers.md) that will be defined for this output port.

> [!warning] Title
> The key (`"midi"`) is the name you will use in code to refer to the MIDI port. The value (`"baston"`) is the _real name_ of the MIDI port used by your operating system. To known which ports are available, run the `list_midi_ports()` command. The command will return a list (_e.g._ `['MIDI Bus 1', 'MIDI Bus 2', 'baston']`). Replace the value with the name of the port you want to use. 

You can create as many output ports as you need. Just add more objects to the `out_ports` list.

### Input ports

The input port is an object that looks like this:

```json title="Input MIDI Port Object"
{
    "midi_in": "baston"
}
```

It is similar to the output port object, but it only has the `midi` key. The value is the name of the MIDI input port you want to use. The same rules apply as for the output port.

You can create as many input ports as you need. Just add more objects to the `in_ports` list.

## Fine-tuning latency

If you are used to working with MIDI, you know how tedious it can be to deal with MIDI latency. Baston allows you to set the latency for each MIDI port at runtime. Imagine that we have a port named `midi`. We can set a nudge (in seconds) for this port by running the following command:

```python
midi.nudge = 0.1 # 10ms nudge forward
```


## Setting up on Windows

Windows does not allow Baston to create a virtual MIDI port. You will need to use a third-party software to create one. We recommend using [LoopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html) to create as many as you may need. Once you have installed LoopMIDI, you can resume the MIDI setup process by using the newly created ports.
