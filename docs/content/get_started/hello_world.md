---
title: 1) Hello, World of Sound!
tag: get started, tutorial
---

> [!note] Before you start!
> This section will start with the basics of Shrimp using MIDI. Please configure a [MIDI Output](/configuration/input_output/midi_configuration/) device before you start. You will also need a software or hardware synthesizer that can receive MIDI messages. Take a look at the list of [recommended software](/installation/recommended_software) if you need to install some :)

## First steps


### Playing one note

Welcome! In this section, you will learn the basics of playing melodies and rhythms using #shrimp. You will also learn how to send MIDI messages to your synthesizer in order to control it. The most basic thing you can do with Shrimp is to play a note. Let's start with that!

```python
p1 >> note(60)
```

This line of code will play a note with the MIDI number 60. The `note()` function is a very important type of object in Shrimp. It is a `Sender` object that holds `Patterns`. In this case, it is so simple that we are not even using a pattern. We are just sending a single note to the synthesizer. 

>[!tip] MIDI Numbers
> The MIDI number 60 corresponds to the note C4. You can find the MIDI numbers for each note in the [MIDI Note Number](https://en.wikipedia.org/wiki/MIDI#MIDI_note_numbers) Wikipedia page.

### Playing more notes

Let's add another note to our melody:

```python
p1 >> note(Pseq(60, 65, 67, 72, 75))
```

This line of code will play two notes in sequence: C4 and D4. The [Pseq](/reference/patterns/pseq) object is your first encounter with a very important concept in Shrimp: `Patterns`. `Patterns` are objects that can generate sequences of values. In this case, the [Pseq](/reference/patterns/pseq) object generates a sequence of two values: `60` and `62`.

### Play from a scale

Using crude MIDI numbers is not very fun. Let's use a scale instead. Shrimp has a built-in scale system. Let's use it to generate a sequence of notes:

```python
p1 >> note(
    note=Pnote("0 2 4 0 3 5 0 1 3"),
)
```

Hey, this is a new object: [Pnote](/reference/patterns/pnote). This object generates a sequence of notes based on a scale and a root note. Each number is a degree of the scale. You can go up and down the scale by using positive and negative numbers. 

The default scale is the natural minor scale. You can change the default scale used by the [Pnote](/reference/patterns/note) object by tweaking the `G`([GlobalConfig](/reference/global_config)) object:

```python
G.root = 40
G.scale = SCALES.dorian
```

Of course, you can also change these values only for the sequence itself without altering the grand scheme of things:

```python
p1 >> n(
    note=Pn("0 2 4 0 3 5 0 1 3", root=40, scale=SCALES.dorian),
)
```

### Stopping patterns

You can stop a `Player` by setting it to `None`. This will stop the generation of new events:

```python
p1 >> None
```

You can also stop it by using the `stop` method:

```python
p1.stop()
```

If you are dealing with multiple `Players` gone rogue, you can stop all of them at once by using the special `silence` function. This is a very powerful function that will stop everything that is currently playing:

```python
silence()
```

### What is `p1`?

Shrimp has three main concepts: `Players`, `Senders` and `Patterns`. They are fairly easy to understand if you think of them as a matrioska doll:
- `Players`: they hold `Senders` and manage them. They are the base object that you interact with.
- `Senders`: they hold `Patterns` and the values held are generating an event (MIDI Note, etc).
- `Patterns`: they generate sequences of values. Some are just generating a single value.

>[!tip] Think of it like this: `Player` -> `Sender` -> `Patterns`.

There are 40 `Players` by default: `p0`..`p19` and `P1..P19`. Believe me, this is more than enough! You assign a pattern to a player by using the `>>` operator. In the previous examples, we used the `p1` player.

All `Players` are synced by default, they all start playing _on the bar_. Of course, this is a behavior that you can change but we are keeping things simple for now.

## Adding rhythm

### Durations and rests

We are playing two notes but we don't have any rhythm yet. Let's add some rhythm to our melody:

```python
p1 >> note(
    note=Pseq(48, 60, 63),
    p=P(1, 1/2, 1, 2)
)
```

The argument `p` controls the duration of each note. `p` stands for `period`, a generic term that we use instead of duration. `1` represents a musical beat, and `1/2` represents half a beat. From there, you can infer all the possible values for the duration of a note. In this case, we are playing four notes with durations of `1`, `1/2`, `1` and `2` beats.

You can also write `Rests` using the `Rest` function:

```python
p1 >> n(
    note=P(60, 62),
    p=P(1, 1/2, 1, Rest(1))
)
```

This is fairly long to type so you can also just write `R(1)` instead of `Rest(1)`:

```python
p1 >> n(
    note=P(60, 62),
    p=P(1, 1/2, 1, R(1))
)
```

>[!warning] Note Duration VS Note length
> The note duration is not the same thing as the note length. The note duration is the time it takes for the note to be played. The note length is the duration for which the note is held. Think of `p` as the _event time_ and the note length as the _sustain time_. 


### Generating rhythms

Writing rhythms by hand is not very fun. You can use patterns to generate rhythms. Let's take a pattern from the library that can generate rhythms: [Pxo](/reference/patterns/pxo). This object generates a sequence of durations and rests based on a classic drum machine pattern representation where `x` is a step and `o` a silence. Let's use it to generate a rhythm for our melody:

```python
p1 >> n(
    note=Pnote(0, 0, 3, 0) / 2,
    p=Pxo("xoxxoo")
)
```

Let's use something else now like [Peuclid](/reference/patterns/peuclid). This pattern generates an Euclidean rhythm. Euclidean rhythms are a very interesting concept in music. They are a way to distribute a number of pulses evenly across a number of steps:

```python
p1 >> note(
    note=Pnote(0, 3, 5, 0, 2, 4, 5, 7, 12),
    p=Peuclid(5, 8) / 2
)
```

## Conclusion

OK, this is a lot of information for a first lesson. Let's stop here and do a quick recap of what you have just learned:

- `Players` are objects that manage `Senders`. There are 40 of them: `p0`..`p19` and `P1..P19`.
  - they can receive patterns using the `>>` operator.
  - they can be stopped using the `stop` method.
- `Senders` are functions like `note()` that hold `Patterns`. Their role is to send events like MIDI notes.
- `Patterns` are objects that generate values. We use them to generate melodies, rhythms, etc.
  - There are many different pattern types you can use. You have learned about [Pseq](/reference/patterns/pseq), [Pnote](/reference/patterns/pnote), [Pxo](/reference/patterns/pxo) and [Peuclid](/reference/patterns/peuclid) already!
  - They are not mandatory, you can also use raw values like `60`, `62`, etc.

In the next section, we will learn more about `Players`.