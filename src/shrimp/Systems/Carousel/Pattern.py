"""
This file is a total mess, and it is not clear what is going. 
If possible, split in multiple files. There are two many funcs
in this class, and they are unsufficiently documented.
"""

# Functions from pattern.mjs (Strudel)
# - [ ] class Pattern
# - [ ] withState
# - [ ] fmap
# - [ ] appWhole
# - [ ] query
# - [ ] apply
# - [ ] appBoth
# - [ ] whole_func
# - [ ] appLeft
# - [ ] query
# - [ ] appRight
# - [ ] query
# - [ ] bindWhole
# - [ ] query
# - [ ] withWhole
# - [ ] match
# - [ ] bind
# - [ ] whole_func
# - [ ] join
# - [ ] outerBind
# - [ ] outerJoin
# - [ ] innerBind
# - [ ] innerJoin
# - [ ] resetJoin
# - [ ] restartJoin
# - [ ] squeezeJoin
# - [ ] squeezeBind
# - [ ] queryArc
# - [ ] splitQueries
# - [ ] withQuerySpan
# - [ ] withQuerySpanMaybe
# - [ ] withQueryTime
# - [ ] withHapSpan
# - [ ] withHapTime
# - [ ] withHaps
# - [ ] withHap
# - [ ] setContext
# - [ ] withContext
# - [ ] stripContext
# - [ ] withLoc
# - [ ] filterHaps
# - [ ] filterValues
# - [ ] removeUndefineds
# - [ ] onsetsOnly
# - [ ] discreteOnly
# - [ ] defragmentHaps
# - [ ] firstCycle
# - [ ] firstCycleValues
# - [ ] showFirstCycle
# - [ ] sortHapsByPart
# - [ ] asNumber
# - [ ] _opIn
# - [ ] _opOut
# - [ ] _opMix
# - [ ] _opSqueeze
# - [ ] _opSqueezeOut
# - [ ] _opReset
# - [ ] superimpose
# - [ ] stack
# - [ ] sequence
# - [ ] seq
# - [ ] cat
# - [ ] fastcat
# - [ ] slowcat
# - [ ] onTrigger
# - [ ] log
# - [ ] logValues
# - [ ] drawLine
# - [ ] groupHapsBy
# - [ ] congruent
# - [ ] collect
# - [ ] arpWith
# - [ ] arp
# - [ ] _nonArrayObject
# - [ ] _composeOp
# - [ ] get
# - [ ] wrapper
# - [ ] struct
# - [ ] structAll
# - [ ] mask
# - [ ] maskAll
# - [ ] reset
# - [ ] resetAll
# - [ ] restart
# - [ ] restartAll
# - [ ] gap
# - [ ] pure
# - [ ] query
# - [ ] isPattern
# - [ ] reify
# - [ ] stack
# - [ ] query
# - [ ] _stackWith
# - [ ] stackLeft
# - [ ] stackRight
# - [ ] stackCentre
# - [ ] stackBy
# - [ ] repeat
# - [ ] slowcat
# - [ ] slowcatPrime
# - [ ] cat
# - [ ] arrange
# - [ ] fastcat
# - [ ] sequence
# - [ ] seq
# - [ ] _sequenceCount
# - [ ] register
# - [ ] stepRegister
# - [ ] hush
# - [ ] elem_or
# - [ ] _iter
# - [ ] _chunk
# - [ ] tag
# - [ ] stepJoin
# - [ ] _retime
# - [ ] adjust
# - [ ] _slices
# - [ ] _fitslice
# - [ ] _match
# - [ ] _polymeterListSteps
# - [ ] s_polymeterSteps
# - [ ] s_polymeter
# [ ] s_cat
# - [ ] findtactus
# - [ ] s_alt
# - [ ] s_taperlist
# - [ ] s_taperlist
# - [ ] s_tour
# - [ ] s_tour
# - [ ] merge
# - [ ] func
# - [ ] _loopAt
# - [ ] ref
# - [ ] xfade

import math
from functools import reduce, partial
from typing import Self, List, Callable, Optional, Iterable, Any, Tuple, Dict
from pyautogui import position as mouse_position
from pyautogui import size as screen_size
from .TimeSpan import TimeSpan, TidalFraction
from .Hap import Hap
from .Utils import flatten, identity, bjorklund, curry, remove_nones, xorwise
from itertools import accumulate
import types


class Pattern:
    """
    Pattern class, representing discrete and continuous events as a function of time.

    A pattern is a function that takes a time span and returns a list of events. The
    time span represents the time interval over which the pattern is queried.
    """

    def __init__(self, query: Callable, tactus: Optional[int] = None):
        self.query: Callable[[TimeSpan], List[Hap]] = query
        self._tactus = tactus
        self._generate_applicative_methods()

    @property
    def tactus(self) -> Optional[int]:
        """Returns the tactus of the pattern."""
        return self._tactus

    @tactus.setter
    def tactus(self, tactus: int):
        self._tactus = tactus

    def has_tactus(self) -> bool:
        """Returns True if the pattern has a tactus."""
        return self.tactus is not None

    ################################################################################
    # LIFTING FUNCTIONS
    ################################################################################

    @staticmethod
    def reify(x: Any) -> Self:
        """
        Converts a value to a pattern. Lifting operation.

        Args:
            x (Any): The value to be converted to a pattern

        Returns:
            Pattern: A pattern that repeats the value once per cycle
        """
        from .Mini import mini

        if not isinstance(x, Pattern):
            if isinstance(x, str):
                return mini(x)
            return pure(x)
        return x

    @staticmethod
    def _patternify(method: Callable) -> Self:
        """Turns a method into a pattern method, by lifting the arguments to patterns."""

        def patterned(self, *args: Any) -> Self:
            pat_arg = sequence(*args)
            return pat_arg.with_value(lambda arg: method(self, arg)).inner_join()

        return patterned

    ################################################################################
    # JOIN FUNCTIONS
    ################################################################################

    def join(self) -> Self:
        """Flattens a pattern of patterns into a pattern, where wholes are
        the intersection of matched inner and outer events."""
        return self._bind(identity)

    def inner_join(self) -> Self:
        """Flattens a pattern of patterns into a pattern, where wholes are
        taken from inner events."""
        return self._inner_bind(identity)

    def outer_join(self) -> Self:
        """Flattens a pattern of patterns into a pattern, where wholes are
        taken from outer events."""
        return self._outer_bind(identity)

    # NOTE: Strudel pattern.mjs port
    def reset_join(self, restart: bool = False):
        """Flatterns patterns of patterns, by retriggering/resetting inner patterns at onsets of outer pattern haps"""
        pat_of_pats = self

        def _query(state):
            outer_haps = pat_of_pats.discrete_only().query(state)

            def process_outer_hap(outer_hap):
                inner_pattern = outer_hap.value
                start = outer_hap.whole.begin if restart else outer_hap.whole.begin.cycle_pos()

                inner_haps = inner_pattern.late(start).query(state)

                def process_inner_hap(inner_hap):
                    combined_whole = (
                        inner_hap.whole.intersection(outer_hap.whole) if inner_hap.whole else None
                    )
                    combined_part = inner_hap.part.intersection(outer_hap.part)
                    if combined_part:
                        return Hap(
                            combined_whole,
                            combined_part,
                            inner_hap.value,
                        )
                    return None

                processed_inner_haps = [process_inner_hap(inner_hap) for inner_hap in inner_haps]
                return [hap for hap in processed_inner_haps if hap is not None]

            processed_haps = [
                hap for outer_hap in outer_haps for hap in process_outer_hap(outer_hap)
            ]

            return processed_haps

        return Pattern(_query)

    def squeeze_join(self: Self) -> Self:
        """Like the other joins above, joins a pattern of patterns of values,
        into a flatter pattern of values. In this case it takes whole cycles
        of the inner pattern to fit each event in the outer pattern."""
        pat_of_pats = self

        def _query(state):
            haps = pat_of_pats.discrete_only().query(state)

            def flat_hap(outer_hap: Hap):
                # What is _focus_span? It is not defined anywhere in the Strudel source...
                inner_pat = outer_hap.value._focus_span(outer_hap.whole_or_part())
                inner_haps = inner_pat.query(state.set_span(outer_hap.part))

                def munge(outer, inner):
                    whole = None
                    if inner.whole and outer.whole:
                        whole = inner.whole.intersection(outer.whole)
                        if not whole:
                            return None
                    part = inner.part.intersection(outer.part)
                    if not part:
                        return None
                    return Hap(whole, part, inner.value)

                return [
                    munge(outer_hap, inner_hap)
                    for inner_hap in inner_haps
                    if munge(outer_hap, inner_hap) is not None
                ]

            result = [item for sublist in haps for item in flat_hap(sublist)]
            return [x for x in result if x is not None]

        return Pattern(_query)

    def restartJoin(self) -> Self:
        """TODO: add docstring"""
        return self.resetJoin(True)

    ################################################################################
    # BIND FUNCTIONS
    ################################################################################

    def squeezeBind(self, func: Callable) -> Self:
        """TODO: add docstring"""
        return self.fmap(func).squeeze_join()

    def _bind_whole(self, choose_whole, func: Callable) -> Self:
        pat_val: Pattern = self

        def _query(span: TimeSpan) -> List[Hap]:
            def with_whole(a: TimeSpan, b: TimeSpan) -> Hap:
                return Hap(choose_whole(a.whole, b.whole), b.part, b.value)

            def match(a: Hap) -> List[Hap]:
                return [with_whole(a, b) for b in func(a.value).query(a.part)]

            return flatten([match(ev) for ev in pat_val.query(span)])

        return Pattern(_query)

    def _bind(self, func: Callable) -> Self:
        """TODO: add docstring"""

        def whole_func(a: TimeSpan, b: TimeSpan):
            return a.intersect(b, throw=True) if a and b else None

        return self._bind_whole(whole_func, func)

    def _outer_bind(self, func) -> Self:
        """TODO: add docstring"""
        return self._bind_whole(lambda a, _: a, func)

    def _inner_bind(self, func: Callable) -> Self:
        """TODO: add docstring"""
        return self._bind_whole(lambda _, b: b, func)

    ################################################################################
    # WITH FUNCTIONS
    ################################################################################

    def with_hap_span(self, func: Callable) -> Self:
        """Similar to `withQuerySpan`, but the function is applied to the timespans
        of all haps returned by pattern queries (both `part` timespans, and where
        present, `whole` timespans)."""

        def _query(state):
            pat = map(lambda hap: hap.with_span(func), self.query(state))
            return pat

        return Pattern(_query)

    def with_tactus(self, f) -> Self:
        """Returns a new pattern with the tactus modified by the function `f`."""
        return Pattern(self.query, None if self.tactus is None else f(self.tactus))

    def with_value(self, func: Callable) -> Self:
        """Returns a new pattern, with the function applied to the value of each event."""

        def _query(span: TimeSpan) -> List[Hap]:
            return [event.with_value(func) for event in self.query(span)]

        return Pattern(_query)

    def with_query_span(self, func: Callable) -> Self:
        """Returns a new pattern, with the function applied to the timespan of the query."""
        return Pattern(lambda span: self.query(func(span)))

    def with_query_time(self, func: Callable) -> Self:
        """Returns a new pattern, with the function applied to both the begin
        and end of the the query timespan."""
        return Pattern(lambda span: self.query(span.with_time(func)))

    def with_event_span(self, func: Callable) -> Self:
        """Returns a new pattern, with the function applied to each event
        timespan."""

        def _query(span: TimeSpan) -> List[Hap]:
            return [event.with_span(func) for event in self.query(span)]

        return Pattern(_query)

    def with_event_time(self, func: Callable) -> Self:
        """Returns a new pattern, with the function applied to both the begin
        and end of each event timespan.
        """
        return self.with_event_span(lambda span: span.with_time(func))

    # NOTE: Strudel pattern.mjs port
    def fmap(self, func: Callable) -> Self:
        """Maps a function over the values of the pattern."""
        return self.with_value(lambda x: func(x))

    ################################################################################
    # APPLICATORS
    ################################################################################

    def _app_whole(
        self,
        whole_func: Callable[[Optional[TimeSpan], Optional[TimeSpan]], Optional[TimeSpan]],
        pat_val: Self,
    ) -> Self:
        """
        Assumes self is a pattern of functions, and given a function to
        resolve wholes, applies a given pattern of values to that
        pattern of functions.
        """

        def _query(span: TimeSpan) -> List[Hap]:
            event_funcs = self.query(span)
            event_vals = pat_val.query(span)

            def apply(event_func: Hap, event_val: Hap) -> Optional[Hap]:
                s = event_func.part.intersection(event_val.part)
                return (
                    None
                    if s is None
                    else Hap(
                        whole_func(event_func.whole, event_val.whole),
                        s,
                        event_func.value(event_val.value),
                    )
                )

            return flatten(
                [
                    remove_nones([apply(event_func, event_val) for event_val in event_vals])
                    for event_func in event_funcs
                ]
            )

        return Pattern(_query)

    # NOTE: Strudel pattern.mjs port
    def _app_both(self, pat_val: Self) -> Self:
        """When this method is called on a pattern of functions, it matches its haps
        with those in the given pattern of values.  A new pattern is returned, with
        each matching value applied to the corresponding function.

        In this `_appBoth` variant, where timespans of the function and value haps
        are not the same but do intersect, the resulting hap has a timespan of the
        intersection. This applies to both the part and the whole timespan.

        Args:
            pat_val (Pattern): The pattern of values to apply

        Returns:
            Pattern: A new pattern with the given pattern of values applied
        """

        def whole_func(span_a: TimeSpan, span_b: TimeSpan) -> Optional[TimeSpan]:
            if (span_a is not None) and (span_b is not None):
                return span_a.intersection(span_b, throw=True)
            else:
                return None

        result = self._app_whole(whole_func, pat_val)
        if self.tactus is not None:
            result.tactus = math.lcm(pat_val.tactus, self.tactus)
        return result

    # NOTE: This is redundant with the method above! Which one should be kept?
    def _app_both(self, other: Self) -> Self:
        """Tidal's <*> operator"""

        def whole_func(span_a: TimeSpan, span_b: TimeSpan) -> Optional[TimeSpan]:
            return span_a.intersection(span_b, throw=True) if span_a and span_b else None

        return self._app_whole(whole_func, other)

    def _app_left(self, other: Self) -> Self:
        """Tidal's <* operator. As with `_app_both`, but the `whole` timespan
        is not the intersection, but the timespan from the function of patterns
        that this method is called on. In practice, this means that the pattern
        structure, including onsets, are preserved from the pattern of functions
        (often referred to as the lefthand or inner pattern).

        Args:
            pat_val (Pattern): The pattern to apply to the left of the current pattern

        Returns:
            Pattern: A new pattern with the given pattern applied to the left
        """

        def _query(span: TimeSpan) -> List[Hap]:
            events: List[Hap] = []

            # Iterating over all the events in the current pattern
            for func in self.query(span):
                event_vals = other.query(func.whole_or_part())

                # Iterating over all the events in the pattern passed as argument
                for val in event_vals:
                    new_whole: TimeSpan = func.whole
                    new_part: TimeSpan = func.part.intersection(val.part)
                    if new_part:
                        new_value = func.value(val.value)
                        events.append(Hap(new_whole, new_part, new_value))
            return events

        result = Pattern(_query)
        result.tactus = self.tactus
        return result

    def _app_right(self, other: Self) -> Self:
        """Tidal's *> operator. As with `appLeft`, but `whole` timespans
        are instead taken from the pattern of values, i.e. structure is
        preserved from the right hand/outer pattern."""

        def _query(span: TimeSpan) -> List[Hap]:
            events: List[Hap] = []

            # Iterating over all the events in the other pattern
            for val in other.query(span):
                event_funcs = self.query(val.whole_or_part())

                # Iterating over all the events in the current pattern
                for func in event_funcs:
                    new_whole: TimeSpan = val.whole
                    new_part: TimeSpan = func.part.intersection(val.part)
                    if new_part:
                        new_value = func.value(val.value)
                        events.append(Hap(new_whole, new_part, new_value))
            return events

        result = Pattern(_query)
        result.tactus = other.tactus
        return result

    ################################################################################
    # FILTERS
    ################################################################################

    def discrete_only(self) -> Self:
        """
        Removes continuous events that don't have a 'whole' timespan.
        TODO: check if this is the right way to implement this
        """
        return self.filter_events(lambda event: event.whole)

    def remove_none(self):
        """Removes all None values from the pattern"""
        return self.filter_values(lambda v: v)

    def split_queries(self) -> Self:
        """Splits queries at cycle boundaries.

        Note: This makes some calculations easier to express, as all events are then
        constrained to happen within a cycle.
        """

        def _query(span: TimeSpan) -> List[Hap]:
            return flatten([self.query(subspan) for subspan in span.span_cycles()])

        return Pattern(_query)

    def filter_events(self, event_test: Callable) -> Self:
        """Returns a new pattern that will only return events that pass the given test."""
        return Pattern(lambda span: list(filter(event_test, self.query(span))))

    def filter_values(self, value_test: Callable) -> Self:
        """Returns a new pattern that will only return events where the value passes the given test."""
        return Pattern(
            lambda span: list(filter(lambda event: value_test(event.value), self.query(span)))
        )

    def onsets_only(self) -> Self:
        """Returns a new pattern that will only return events where the start
        of the 'whole' timespan matches the start of the 'part'
        timespan, i.e. the events that include their 'onset'.
        """
        return self.filter_events(Hap.has_onset)

    ################################################################################
    # OPERATORS: add, sub, mul, truediv, floordiv, mod, pow, etc...
    ################################################################################

    def _apply_op(
        self,
        a: dict | Any,
        b: dict | Any,
        func: Callable[[Any, Any], Any],
    ) -> dict | Any:
        if isinstance(a, dict) and isinstance(b, dict):
            result: Dict[str, Any] = {}
            all_keys = set(a.keys()).union(set(b.keys()))
            for key in all_keys:
                if key in a and key in b:
                    result[key] = self._apply_op(a[key], b[key], func)
                elif key in a:
                    result[key] = a[key]
                elif key in b:
                    result[key] = b[key]
            return result
        elif not isinstance(a, dict) and not isinstance(b, dict):
            return func(a, b)
        else:
            print(a, b)
            raise ValueError("Both arguments must be either pure values or dictionaries.")

    # TODO: I think that this is not the right way to implement this (bugs ?)
    def _generate_applicative_methods(self):
        def _apply_op_pattern(op_name: str, func: Callable):
            def method_left(self, other: Self) -> Self:
                return self.with_value(lambda x: lambda y: self._apply_op(x, y, func)).app_left(
                    Pattern.reify(other)
                )

            def method_right(self, other: Self) -> Self:
                return self.with_value(lambda x: lambda y: self._apply_op(x, y, func)).app_right(
                    Pattern.reify(other)
                )

            def method_both(self, other: Self) -> Self:
                return self.with_value(lambda x: lambda y: self._apply_op(x, y, func)).app_both(
                    Pattern.reify(other)
                )

            return method_left, method_right, method_both

        # Define the operations and their corresponding functions
        operations = {
            "add": lambda a, b: a + b,
            "sub": lambda a, b: a - b,
            "mul": lambda a, b: a * b,
            "truediv": lambda a, b: a / b,
            "floordiv": lambda a, b: a // b,
            "mod": lambda a, b: a % b,
            "pow": lambda a, b: a**b,
        }

        # Attach the methods to the instance
        for op_name, func in operations.items():
            method_left, method_right, method_both = _apply_op_pattern(op_name, func)
            setattr(self, f"{op_name}left", types.MethodType(method_left, self))
            setattr(self, f"{op_name}right", types.MethodType(method_right, self))
            setattr(self, f"{op_name}both", types.MethodType(method_both, self))

    def __add__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: a + b)
        )._app_left(self.reify(other))

    def __radd__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b + a)
        )._app_left(self.reify(other))

    def __sub__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: a - b)
        )._app_left(self.reify(other))

    def __rsub__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b - a)
        )._app_left(self.reify(other))

    def __mul__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: a * b)
        )._app_left(self.reify(other))

    def __rmul__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b * a)
        )._app_left(self.reify(other))

    def __truediv__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: a / b)
        )._app_left(self.reify(other))

    def __rtruediv__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b / a)
        )._app_left(self.reify(other))

    def __floordiv__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: a // b)
        )._app_left(self.reify(other))

    def __rfloordiv__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b // a)
        )._app_left(self.reify(other))

    def __mod__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: a % b)
        )._app_left(self.reify(other))

    def __rmod__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b % a)
        )._app_left(self.reify(other))

    def __pow__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: a**b)
        )._app_left(self.reify(other))

    def __rpow__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b**a)
        )._app_left(self.reify(other))

    def __rshift__(self, other: Self) -> Self:
        """
        Alias of `combine_right`

        Accepts a Pattern or an iterable of Patterns.

        >>> s("a") >> n("0 1") >> s("b c")
            ~[((0, 1), (0, ½), {'n': 0, 's': 'b'}),
              ((0, 1), (½, 1), {'n': 1, 's': 'c'})] ...~

        >>> s("a") >> [s("b c"), n("0 1"), gain(0.75)]
            ~[((0, 1), (0, ½), {'gain': 0.75, 'n': 0, 's': 'b'}),
              ((0, 1), (½, 1), {'gain': 0.75, 'n': 1, 's': 'c'})] ...~

        """
        if not isinstance(other, Iterable):
            other = [other]
        return self.combine_right(*other)

    def __lshift__(self, other: Self) -> Self:
        """
        Alias of `combine_left`

        Accepts a Pattern or an iterable of Patterns.

        >>> s("a") << n("0 1") << s("b c")
            ~[((0, 1), (0, ½), {'n': 0, 's': 'a'}),
              ((0, 1), (½, 1), {'n': 1, 's': 'a'})] ...~

        >>> s("a") << [s("b c"), n("0 1"), gain(0.75)]
            ~[((0, 1), (0, ½), {'gain': 0.75, 'n': 0, 's': 'a'}),
              ((0, 1), (½, 1), {'gain': 0.75, 'n': 1, 's': 'a'})] ...~

        """
        if not isinstance(other, Iterable):
            other = [other]
        return self.combine_left(*other)

    def _opIn(self, other: Self, func: Callable) -> Self:
        return self.fmap(func)._app_left(other)

    def _opOut(self, other: Self, func: Callable) -> Self:
        return self.fmap(func)._app_right(other)

    def _opMix(self, other: Self, func: Callable) -> Self:
        return self.fmap(func)._app_both(other)

    def _op_squeeze(self, other: Self, func: Callable) -> Self:
        otherPat = self.reify(other)
        return self.fmap(lambda a: otherPat.fmap(lambda b: func(a)(b))).squeeze_join()

    def _op_squeeze_out(self, other: Self, func: Callable) -> Self:
        otherPat = self.reify(other)
        return otherPat.fmap(lambda a: self.fmap(lambda b: func(b)(a))).squeeze_join()

    def _op_reset(self, other: Self, func: Callable) -> Self:
        otherPat = self.reify(other)
        return otherPat.fmap(lambda b: self.fmap(lambda a: func(a)(b))).reset_join()

    def _op_restart(self, other: Self, func: Callable) -> Self:
        otherPat = self.reify(other)
        return otherPat.fmap(lambda b: self.fmap(lambda a: func(a)(b))).restart_join()

    ################################################################################
    # COMBINATORS
    ################################################################################

    def combine_right(self, *others: Self) -> Self:
        """
        Combine multiple dict patterns (AKA control patterns) by merging the
        values from other patterns, and replacing any key with the same name.

        If there are duplicate keys, the last pattern with that key takes
        precedence when merging values.  For inverting the precedence, see
        `combine_left`.

        See `__rshift__` (`>>` operator)

        >>> s("a").combine_right(n("0 1"), s("b c"))
            ~[((0, 1), (0, ½), {'n': 0, 's': 'b'}),
              ((0, 1), (½, 1), {'n': 1, 's': 'c'})] ...~

        """
        return reduce(
            lambda a, b: a.with_value(lambda x: lambda y: {**x, **y})._app_left(b),
            others,
            self,
        )

    union = combine_right

    def combine_left(self, *others: Self) -> Self:
        """
        Combine multiple dict patterns (AKA control patterns) by merging the
        values from other patterns, and replacing any key with the same name.

        If there are duplicate keys, the first pattern with that key takes
        precedence when merging values.  For inverting the precedence, see
        `combine_right`.

        See `__lshift__` (`<<` operator)

        >>> s("a").combine_left(n("0 1"), s("b c"))
            ~[((0, 1), (0, ½), {'n': 0, 's': 'a'}),
              ((0, 1), (½, 1), {'n': 1, 's': 'a'})] ...~

        """
        return reduce(
            lambda a, b: a.with_value(lambda x: lambda y: {**y, **x})._app_left(b),
            others,
            self,
        )

    ################################################################################
    # FAST AND SLOW
    ################################################################################

    def fast(self, factor: float) -> Self:
        """Speeds up a pattern by the given factor"""
        fast_query = self.with_query_time(lambda t: t * factor)
        fast_events = fast_query.with_event_time(lambda t: t / factor)
        return fast_events

    fast = _patternify(fast)

    def _slow(self, factor: float) -> Self:
        """Slow slows down a pattern"""
        return self.fast(1 / factor)

    slow = _patternify(_slow)

    def fast_gap(self, factor: float) -> Self:
        """
        Similar to `fast` but maintains its cyclic alignment.

        For example, `p.fastgap(2)` would squash the events in pattern `p` into
        the first half of each cycle (and the second halves would be empty).

        The factor should be at least 1.

        """
        if factor <= 0:
            return silence()

        factor_ = max(1, factor)

        def munge_query(t: TidalFraction) -> TidalFraction:
            return t.sam() + min(1, factor_ * t.cycle_pos())

        def event_span_func(span: TimeSpan) -> TimeSpan:
            begin = span.begin.sam() + TidalFraction(span.begin - span.begin.sam(), factor_)
            end = span.begin.sam() + TidalFraction(span.end - span.begin.sam(), factor_)
            return TimeSpan(begin, end)

        def _query(span: TimeSpan) -> List[Hap]:
            new_span = TimeSpan(munge_query(span.begin), munge_query(span.end))
            if new_span.begin == span.begin.next_sam():
                return []
            return [e.with_span(event_span_func) for e in self.query(new_span)]

        return Pattern(_query).split_queries()

    ################################################################################
    # EARLY AND LATE
    ################################################################################

    def _early(self, offset: float) -> Self:
        """Equivalent of Tidal's <~ operator"""
        offset = TidalFraction(offset)
        return self.with_query_time(lambda t: t + offset).with_event_time(lambda t: t - offset)

    early = _patternify(_early)

    def _late(self, offset: float) -> Self:
        """Equivalent of Tidal's ~> operator"""
        return self._early(0 - offset)

    late = _patternify(_late)

    def off(self, time_pat: Self, func: Callable) -> Self:
        """TODO: add docstring"""
        return stack(self, func(self.early(time_pat)))

    ################################################################################
    # CONDITION BASED FUNCTIONS
    ################################################################################

    def when(self, boolean_pat, func: Callable) -> Self:
        """
        Applies function `func` on each event of pattern if `boolean_pat` is true.

        """
        boolean_pat = sequence(boolean_pat)
        true_pat = boolean_pat.filter_values(identity)
        false_pat = boolean_pat.filter_values(lambda val: not val)
        with_pat = true_pat.with_value(lambda _: lambda y: y)._app_left(func(self))
        without_pat = false_pat.with_value(lambda _: lambda y: y)._app_left(self)
        return stack(with_pat, without_pat)

    def when_cycle(self, test_func: Callable, func: Callable) -> Self:
        """
        Applies function `func` to pattern only if `test_func` returns true on
        each cycle.

        Similar to `when`, but instead of working with a boolean pattern, this
        evaluates a boolean function with the cycle number and applies
        (or not) transformation on each cycle.

        """

        def _query(span: TimeSpan):
            if test_func(math.floor(span.begin)):
                return func(self).query(span)
            return self.query(span)

        return Pattern(_query).split_queries()

    def every(self, n: float, func: Callable) -> Self:
        """Applies a function to every nth cycle of a pattern"""
        pats = [func(self)] + ([self] * (n - 1))
        return slowcat(*pats)

    ################################################################################
    # CONCATENATIVE FUNCTIONS
    ################################################################################

    def jux(self, func: Callable, by: int | float = 1) -> Self:
        """Classic Tidal Function."""

        left = self.with_value(
            lambda val: dict(list(val.items()) + [("pan", val.get("pan", 0.5) - by / 2)])
        )
        right = self.with_value(
            lambda val: dict(list(val.items()) + [("pan", val.get("pan", 0.5) + by / 2)])
        )

        return stack(left, func(right))

    def superimpose(self, func: Callable) -> Self:
        """
        Play a modified version of a pattern at the same time as the original pattern,
        resulting in two patterns being played at the same time.

        >>> s("bd sn [cp ht] hh").superimpose(lambda p: p.fast(2))
        >>> s("bd sn cp hh").superimpose(lambda p: p.speed(2).early(0.125))

        """
        return stack(self, func(self))

    def layer(self, *list_funcs: Callable) -> Self:
        """
        Layer up multiple functions on one pattern.

        For example, the following will play two versions of the pattern at the
        same time, one reversed and one at twice the speed:

        >>> s("arpy [~ arpy:4]").layer(rev, lambda p: p.fast(2)])

        If you want to include the original version of the pattern in the
        layering, use the `id` function:

        >>> s("arpy [~ arpy:4]").layer(identity, rev, lambda p: p.fast(2)])

        """
        return stack(*[func(self) for func in list_funcs])

    def append(self, other: Self) -> Self:
        """Appends two patterns together and compress them into a single cycle"""
        return fastcat(self, other)

    def rev(self) -> Self:
        """Returns the reversed the pattern"""

        def _query(span: TimeSpan):
            cycle = span.begin.sam()
            next_cycle = span.begin.next_sam()

            def reflect(to_reflect: Hap) -> Hap:
                reflected = to_reflect.with_time(lambda time: cycle + (next_cycle - time))
                (reflected.begin, reflected.end) = (reflected.end, reflected.begin)
                return reflected

            events = self.query(reflect(span))
            return [event.with_span(reflect) for event in events]

        return Pattern(_query).split_queries()

    def first_cycle(self) -> List[Hap]:
        """Returns the events of the first cycle of the pattern"""
        return sorted(self.query(TimeSpan(TidalFraction(0), TidalFraction(1))))

    ################################################################################
    # ITER BASED FUNCTIONS
    ################################################################################

    def iter(self, n: int) -> Self:
        """
        Divides a pattern into a given number of subdivisions, plays the
        subdivisions in order, but increments the starting subdivision each
        cycle.

        The pattern wraps to the first subdivision after the last subdivision is
        played.

        >>> s("bd hh sn cp").iter(4)

        """
        return slowcat(*[self.early(TidalFraction(i, n)) for i in range(n)])

    def reviter(self, n: int) -> Self:
        """
        Same as `iter` but in the other direction.

        >>> s("bd hh sn cp").reviter(4)

        """
        return slowcat(*[self.late(TidalFraction(i, n)) for i in range(n)])

    def compress(self, begin: TidalFraction, end: TidalFraction) -> Self:
        """Squeeze pattern within the specified time span"""
        begin = TidalFraction(begin)
        end = TidalFraction(end)
        if begin > end or end > 1 or begin > 1 or begin < 0 or end < 0:
            return silence()
        return self.fast_gap(TidalFraction(1, end - begin)).late(begin)

    def loop_at(self, factor: float, cps: float = 0.5) -> Self:
        """Makes the sample fit the given number of cycles by changing the speed."""
        return self.speed((1 / factor) * cps).unit("c").slow(factor)

    def zoom(self, zoom_start: TidalFraction, zoom_end: TidalFraction) -> Self:
        """Plays a portion of a pattern, specified by the beginning and end of a time span.
        The new resulting pattern is played over the time period of the original pattern"""
        zoom_start, zoom_end = TidalFraction(zoom_start), TidalFraction(zoom_end)
        if zoom_start >= zoom_end:
            return self.nothing()
        duration = zoom_end - zoom_start
        result = (
            self.with_query_span(
                lambda span: span.with_cycle(lambda t: (t * duration) + zoom_start)
            )
            .with_hap_span(lambda span: span.with_cycle(lambda t: (t - zoom_start) / duration))
            .split_queries()
        )
        return result

    def inside(self, factor, func):
        """Carries out an operation 'inside' a cycle."""
        return func(self.slow(factor)).fast(factor)

    def swing_by(self, swing, n) -> Self:
        """Swing a pattern by a given amount."""
        return self.inside(n, late(sequence(0, swing / 2)))

    def swing(self, n) -> Self:
        """Swing a pattern by 1/3."""
        return self.swing_by(1 / 3, n)

    def reset(self, *args):
        """Resets the pattern to the start of the cycle for each onset of the reset pattern."""
        return self.keepif.reset(*args)

    ################################################################################
    # STRIATE
    ################################################################################

    def striate(self, n_pat: int) -> Self:
        """
        Cut samples into bits in a similar way to `chop`

        Pattern must be an `s` control pattern, and the resulting pattern will
        contain `begin` and `end` values to be interpreted by the synth
        (SuperDirt, Dirt, etc.)

        """
        return self.reify(n_pat).with_value(lambda n: self._striate(n)).inner_join()

    def _striate(self, n: int) -> Self:
        def merge_sample(samp_range: dict) -> Self:
            return self.with_value(
                lambda v: {"s": v["s"] if isinstance(v, dict) else v, **samp_range}
            )

        samp_ranges = [dict(begin=i / n, end=(i + 1) / n) for i in range(n)]
        return fastcat(*[merge_sample(r) for r in samp_ranges])

    ################################################################################
    # SIGNAL-LIKE FUNCTIONS
    ################################################################################

    def to_bipolar(self) -> Self:
        """Takes a unipolar pattern and converts it to a bipolar pattern."""
        return self.fmap(lambda x: x * 2 - 1)

    def segment(self, n: int) -> Self:
        """
        Samples the pattern at a rate of `n` events per cycle.
        Useful for turning a continuous pattern into a discrete one.
        >>> rand().segment(4)
        """
        return pure(identity).fast(n)._app_left(self)

    def range(self, minimum: Self, maximum: Self) -> Self:
        """
        Rescales values to the range [min, max].  Assumes pattern is numerical,
        containing unipolar values in the range [0, 1].

        Args:
            minimum (Self): The minimum value of the range
            maximum (Self): The maximum value of the range

        Returns:
            Pattern: The rescaled pattern

        """
        return self * (maximum - minimum) + minimum

    def rangex(self, minimum: Self, maximum: Self) -> Self:
        """
        Rescales values to the range [min, max] following an exponential curve

        Assumes pattern is numerical, containing unipolar values in the range
        [0, 1].

        """
        return self.range(math.log(minimum), math.log(maximum)).with_value(math.exp)

    ################################################################################
    # PROBABILISTIC FUNCTIONS
    ################################################################################

    def degrade(self) -> Self:
        """
        Randomly removes events from pattern, by 50% chance.

        """
        return self.degrade_by(0.5)

    def degrade_by(self, by: float, prand: Self = None) -> Self:
        """
        Randomly removes events from pattern.

        You can control the percentage of events that are removed with `by`.
        With `prand` you can specify a different random pattern, must be a
        numerical 0-1 ranged pattern.

        """
        if by == 0:
            return self
        if not prand:
            prand = rand()
        return self.with_value(lambda a: lambda _: a)._app_left(
            prand.filter_values(lambda v: v > by)
        )

    def undegrade(self) -> Self:
        """
        Same as `degrade`, but random values represent percentage of events to
        keep, not remove, by 50% chance.

        """
        return self.undegrade_by(0.5)

    def undegrade_by(self, by: float, prand: Self = None) -> Self:
        """
        Same as `degrade`, but random values represent percentage of events to
        keep, not remove.

        You can control the percentage of events that are removed with `by`.
        With `prand` you can specify a different random pattern, must be a
        numerical 0-1 ranged pattern.

        """
        if not prand:
            prand = rand()
        return self.with_value(lambda a: lambda _: a)._app_left(
            prand.filter_values(lambda v: v <= by)
        )

    def sometimes_by(self, by_pat: float, func: Callable) -> Self:
        """
        Applies a function to pattern sometimes based on specified `by`
        percentage, at random.

        `by_pat` is a number between 0 and 1, representing 0% to 100% chance of
        applying function.

        >>> s("bd").fast(8).sometimes_by(0.75, lambda p: p << speed(3))

        """
        return self.reify(by_pat).with_value(lambda by: self._sometimes_by(by, func)).inner_join()

    def always(self, func: Callable) -> Self:
        """Always return the function applied to the pattern"""
        return self.sometimes_by(1, func)

    def almostAlways(self, func: Callable) -> Self:
        """Almost always return the function applied to the pattern (90% chance)"""
        return self.sometimes_by(0.90, func)

    def often(self, func: Callable) -> Self:
        """Often return the function applied to the pattern (75% chance)"""
        return self.sometimes_by(0.75, func)

    def sometimes(self, func: Callable) -> Self:
        """
        Applies a function to pattern, around 50% of the time, at random.

        >>> s("bd").fast(8).sometimes(lambda p: p << speed(2))

        """
        return self.sometimes_by(0.5, func)

    def rarely(self, func: Callable) -> Self:
        """Rarely return the function applied to the pattern (25% chance)"""
        return self.sometimes_by(0.25, func)

    def almostNever(self, func: Callable) -> Self:
        """Almost never return the function applied to the pattern (10% chance)"""
        return self.sometimes_by(0.10, func)

    def never(self, func: Callable) -> Self:
        """
        Never return the function applied to the pattern (0% chance).
        This function is equivalent to the identity function.
        """
        return self.sometimes_by(0, func)

    def _sometimes_by(self, by: float, func: Callable) -> Self:
        """Applies a function to pattern sometimes based on specified `by` percentage, at random."""
        return stack(self.degrade_by(by), func(self.undegrade_by(by)))

    def sometimes_pre(self, func: Callable) -> Self:
        """
        Similar to `sometimes` but applies a function to the pattern *before*
        filtering events 50% of the time, at random.
        """
        return self.sometimes_pre_by(0.5, func)

    def sometimes_pre_by(self, by_pat: float, func: Callable) -> Self:
        """
        Similar to `sometimes_by` but applies a function to the pattern *before*
        filtering events sometimes, based on `by` percentage, at random.

        `by` is a number between 0 and 1, representing 0% to 100% chance of
        applying function.

        """
        return (
            self.reify(by_pat).with_value(lambda by: self._sometimes_pre_by(by, func)).inner_join()
        )

    def _sometimes_pre_by(self, by: float, func: Callable) -> Self:
        return stack(self.degrade_by(by), func(self).undegrade_by(by))

    def somecycles(self, func: Callable) -> Self:
        """Applies a function to pattern sometimes based on specified `by` percentage, at random."""
        return self.somecycles_by(0.5, func)

    def somecycles_by(self, by_pat: float, func: Callable) -> Self:
        """Applies a function to pattern sometimes based on specified `by` percentage, at random."""
        return self.reify(by_pat).with_value(lambda by: self._somecycles_by(by, func)).inner_join()

    def _somecycles_by(self, by: float, func: Callable) -> Self:
        return self.when_cycle(lambda c: time_to_rand(c) < by, func)

    ################################################################################
    # TODO: SORTING AREA, FREE-FLOATING FUNCS NOT BELONGING TO ANY FAMILY
    ################################################################################

    def struct(self, *binary_pats: bool) -> Self:
        """
        Restructure the pattern according to a binary pattern (false values are
        dropped).

        """
        return (
            sequence(binary_pats)
            .with_value(lambda b: lambda val: val if b else None)
            ._app_left(self)
            .remove_none()
        )

    def ply(self, factor: int) -> Self:
        """Tidal 'ply' function"""
        result = self.fmap(lambda x: pure(x).fast(factor)).squeeze_join()
        if self.tactus:
            result.tactus = TidalFraction(factor).mulmaybe(self.tactus)
        return result

    def mask(self, *binary_pats: bool) -> Self:
        """
        Only let through parts of pattern corresponding to true values in the
        given binary pattern.

        """
        return (
            sequence(binary_pats)
            .with_value(lambda b: lambda val: val if b else None)
            ._app_right(self)
            .remove_none()
        )

    def mask_all(self, *binary_pats: bool) -> Self:
        raise NotImplementedError

    def reset(self, *args: Any) -> Self:
        raise NotImplementedError

    def reset_all(self, *args: Any) -> Self:
        raise NotImplementedError

    def euclid(self, k: int, n: int, rot: int = 0) -> Self:
        """
        Change the structure of the pattern to form an euclidean rhythm

        Euclidian rhythms are rhythms obtained using the greatest common divisor
        of two numbers. They were described in 2004 by Godfried Toussaint, a
        canadian computer scientist. Euclidian rhythms are really useful for
        computer/algorithmic music because they can accurately describe a large
        number of rhythms used in the most important music world traditions.

        >>> s("bd").euclid(3, 8)
        >>> s("sd").euclid(5, 8, fastcat(0, 2, 4))

        """
        return self.struct(_tparams(_euclid, k, n, rot).inner_join())

    ################################################################################
    # NOTHING OR SILENCE FUNCTIONS
    ################################################################################

    def gap(self, tactus: int | float) -> Self:
        """Does absolutely nothing, but with a given matrical 'tactus'"""
        return Pattern(query=lambda _: [], tactus=tactus)

    def silence(self) -> Self:
        """Does absolutely nothing"""
        return self.gap(1)

    def nothing(self) -> Self:
        """Like silence, but with a 'tactus' (relative duration) of 0"""
        return self.gap(0)

    ################################################################################
    # ARP FUNCTIONS
    ################################################################################

    def arp(self, pat: Self) -> Self:
        return self.arp_with(lambda haps: pat.fmap(lambda i: haps[i % len(haps)]))

    def arp_with(self, func: Callable) -> Self:
        some_func = lambda h: Hap(whole=h.whole, part=h.part, value=h.value.value)
        return self.collect().fmap(lambda v: self.reify(func(v))).inner_join().with_hap(some_func)

    def with_hap(self, func: Callable) -> Self:
        return self.with_haps(lambda haps: map(lambda a: func(a), haps))

    def with_haps(self, func: Callable) -> Self:
        result = Pattern(lambda state: func(self.query(state)))
        result.tactus = self.tactus
        return result

    def collect(self) -> Self:
        raise NotImplementedError

    def __repr__(self):
        events = [str(e) for e in self.first_cycle()]
        events_str = ",\n ".join(events).replace("\n", "\n ")
        return f"~[{events_str}] ...~"

    def __eq__(self, other):
        raise NotImplementedError(
            "Patterns cannot be compared. Evaluate them with `.first_cycle()` or similar"
        )


def partial_decorator(f: Callable) -> Callable:
    """
    This decorator allows module-level functions to be used as pattern methods.

    The `partial_decorator` function takes a callable `f` as input and returns a new callable `wrapper`.
    The `wrapper` function is responsible for handling the execution of the original function `f`.

    When the `wrapper` function is called with arguments, it first tries to execute the original
    function `f` with the given arguments. If the execution of `f` raises a `TypeError` or
    `AttributeError`, it catches the exception and returns a partial function instead.  The partial
    function is created by calling the `partial` function with `f` and the given arguments.

    This decorator is useful when you want to use module-level functions as pattern methods.
    It allows you to seamlessly use these functions as methods within a pattern, even if they
    were not originally designed to be used that way.

    Parameters:
        f (Callable): The original function to be decorated.

    Returns:
        Callable: The decorated function.
    """

    def wrapper(*args):
        try:
            return f(*args)
        except (TypeError, AttributeError) as _:
            return partial(f, *args)

    return wrapper


# reify = Pattern.reify


def silence() -> Pattern:
    """Returns a pattern that plays no events"""
    return Pattern(lambda _: [])


def _tparams(func, *params: Any) -> Pattern:
    if not params:
        return silence()
    curried_func = curry(func)
    return reduce(
        lambda a, b: a._app_both(Pattern.reify(b)),
        params[1:],
        Pattern.reify(params[0]).with_value(curried_func),
    )


def pure(value: Any) -> Pattern:
    """
    Returns a pattern that repeats 'value' once per cycle using
    'span_cycles'. Lifts a value into a pattern.

    Args:
        value (Any): The value to be repeated

    Returns:
        Pattern: A pattern that repeats the value once per cycle
    """

    def _query(span: TimeSpan):
        return [
            Hap(TidalFraction(subspan.begin).whole_cycle(), subspan, value)
            for subspan in span.span_cycles()
        ]

    return Pattern(_query)


def steady(value: Any) -> Pattern:
    def _query(span: TimeSpan) -> List[Hap]:
        return [Hap(None, span, value)]

    return Pattern(_query)


def slowcat(*pats: Pattern) -> Pattern:
    """
    Combines a list of patterns, switching between them successively, one per cycle.
    It currently behaves slightly differently from Tidal.
    """
    pats = [Pattern.reify(pat) for pat in pats]

    def _query(span: TimeSpan) -> List[Hap]:
        pat = pats[math.floor(span.begin) % len(pats)]
        return pat.query(span)

    return Pattern(_query).split_queries()


def fastcat(*pats: Pattern) -> Pattern:
    """Concatenation: as with slowcat, but squashes a cycle from each
    pattern into one cycle"""
    return slowcat(*pats).fast(len(pats))


cat = fastcat
seq = fastcat


def stack(*pats: Tuple[Pattern]) -> Self:
    """Pile up patterns"""
    pats = [Pattern.reify(pat) for pat in pats]

    def _query(span: TimeSpan) -> List[Hap]:
        return flatten([pat.query(span) for pat in pats])

    return Pattern(_query)


def _sequence_count(x: list | tuple | str | Any) -> Tuple[Pattern, int]:

    if isinstance(x, (list, tuple)):
        if len(x) == 1:
            return _sequence_count(x[0])
        else:
            return (fastcat(*[sequence(x) for x in x]), len(x))

    if isinstance(x, Pattern):
        return (x, 1)

    if isinstance(x, str):
        from .Mini import mini

        return (mini(x), 1)
    return (pure(x), 1)


def sequence(*args: Any) -> Pattern:
    """TODO: add docstring"""
    return _sequence_count(args)[0]


def congruent(a: Hap, b: Hap) -> bool:
    return a.span_equals(b)


# TODO: what is the steps type?
def polymeter(*args, steps=None) -> Pattern:
    seqs = [_sequence_count(x) for x in args]
    if len(seqs) == 0:
        return silence()
    if not steps:
        steps = seqs[0][1]
    pats = []
    for seq in seqs:
        if seq[1] == 0:
            continue
        if steps == seq[1]:
            pats.append(seq[0])
        else:
            pats.append(seq[0].fast(TidalFraction(steps) / TidalFraction(seq[1])))
    return stack(*pats)


def polyrhythm(*xs: Any) -> Pattern:
    seqs = [sequence(x) for x in xs]

    if len(seqs) == 0:
        return silence()

    return stack(*seqs)


def _euclid(k: int, n: int, rotation: float):
    """Generate an euclidean sequence, with optional rotation"""
    b = bjorklund(k, n)
    if rotation:
        b = b[rotation:] + b[:rotation]
    return sequence(b)


@partial_decorator
def fast(arg: int | float, pat: Any):
    """Override for `fast` method"""
    return Pattern.reify(pat).fast(arg)


@partial_decorator
def zoom(zoom_begin: TidalFraction, zoom_end: TidalFraction, pat: Any):
    """Override for `zoom` method"""
    return Pattern.reify(pat).zoom(zoom_begin, zoom_end)


@partial_decorator
def swing(n: TidalFraction, pat: Any):
    """Override for `zoom` method"""
    return Pattern.reify(pat).swing(n)


@partial_decorator
def swing_by(swing: TidalFraction, n: TidalFraction, pat: Any):
    """Override for `zoom` method"""
    return Pattern.reify(pat).swing_by(swing, n)


@partial_decorator
def slow(arg: int | float, pat: Any):
    """Override for `slow` method"""
    return Pattern.reify(pat).slow(arg)


@partial_decorator
def early(arg: int | float, pat: Any):
    """Override for `early` method"""
    return Pattern.reify(pat).early(arg)


@partial_decorator
def late(arg: int | float, pat: Any):
    """Override for `late` method"""
    return Pattern.reify(pat).late(arg)


@partial_decorator
def jux(arg: Callable, pat: Any):
    """Override for `jux` method"""
    return Pattern.reify(pat).jux(arg)


@partial_decorator
def union(pat_a, pat_b):
    """Override for `union` method"""
    return Pattern.reify(pat_b).union(pat_a)


def rev(pat):
    """Override for `rev` method"""
    return Pattern.reify(pat).rev()


def degrade(pat):
    return Pattern.reify(pat).degrade()


## Combinators


def run(n):
    return sequence(list(range(n)))


def scan(n):
    return slowcat(*[run(k) for k in range(1, n + 1)])


def timecat(*time_pat_tuples):
    """
    Like `fastcat` except that you provide proportionate sizes of the
    patterns to each other for when they're concatenated into one cycle.

    The larger the value in the list, the larger relative size the pattern
    takes in the final loop. If all values are equal then this is equivalent
    to `fastcat`.

    >>> timecat((1, s("bd*4")), (1, s("hh27*8")))

    """
    time_pat_tuples = [(TidalFraction(t), p) for t, p in time_pat_tuples]
    total = sum(TidalFraction(time) for time, _ in time_pat_tuples)
    arranged = []
    accum = TidalFraction(0)
    for time, pat in time_pat_tuples:
        arranged.append((accum, accum + TidalFraction(time), Pattern.reify(pat)))
        accum += time
    return stack(
        *[pat.compress(TidalFraction(s, total), TidalFraction(e, total)) for s, e, pat in arranged]
    )


# TODO: fix ??
def group_haps_by(eq: Callable, haps: List[Hap]) -> List[List[Hap]]:
    """returns List[Event] where each list of Events satisfies eq"""
    groups = []
    for hap in haps:
        match = next((i for i, other in enumerate(groups) if eq(hap, other)), -1)
        if match == -1:
            groups.append([hap])
        else:
            groups[match].append(hap)

    return groups


################################################################################
# SIGNAL FUNCTIONS
################################################################################


def saw() -> Pattern:
    """Returns a pattern that generates a saw wave between 0 and 1"""
    return signal(lambda t: t % 1)


def saw2() -> Pattern:
    """Returns a pattern that generates a saw wave between -1 and 1"""
    return saw().to_bipolar()


def isaw() -> Pattern:
    """Returns a pattern that generates an inverted saw wave between 0 and 1"""
    return signal(lambda t: 1 - (t % 1))


def isaw2() -> Pattern:
    """Returns a pattern that generates an inverted saw wave between -1 and 1"""
    return isaw().to_bipolar()


def tri() -> Pattern:
    """Returns a pattern that generates a triangle wave between 0 and 1"""
    return fastcat(isaw(), saw())


def tri2() -> Pattern:
    """Returns a pattern that generates a triangle wave between -1 and 1"""
    return fastcat(isaw2(), saw2())


def square() -> Pattern:
    """Returns a pattern that generates a square wave between 0 and 1"""
    return signal(lambda t: math.floor((t * 2) % 2))


def square2() -> Pattern:
    """Returns a pattern that generates a square wave between -1 and 1"""
    return square().to_bipolar()


def envL() -> Pattern:
    """
    Returns a Pattern of continuous Double values, representing
    a linear interpolation between 0 and 1 during the first cycle,
    then staying constant at 1 for all following cycles.
    """
    return signal(lambda t: max(0, min(t, 1)))


def envLR() -> Pattern:
    """
    Like envL but reversed.
    """
    return signal(lambda t: 1 - max(0, min(t, 1)))


def envEq() -> Pattern:
    """
    'Equal power' version of env, for gain-based transitions.
    """
    return signal(lambda t: math.sqrt(math.sin(math.pi / 2 * max(0, min(1 - t, 1)))))


def envEqR() -> Pattern:
    """
    Equal power reversed.
    """
    return signal(lambda t: math.sqrt(math.cos(math.pi / 2 * max(0, min(1 - t, 1)))))


def rand() -> Pattern:
    """
    Generate a continuous pattern of pseudo-random numbers between `0` and `1`.

    >>> rand().segment(4)

    """
    return signal(time_to_rand)


def irand(n: int) -> Pattern:
    """
    Generate a pattern of pseudo-random whole numbers between `0` to `n-1` inclusive.

    e.g this generates a pattern of 8 events per cycle, with values ranging from
    0 to 15 inclusive.

    >>> irand(16).segment(8)

    """
    return signal(lambda t: math.floor(time_to_rand(t) * n))


def _perlin_with(p: Pattern) -> Pattern:
    """
    1D Perlin noise. Takes a pattern as the RNG's "input" for Perlin noise, instead of
    automatically using the cycle count.

    """
    pa = p.with_value(math.floor)
    pb = p.with_value(lambda v: math.floor(v) + 1)

    def smoother_step(x: int | float) -> float:
        return 6.0 * x**5 - 15.0 * x**4 + 10.0 * x**3

    interp = lambda x: lambda a: lambda b: a + smoother_step(x) * (b - a)

    return (
        (p - pa)
        .with_value(interp)
        ._app_both(pa.with_value(time_to_rand))
        ._app_both(pb.with_value(time_to_rand))
    )


def perlin(p: Optional[Pattern] = None) -> Pattern:
    """
    1D Perlin (smooth) noise, works like rand but smoothly moves between random
    values each cycle.

    """
    if not p:
        p = signal(identity)
    return _perlin_with(p)


# Randomness
RANDOM_CONSTANT = 2**29
RANDOM_CYCLES_LENGTH = 300


def time_to_int_seed(a: float) -> int:
    """
    Stretch RANDOM_CYCLES_LENGTH cycles over the range of [0, RANDOM_CONSTANT]
    then apply the xorshift algorithm.

    """
    return xorwise(math.trunc((a / RANDOM_CYCLES_LENGTH) * RANDOM_CONSTANT))


def int_seed_to_rand(a: int) -> float:
    """Converts an integer seed to a random float between 0 and 1"""
    return (a % RANDOM_CONSTANT) / RANDOM_CONSTANT


def time_to_rand(a: float) -> float:
    """Converts a time value to a random float between 0 and 1"""
    return int_seed_to_rand(time_to_int_seed(a))


def signal(func: Callable) -> Pattern:
    """
    Base definition of a signal pattern. Returns an event with no whole, only a span and a value.
    The value is taken from the function applied to the midpoint of the span.
    """

    def _query(span: TimeSpan):
        return [Hap(None, span, func(span.midpoint()))]

    return Pattern(_query)


def sine() -> Pattern:
    """Returns a pattern that generates a sine wave between 0 and 1"""
    return signal(lambda t: (math.sin(math.pi * 2 * t) + 1) / 2)


def sine2() -> Pattern:
    """Returns a pattern that generates a sine wave between -1 and 1"""
    return signal(lambda t: math.sin(math.pi * 2 * t))


def cosine() -> Pattern:
    """Returns a pattern that generates a cosine wave between 0 and 1"""
    return sine().early(0.25)


def cosine2() -> Pattern:
    """Returns a pattern that generates a cosine wave between -1 and 1"""
    return sine2().early(0.25)


def mouseX() -> Pattern:
    """Returns a pattern that generates the x position of the mouse"""
    return signal(lambda _: mouse_position()[0] / screen_size()[0])


mousex = mouseX


def mouseY() -> Pattern:
    """Returns a pattern that generates the y position of the mouse"""
    return signal(lambda _: mouse_position()[1] / screen_size()[1])


mousey = mouseY


def wchoose(*vals):
    """Like @choose@, but works on an a list of tuples of values and weights"""
    return wchoose_with(rand(), *vals)


def wchoose_with(pat, *pairs):
    """
    Like `wchoose`, but works on an a list of tuples of values and weights

    Values are samples using the 0..1 ranged numerical pattern `pat`.

    """
    values, weights = list(zip(*pairs))
    cweights = list(accumulate(w for _, w in pairs))
    total = sum(weights)

    def match(r):
        if r < 0 or r > 1:
            raise ValueError("value from random pattern used by `wchooseby` is outside 0-1 range")
        indices = [i for i, c in enumerate(cweights) if c >= r * total]
        return values[indices[0]]

    return pat.with_value(match)


def choose(*vals):
    """Chooses randomly from the given list of values."""
    return choose_with(rand(), *vals)


def _choose_with(pat, *vals):
    return pat.range(0, len(vals)).with_value(lambda v: Pattern.reify(vals[math.floor(v)]))


def choose_with(pat, *vals):
    """
    Choose from the list of values (or patterns of values) using the given
    pattern of numbers, which should be in the range of 0..1

    """
    return _choose_with(pat, *vals).outer_join()


def choose_cycles(*vals):
    """
    Similar to `cat`, but rather than playing the given patterns in order, it
    picks them at random.

    >>> s(choose_cycles("bd*2 sn", "jvbass*3", "drum*2", "ht mt")

    """
    return choose(*vals).segment(1)


def randcat(*vals):
    """Alias of `choose_cycles`"""
    return choose_cycles(*vals)
