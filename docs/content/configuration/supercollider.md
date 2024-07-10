---
title: 5) Using SuperCollider
tag: configuration, technical
---

You can use [SuperCollider](https://supercollider.github.io) as a potential audio engine for Baston. SuperCollider is a powerful, flexible, and open-source platform for audio synthesis and algorithmic composition. It is one of the most popular tools for live coding music on its own. Thanks to its server-client architecture, it is possible to use only the server part of SuperCollider and control it from Python.

Baston is speaking to [SuperDirt](https://github.com/musikinformatik/SuperDirt), a custom quark (plugin) that facilitates the use of SuperCollider as a sound engine in live coding environments. SuperDirt features a very versatile audio sampler and some basic synthesizers to help you craft your own. It also features some basic effects and filters to apply to your sounds. People using SuperDirt are mostly using [TidalCycles](https://tidalcycles.org) or [Sardine](https://sardine.raphaelforment.fr).

## Installation

1) Follow the instructions on the [official website](https://supercollider.github.io/download) to install SuperCollider on your system.
2) Install the SuperDirt quark by running the following code in the SuperCollider IDE that you just installed:

```cpp
Quarks.install("SuperDirt")
```

>[!note]-Evaluating code in the SuperCollider IDE
> To evaluate code in the SuperCollider IDE, you can either copy-paste the code into the IDE and press `Cmd + Enter` (Mac) or `Ctrl + Enter` (Windows/Linux), or you can use the `sclang` command-line tool to evaluate code from the command line if you are more familiar with it.

3) (Optional) Install the `sc3-plugins` quark. The procedure to do so depends on your system. You can find more information on the [official website](https://supercollider.github.io/sc3-plugins/).

## Starting the engine

To start SuperDirt, you need to run the following code in the SuperCollider IDE. This will start the SuperCollider Server and SuperDirt, using the default settings:

```cpp 
SuperDirt.start
```

## More advanced configuration

Of course, there is a lot more you can do to configure the engine. You can start by [reading the default configuration](https://github.com/musikinformatik/SuperDirt/blob/develop/superdirt_startup.scd) file that will teach you a lot. You can also save your own configuration file and load it at startup. To do so:

1) Open the SuperCollider IDE and click on `File` > `Open startup file`.
2) Paste your configuration code in the file and save it.
3) Restart SuperCollider.

Everytime you start SuperCollider, it will load your configuration file and thus your custom settings for SuperDirt. There is nothing more to do to be ready to play!