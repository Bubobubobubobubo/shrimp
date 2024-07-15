---
title: The Player object
tag: reference, Player
---

## Introduction

The [Player](/reference/player/player.md) object is the main object that you will interact with when using #shrimp. This object can receive [Senders](/reference/senders/sender) and play various types of events: MIDI notes, controls, OSC messages, etc. It is packing a lot of features and it might take some time to learn everything about it.

### About Player names

By default, there are 40 players in #shrimp. They are labelled from `p1` to `p19` (lowercase) and from `P1` to `P19` (uppercase). You can access them by their name in the global scope. For example, to play a note with player `p1`, you can write:

```python
p1 >> note(50)
p1.stop()
```

### Creating a new Player

Be mindful not to overwrite the player names with other variables. If you do, the player will be lost until you restart the REPL. You can create a new player using the following syntax:

```python 
# Creating a new player named "dada"
aa = Player.create_player(name="dada", name=clock)
```

### Accessing Player data

You can get data from another Player by using the `key` method. Please make sure to request the right key, or you will get an error. Here is an example:

```python
p1.key("note") # Retrieving the note keyword arguments from p1
p1.key("p")    # Retrieving the period from p1
```

This is useful when you want to copy the data from one player to another or mimick the behavior of a player using another one.

## Player attributes

### active (`bool`)

This property is a boolean that tells you if the player is currently playing or not:

```python
p1.active
```

### begin/end (`Optional[TimePos]`)

These properties are the time position at which the player will start and stop playing. You can set them with the `begin` and `end` setters:

```python
# Setting the begin property
p1.begin = TimePos(bar=4, beat=0, phase=0)

# Setting the end property
p1.end = TimePos(bar=9, beat=0, phase=0)

# Checking the values
p1.begin # TimePos(bar=4, beat=0, phase=0)
p1.end   # TimePos(bar=9, beat=0, phase=0)
```

### iterator (`int`)

This property returns the current iteration index of the player but there is not much you can do with it. It is mostly used internally.

```python
p1.iterator
```