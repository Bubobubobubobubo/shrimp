---
title: 4) Global Parameters
tag: get_started, tutorial
---

## Global scale

The default scale when you start the program is the natural minor scale. The default root note is `60`. You can change the default scale and root note used by the [Pnote](/reference/patterns/note) object by tweaking the `G`([GlobalConfig](/reference/global_config)) object:

```python
G.root = 40
G.scale = SCALES.dorian
```

## Local scale

Of course, you can also change these values only for the sequence itself without altering the grand scheme of things:

```python
p1 >> note(
    note=Pn("0 2 4 0 3 5 0 1 3", root=40, scale=SCALES.dorian),
)
```
