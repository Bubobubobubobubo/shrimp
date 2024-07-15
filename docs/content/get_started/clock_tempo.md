---
title: 3) Clock and Tempo
tag: get started, tutorial
---

## Clock basics

Everything you do in #shrimp is synchronized or relative to a clock. The clock is the heart of the system. It is the object that keeps track of time, that schedules events to take place. It is important to understand how the clock works and what you can expect from it!

### Getting / setting the tempo

To get the current tempo of the clock, you can use the `Clock` object:

```python
clock.tempo
```

To set the tempo of the clock, you can use the same object:

```python
clock.tempo = 120
```

The tempo is limited to a range of `20` to `999` BPM (beats per minute). If you try to set a tempo outside of this range, the tempo will be clamped to the nearest limit. This limitation is imposed by [Ableton Link](https://www.ableton.com/en/link/products/), the technology used by Shrimp to synchronize with other software and hardware.

### Play / pause the clock

You can start and stop the clock using the `play` and `pause` methods of the clock:

```python
clock.play()
```

Try evaluating this next and notice how events stop playing:

```python
clock.pause()
```

>[!tip] External play and pause
> You are not the only one who can play and pause the clock. Other peers on the local network using the same technology ([Ableton Link](https://www.ableton.com/en/link/products/)) can also play and pause the clock. This is useful when you want to synchronize with other musicians. Make sure that you are not sharing the same network with other people when you don't need to synchronize with them!

### Musical division of time

The clock follows a musical division of time. In other software, we often talk about the _transport_: bar, beat, phase, etc. You can request similar information from the clock:

```python
clock.bar   # current bar
clock.beat  # current beat
clock.phase # current phase
```

Some of these methods also have homonyms like `beat` and `now`:

```python
print(clock.now, clock.beat)
```

You can't directly set the bar, beat, or phase of the clock but you can indirectly control these values using the `play` and `pause` methods of the clock.

### About time signatures

Even though it is rarely used in Shrimp, you can set the time signature of the clock:

```python
clock.time_signature = (4, 4)
```

You can also get the current time signature:

```python
clock.time_signature
```

Internally, these values are used as `clock._nominator` and `clock._denominator` for several objects that need to know the time signature to compute properly. You very rarely interact with these values directly!

## Clock Synchronization

Shrimp is capable of synchronizing with other software and hardware using [Ableton Link](https://www.ableton.com/en/link/products/). This technology allows you to synchronize the tempo of Shrimp with other software and hardware on the same network. You also share some basic controls like play and pause. There is an important factor to consider when synchronizing with other software and hardware:
- **Latency**: the time it takes for your system to react to the changes on the network: tempo, play, pause, etc. The time it takes to play a note after you have sent some command, etc.

Getting perfect synchronization is hard, especially with Python which is not tailored for real-time usage.

### Link synchronization

Everytime you start #shrimp, it will start a Link session automatically and try to find peers on the local network. If it finds some, you enter a session. There is a method to prevent this behavior from happening. If you set `value` to `False`, you will prevent the software from entering a Link session. This is useful when you want to use #shrimp in a standalone mode.

```python
clock.sync(value: bool)
```

If you want to check if you are in a Link session and if other peers are detected, you can use the following property:

```python
clock.peers
```

Whenever you are in a Link session, the following events are synchronized with the peers:
- **Tempo changes**: changing the tempo will change the tempo of the peers and vice-versa.
- **Play and pause**: playing and pausing the clock will play and pause the peers and vice-versa.

### MIDI synchronization

>[!warning] To implement! 
> I have no desire to implement this feature. Please let me know if you want to contribute or why it should be reconsidered. The instructions above will _approximate_ the behavior of MIDI clock send. It does not cover receiving a clock!

There is no official support for MIDI synchronization in Shrimp. However, you can _fake it_ by sending MIDI clock messages to your hardware synthesizer. Don't expect perfection though! MIDI is not a very reliable protocol for synchronization and nailing it perfectly, especially with Python, is hard.

If you want to send MIDI clock messages to your hardware synthesizer, you can use the following method. I'm assuming that your MIDI interface is correctly configured and named `midi`. Let's start by sending a start message:

```python
midi.start()
```

Then let's send clock messages fast enough to make your synthesizer happy:

```python
p1 >> tick(p=1/24)
```

Finally, you can stop the clock by sending a stop message:

```python
midi.stop()
```

### Correcting eventual delays

Even though the clock synchronization is perfect, there is always a delay between the moment you send commands and the moment they are executed. Sometimes, the simplest solution is just to shift the clock a little bit. You can do this by setting the `delay` property of the clock:

```python
clock.delay = -8
```
>[!tip] This number must be an integer! It can be positive or negative.

Each and every `Sender` can also be delayed individually. To do so, use the `nudge` property of each `Sender`. The `nudge` value should always be positive, and is expressed in seconds:
.

```python
midi.nudge = 0.1
dirt.nudge = 0.2
```
>[!tip] This is a last resort solution! Do not use it unless you have no other choice!

