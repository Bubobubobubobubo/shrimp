---
title: 2) Hello, beloved Players!
tag: get started, tutorial
---

## Introduction

You have learned how to play notes using the `note()` function. `note()` is one of many [Senders](/reference/senders/senders) in Shrimp. The role of this sender is simply to send `MIDI` notes. `Senders` are objects that can hold `Patterns`, generators of all sorts of values. They use these values to send events to the system!

They are the backbone of Shrimp. [Senders](/reference/senders/senders) can be simple, like the `note()` function, or more complex, like [MIDI Instruments](). There is generally at least one sender per possible input/output action!

### How do they work?

A [Sender](/reference/senders/senders) is nothing more than a Python function in disguise. As such, it receives **arguments** and **keyword arguments**, data that you pass through to specify what you want to do:
```python
p1 >> debug(1, "hello", keyword=1/2, another_keyword="world")
```

You can test how a sender works by playing around with the `debug` Sender. It will print the arguments and keyword arguments you pass to it:
```python
p1 >> debug(test=Pseq("Hello,", "I", "am", "looping!"))
```

Watch out what happens if you print out any kind of [Pattern](/reference/patterns/pattern) like [Peuclid](/reference/patterns/peuclid):

```python
p1 >> debug(p=Peuclid(5, 8), test="Hi!")
```


Each type of `Player` has its own set of arguments and keyword arguments. These arguments are relative to what each `Player` does. For instance, the `note()` function has arguments like `note`, `velocity`, `channel`, and `duration`. Another `Player` might have a very different set of arguments. You will have to check the documentation to know what you can pass to each `Player`. After a while, it becomes like a second nature to know what to pass to each `Player` 😄.

### Possible value types 

You can pass the following data types as **arguments** and **keyword arguments**:
- **Plain values**: `1`, `"hello"`, `1/2`, `True`, `False`, etc.
- **Patterns**: `Pseq("hello", "world")`, `Pn(0, 1, 2, 3)`, `PWhite(0, 1)`, etc.
- **Generators** and **Iterables**: `zip([1, 2, 3], [4, 5, 6])`, etc.
- **Functions**: `lambda: test()`, etc.

The system is built so that it will accept most of what you can throw at it! This is convenient when you live code and you don't really know exactly where you are heading.

### Wait, there is more!

The [Player](/reference/player/player) can see what **arguments** and **keyword arguments** you pass to the [Sender](/reference/senders/senders)! It means that extra arguments can be used to modify the behavior of the [Player](/reference/player/player) itself:
- `p` (`period`) is a keyword argument that can be used to change the period of the [Player](/reference/player/player). It is useful to change the speed of the [Player](/reference/player/player) without changing the speed of the [Sender](/reference/senders/senders) itself.
- `until` (`int`) is a keyword argument that can be used to stop the [Player](/reference/player/player) after a certain number of repetitions. It has nothing to do with the [Sender](/reference/senders/senders) itself but it has behavior anyway!

There is a growing number of extra arguments that can be used to modify the behavior of the [Player](/reference/player/player). You can check the documentation of each [Sender](/reference/senders/senders) to know what you can pass to each of them but please note that you are controlling **two objects with one set of arguments**.

### Custom behavior

Building custom value generators is super interesting when you try to develop your own library of objects for composition and _live coding_. We have [just seen](#possible-value-types) that you can throw a lot of things as **arguments** and **keyword arguments**. Let's explore a bit. Here is a custom function:


```python
from random import choice
def hi_or_bye():
    return choice(["hello", "goodbye"])

p1 >> debug(test=lambda: hi_or_bye())
```

And here is my own random number generator:

```python
from random import random
def random_generator():
    while True:
        yield random()
my_random = custom_iterator()

p1 >> debug(test=my_random)
```

> [!warning] StopIteration
> I'm not preventing your code from raising a `StopIteration` exception. If you pass a generator, make sure that it will not stop by itself. If it does, you will have to deal with the consequences!

## Conclusion

[Players](/reference/player/player) are very powerful functions and they act as the main type of function you will have to deal with when using #shrimp. Don't think too much about them for now, you will learn how to use them gradually, through experience and music-making! It is important to know that they exist, and that they are the main way to interact with your synths, your DAW or any other piece of software!