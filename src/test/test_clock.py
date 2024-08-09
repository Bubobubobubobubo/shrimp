from shrimp import Clock, read_configuration
import math


CLOCK = Clock(120, grain=0.001, delay=0)
CONFIGURATION = read_configuration()


def test_clock_tempo():
    """The default tempo should be the one provided by the user configuration file"""
    assert math.isclose(round(CLOCK.tempo, 1), CONFIGURATION["clock"]["default_tempo"])


def test_clock_grain():
    """The clock grain should be the one provided by the user configuration file"""
    assert math.isclose(CLOCK.grain, CONFIGURATION["clock"]["time_grain"])


def test_clock_delay():
    """The clock delay should be the one provided by the user configuration file"""
    assert math.isclose(CLOCK.delay, CONFIGURATION["clock"]["delay"])


def test_clock_next_bar():
    """The next_bar function should... return the next bar"""
    now = int(CLOCK.now)
    assert CLOCK.next_bar == now + CLOCK._denominator


def test_clock_next_beat():
    """The next_beat function should... return the next beat"""
    now = int(CLOCK.now)
    assert CLOCK.next_beat == now + 1


def test_add_new_children():
    """The clock should be able to add new children and they should have an effect"""
    children_func = lambda: 1 + 1
    CLOCK.add(func=children_func, name="test")
    assert "test" in CLOCK.children.keys()


def test_clock_remove_by_name():
    """The clock should be able to remove a children from its name"""
    children_func = lambda: 1 + 1
    CLOCK.add(func=children_func, name="test")
    CLOCK.remove_by_name("test")
    assert "test" not in CLOCK.children.keys()


def test_clock_remove_by_func():
    """The clock should be able to remove a children from its function"""
    children_func = lambda: 1 + 1
    CLOCK.add(func=children_func, name="test")
    CLOCK.remove_by_func(children_func)
    assert "test" not in CLOCK.children.keys()
