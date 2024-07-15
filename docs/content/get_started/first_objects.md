---
title: 2) Players and arguments
tag: get started, tutorial
---

## Introduction

You have learned how to play notes using the `note()` function. `note()` is one of many `Players` in Shrimp. Its role is to send `MIDI` notes. `Players` are objects that can hold `Patterns`. They are the backbone of Shrimp. They are the objects that will play your music and send events throughout the system to achieve whatever duty they have been assigned.

### Arguments and keyword arguments

Players can receive **arguments** and **keyword arguments**:
    
```python
p1 >> debug(1, "hello", keyword=1/2, another_keyword="world")
```

Each type of `Player` has its own set of arguments and keyword arguments. You will have to check the documentation to know what you can pass to each `Player`. After a while, it becomes like a second nature to know what to pass to each `Player` 😄.

### **Sender** arguments and keyword arguments

Let's fall back to the `note()` function. The `note()` function can receive the following arguments:
- `note` (`ìnt`): the note to play
- `velocity` (`int`): the velocity of the note
- `channel` (`int`): the MIDI channel to send the note
- `duration` (`float`): the duration of the note

### **Player** arguments and keyword arguments

OK.. is that it? Yes, but there are other possible arguments and keyword arguments that have no specific effect on the `Sender` itself. These args and kwargs are passed to the `Player` that manages the playback of the `Sender`. 

For example, the `until` keyword argument is used to stop the `Sender` after a certain amount of repetitions.