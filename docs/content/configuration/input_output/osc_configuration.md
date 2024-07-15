---
title: Configuring OSC
tag: configuration, osc, technical, supercollider, superdirt
---

Configuring [OSC](https://en.wikipedia.org/wiki/Open_Sound_Control) (Open Sound Control) connexions in #shrimp is done through the [configuration](configuration_file.md) file. OSC is a protocol for communication among computers, sound synthesizers, and other multimedia devices. It is particularly useful for sending and receiving messages between software applications and is often used in everything related to audio and video applications. Shrimp uses OSC to communicate with [SuperDirt](./superdirt.md) by default ([SuperCollider](https://supercollider.github.io)).

## Configuring OSC

The OSC configuration section in the `config.json` file will likely look like this the first time you open it:

```json title="config.json"
"osc": {
    "ports": {
        "superdirt": {
            "host": "127.0.0.1",
            "port": 57120,
            "name": "SuperDirt"
        }
    }
},
```

You can see that there is already a port defined for [SuperDirt](./superdirt.md). You can add more ports by adding more objects to the `ports` list. Here is a breakdown of the keys in the object:

- `superdirt`: The user name of the OSC port.
- `host`: The IP address of the host computer.
- `port`: The port number (from 0 to 65535).
- `name`: The real name of the OSC port.

## Timestamping

If you are using [SuperCollider](supercollider.md) with Shrimp, you will have to care for OSC messages timestamping. SuperDirt uses timestamps to get the right timing for audio playback. Shrimp emits SuperDirt messages with a timestamp a little bit in the future to ensure that the messages can be received and played at the right time. This is why you will see a delay between the moment you send a message and the moment you hear the sound. You can fine-tune this delay by changing the `nudge` on your OSC port.

Let's imagine that our SuperDirt port is named `superdirt`. You can run this command in Shrimp to change the `nudge` value:

```python
superdirt.nudge = 0.1
```

