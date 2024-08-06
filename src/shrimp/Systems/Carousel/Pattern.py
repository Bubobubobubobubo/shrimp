import math
from functools import reduce, partial
from itertools import accumulate
from typing import Self, List, Callable, Optional, Iterable, Any, Tuple, Dict
from .TimeSpan import TimeSpan, TidalFraction
from .Event import Event
from .Utils import flatten, identity, bjorklund, curry, remove_nones, xorwise
import types


class Pattern:
    """
    Pattern class, representing discrete and continuous events as a function of time.

    A pattern is a function that takes a time span and returns a list of events. The
    time span represents the time interval over which the pattern is queried.
    """

    def __init__(self, query: Callable, tactus: Optional[int] = None):
        self.query: Callable[[TimeSpan], List[Event]] = query
        self._tactus = tactus
        # TODO: add all the tactus related things
        self._generate_applicative_methods()

    @property
    def tactus(self) -> Optional[int]:
        return self._tactus

    @tactus.setter
    def tactus(self, tactus: int):
        self._tactus = tactus

    def with_tactus(self, f) -> Self:
        return Pattern(self.query, None if self.tactus is None else f(self.tactus))

    def has_tactus(self) -> bool:
        return self.tactus is not None

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

    def split_queries(self) -> Self:
        """Splits queries at cycle boundaries.

        Note: This makes some calculations easier to express, as all events are then
        constrained to happen within a cycle.
        """

        def _query(span: TimeSpan) -> List[Event]:
            return flatten([self.query(subspan) for subspan in span.span_cycles()])

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

        def _query(span: TimeSpan) -> List[Event]:
            return [event.with_span(func) for event in self.query(span)]

        return Pattern(_query)

    def with_event_time(self, func: Callable) -> Self:
        """Returns a new pattern, with the function applied to both the begin
        and end of each event timespan.
        """
        return self.with_event_span(lambda span: span.with_time(func))

    def with_value(self, func: Callable) -> Self:
        """Returns a new pattern, with the function applied to the value of each event."""

        def _query(span: TimeSpan) -> List[Event]:
            return [event.with_value(func) for event in self.query(span)]

        return Pattern(_query)

    def fmap(self, func: Callable) -> Self:
        """Maps a function over the values of the pattern."""
        return self.with_value(lambda x: func(x))

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
        return self.filter_events(Event.has_onset)

    # applyPatToPatLeft :: Pattern (a -> b) -> Pattern a -> Pattern b
    # applyPatToPatLeft pf px = Pattern q
    #    where q st = catMaybes $ concatMap match $ query pf st
    #            where
    #              match ef = map (withFX ef) (query px $ st {arc = wholeOrPart ef})
    #              withFX ef ex = do let whole' = whole ef
    #                                part' <- subArc (part ef) (part ex)
    #                                return (Event (combineContexts [context ef, context ex]) whole' part' (value ef $ value ex))

    def _app_both( self, pat_val) -> Self:
        """TODO: check if implementation is correct"""

        def whole_func(span_a, span_b):
            if (span_a is not None) and (span_b is not None):
                return span_a.intersection(span_b, throw=True)
            else:
                return None

        result = self._appwhole(whole_func, pat_val)
        if self.tactus is not None:
            result.tactus = math.lcm(pat_val.tactus, self.tactus)
        return result


        return NotImplementedError

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

        def _query(span: TimeSpan) -> List[Event]:
            event_funcs = self.query(span)
            event_vals = pat_val.query(span)

            def apply(event_func: Event, event_val: Event) -> Optional[Event]:
                s = event_func.part.intersection(event_val.part)
                return (
                    None
                    if s is None
                    else Event(
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

    # A bit more complicated than this..
    def app_both(self, other: Self) -> Self:
        """Tidal's <*> operator"""

        def whole_func(span_a: TimeSpan, span_b: TimeSpan) -> Optional[TimeSpan]:
            return span_a.intersection(span_b, throw=True) if span_a and span_b else None

        return self._app_whole(whole_func, other)

    def _app_left(self, other: Self) -> Self:
        """Tidal's <* operator.

        Args:
            pat_val (Pattern): The pattern to apply to the left of the current pattern

        Returns:
            Pattern: A new pattern with the given pattern applied to the left
        """

        def _query(span: TimeSpan) -> List[Event]:
            events: List[Event] = []

            # Iterating over all the events in the current pattern
            for func in self.query(span):
                event_vals = other.query(func.whole_or_part())

                # Iterating over all the events in the pattern passed as argument
                for val in event_vals:
                    new_whole: TimeSpan = func.whole
                    new_part: TimeSpan = func.part.intersection(val.part)
                    if new_part:
                        new_value = func.value(val.value)
                        events.append(Event(new_whole, new_part, new_value))
            return events

        result = Pattern(_query)
        result.tactus = self.tactus
        return result

    def _app_right(self, other: Self) -> Self:
        """Tidal's *> operator"""

        def _query(span: TimeSpan) -> List[Event]:
            events: List[Event] = []

            # Iterating over all the events in the other pattern
            for val in other.query(span):
                event_funcs = self.query(val.whole_or_part())

                # Iterating over all the events in the current pattern
                for func in event_funcs:
                    new_whole: TimeSpan = val.whole
                    new_part: TimeSpan = func.part.intersection(val.part)
                    if new_part:
                        new_value = func.value(val.value)
                        events.append(Event(new_whole, new_part, new_value))
            return events

        result = Pattern(_query)
        result.tactus = other.tactus
        return result

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
        )._app_left(reify(other))

    def __radd__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b + a)
        )._app_left(reify(other))

    def __sub__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: a - b)
        )._app_left(reify(other))

    def __rsub__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b - a)
        )._app_left(reify(other))

    def __mul__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: a * b)
        )._app_left(reify(other))

    def __rmul__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b * a)
        )._app_left(reify(other))

    def __truediv__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: a / b)
        )._app_left(reify(other))

    def __rtruediv__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b / a)
        )._app_left(reify(other))

    def __floordiv__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: a // b)
        )._app_left(reify(other))

    def __rfloordiv__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b // a)
        )._app_left(reify(other))

    def __mod__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: a % b)
        )._app_left(reify(other))

    def __rmod__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b % a)
        )._app_left(reify(other))

    def __pow__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: a**b)
        )._app_left(reify(other))

    def __rpow__(self, other: Self) -> Self:
        return self.with_value(
            lambda x: lambda y: self._apply_op(x, y, lambda a, b: b**a)
        )._app_left(reify(other))

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

    def _bind_whole(self, choose_whole, func: Callable) -> Self:
        pat_val: Pattern = self

        def _query(span: TimeSpan) -> List[Event]:
            def with_whole(a: TimeSpan, b: TimeSpan) -> Event:
                return Event(choose_whole(a.whole, b.whole), b.part, b.value)

            def match(a: Event) -> List[Event]:
                return [with_whole(a, b) for b in func(a.value).query(a.part)]

            return flatten([match(ev) for ev in pat_val.query(span)])

        return Pattern(_query)

    def bind(self, func: Callable) -> Self:
        """TODO: add docstring"""

        def whole_func(a: TimeSpan, b: TimeSpan):
            return a.intersect(b, throw=True) if a and b else None

        return self._bind_whole(whole_func, func)

    def join(self) -> Self:
        """Flattens a pattern of patterns into a pattern, where wholes are
        the intersection of matched inner and outer events."""
        return self.bind(identity)

    def inner_bind(self, func: Callable) -> Self:
        """TODO: add docstring"""
        return self._bind_whole(lambda _, b: b, func)

    def inner_join(self) -> Self:
        """Flattens a pattern of patterns into a pattern, where wholes are
        taken from inner events."""
        return self.inner_bind(identity)

    def outer_bind(self, func) -> Self:
        """TODO: add docstring"""
        return self._bind_whole(lambda a, _: a, func)

    def outer_join(self) -> Self:
        """Flattens a pattern of patterns into a pattern, where wholes are
        taken from outer events."""
        return self.outer_bind(identity)

    def discreteOnly(self) -> Self:
        """
        Removes continuous events that don't have a 'whole' timespan.
        TODO: check if this is the right way to implement this
        """
        return self.filter_events(lambda event: event.whole)

    def squeezeJoin(self) -> Self:
        return NotImplementedError

    def squeezeBind(self) -> Self:
        raise NotImplementedError

    @staticmethod
    def _patternify(method: Callable) -> Self:
        def patterned(self, *args):
            pat_arg = sequence(*args)
            return pat_arg.with_value(lambda arg: method(self, arg)).inner_join()

        return patterned

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

    def _early(self, offset: float) -> Self:
        """Equivalent of Tidal's <~ operator"""
        offset = TidalFraction(offset)
        return self.with_query_time(lambda t: t + offset).with_event_time(lambda t: t - offset)

    early = _patternify(_early)

    def _late(self, offset: float) -> Self:
        """Equivalent of Tidal's ~> operator"""
        return self._early(0 - offset)

    late = _patternify(_late)

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

    def off(self, time_pat: Self, func: Callable) -> Self:
        """TODO: add docstring"""
        return stack(self, func(self.early(time_pat)))

    def every(self, n: float, func: Callable) -> Self:
        """Applies a function to every nth cycle of a pattern"""
        pats = [func(self)] + ([self] * (n - 1))
        return slowcat(*pats)

    def append(self, other: Self) -> Self:
        """Appends two patterns together and compress them into a single cycle"""
        return fastcat(self, other)


    def rev(self) -> Self:
        """Returns the reversed the pattern"""

        def _query(span: TimeSpan):
            cycle = span.begin.sam()
            next_cycle = span.begin.next_sam()

            def reflect(to_reflect: Event) -> Event:
                reflected = to_reflect.with_time(lambda time: cycle + (next_cycle - time))
                (reflected.begin, reflected.end) = (reflected.end, reflected.begin)
                return reflected

            events = self.query(reflect(span))
            return [event.with_span(reflect) for event in events]

        return Pattern(_query).split_queries()

    def jux(self, func: Callable, by: int | float = 1) -> Self:
        """Classic Tidal Function."""

        left = self.with_value(
            lambda val: dict(list(val.items()) + [("pan", val.get("pan", 0.5) - by / 2)])
        )
        right = self.with_value(
            lambda val: dict(list(val.items()) + [("pan", val.get("pan", 0.5) + by / 2)])
        )

        return stack(left, func(right))

    def first_cycle(self) -> List[Event]:
        """Returns the events of the first cycle of the pattern"""
        return sorted(self.query(TimeSpan(TidalFraction(0), TidalFraction(1))))

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
        return self.fastgap(TidalFraction(1, end - begin)).late(begin)

    def fastgap(self, factor: float) -> Self:
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

        def _query(span: TimeSpan) -> List[Event]:
            new_span = TimeSpan(munge_query(span.begin), munge_query(span.end))
            if new_span.begin == span.begin.next_sam():
                return []
            return [e.with_span(event_span_func) for e in self.query(new_span)]

        return Pattern(_query).split_queries()

    def striate(self, n_pat: int) -> Self:
        """
        Cut samples into bits in a similar way to `chop`

        Pattern must be an `s` control pattern, and the resulting pattern will
        contain `begin` and `end` values to be interpreted by the synth
        (SuperDirt, Dirt, etc.)

        """
        return reify(n_pat).with_value(lambda n: self._striate(n)).inner_join()

    def _striate(self, n: int) -> Self:
        def merge_sample(samp_range: dict) -> Self:
            return self.with_value(
                lambda v: {"s": v["s"] if isinstance(v, dict) else v, **samp_range}
            )

        samp_ranges = [dict(begin=i / n, end=(i + 1) / n) for i in range(n)]
        return fastcat(*[merge_sample(r) for r in samp_ranges])

    def segment(self, n: int) -> Self:
        """
        Samples the pattern at a rate of `n` events per cycle.

        Useful for turning a continuous pattern into a discrete one.

        >>> rand().segment(4)

        """
        return pure(identity).fast(n)._app_left(self)

    def range(self, minimum: Self, maximum: Self) -> Self:
        """
        Rescales values to the range [min, max]

        Assumes pattern is numerical, containing unipolar values in the range
        [0, 1].

        """
        return self * (maximum - minimum) + minimum

    def rangex(self, minimum: Self, maximum: Self) -> Self:
        """
        Rescales values to the range [min, max] following an exponential curve

        Assumes pattern is numerical, containing unipolar values in the range
        [0, 1].

        """
        return self.range(math.log(minimum), math.log(maximum)).with_value(math.exp)

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
        return reify(by_pat).with_value(lambda by: self._sometimes_by(by, func)).inner_join()

    def always(self, func: Callable) -> Self:
        return self.sometimes_by(1, func)

    def almostAlways(self, func: Callable) -> Self:
        return self.sometimes_by(0.90, func)

    def often(self, func: Callable) -> Self:
        return self.sometimes_by(0.75, func)

    def sometimes(self, func: Callable) -> Self:
        """
        Applies a function to pattern, around 50% of the time, at
        random.

        >>> s("bd").fast(8).sometimes(lambda p: p << speed(2))

        """
        return self.sometimes_by(0.5, func)

    def rarely(self, func: Callable) -> Self:
        return self.sometimes_by(0.25, func)

    def almostNever(self, func: Callable) -> Self:
        return self.sometimes_by(0.10, func)

    def never(self, func: Callable) -> Self:
        return self.sometimes_by(0, func)

    def _sometimes_by(self, by: float, func: Callable) -> Self:
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
        return reify(by_pat).with_value(lambda by: self._sometimes_pre_by(by, func)).inner_join()

    def _sometimes_pre_by(self, by: float, func: Callable) -> Self:
        return stack(self.degrade_by(by), func(self).undegrade_by(by))

    def somecycles(self, func: Callable) -> Self:
        return self.somecycles_by(0.5, func)

    def somecycles_by(self, by_pat: float, func: Callable) -> Self:
        return reify(by_pat).with_value(lambda by: self._somecycles_by(by, func)).inner_join()

    def _somecycles_by(self, by: float, func: Callable) -> Self:
        return self.when_cycle(lambda c: time_to_rand(c) < by, func)

    def remove_none(self):
        """TODO: add docstring"""
        return self.filter_values(lambda v: v)

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
        self.with_value(lambda x: x.fast(factor)).squeezeJoin() # TODO: squeezeJoin does not exist

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

    def __repr__(self):
        events = [str(e) for e in self.first_cycle()]
        events_str = ",\n ".join(events).replace("\n", "\n ")
        return f"~[{events_str}] ...~"

    def __eq__(self, other):
        raise NotImplementedError(
            "Patterns cannot be compared. Evaluate them with `.first_cycle()` or similar"
        )


reify = Pattern.reify


def silence() -> Pattern:
    """Returns a pattern that plays no events"""
    return Pattern(lambda _: [])


def _tparams(func, *params: Any) -> Pattern:
    if not params:
        return silence()
    curried_func = curry(func)
    return reduce(
        lambda a, b: a.app_both(reify(b)),
        params[1:],
        reify(params[0]).with_value(curried_func),
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
            Event(TidalFraction(subspan.begin).whole_cycle(), subspan, value)
            for subspan in span.span_cycles()
        ]

    return Pattern(_query)


def steady(value: Any) -> Pattern:
    def _query(span: TimeSpan) -> List[Event]:
        return [Event(None, span, value)]

    return Pattern(_query)


def slowcat(*pats: Pattern) -> Pattern:
    """
    Concatenation: combines a list of patterns, switching between them
    successively, one per cycle.
    (currently behaves slightly differently from Tidal)
    """
    pats = [reify(pat) for pat in pats]

    def _query(span: TimeSpan) -> List[Event]:
        pat = pats[math.floor(span.begin) % len(pats)]
        return pat.query(span)

    return Pattern(_query).split_queries()


def fastcat(*pats: Pattern) -> Pattern:
    """Concatenation: as with slowcat, but squashes a cycle from each
    pattern into one cycle"""
    return slowcat(*pats).fast(len(pats))


cat = fastcat
seq = fastcat


def stack(*pats: Pattern) -> Self:
    """Pile up patterns"""
    pats = [reify(pat) for pat in pats]

    def _query(span: TimeSpan) -> List[Event]:
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


def partial_decorator(f: Callable) -> Callable:
    """Decorator to allow module-level function versions of pattern methods"""

    def wrapper(*args):
        try:
            return f(*args)
        except (TypeError, AttributeError) as _:
            return partial(f, *args)

    return wrapper


# TODO: continue from here


@partial_decorator
def fast(arg: int | float, pat: Any):
    """Override for `fast` method"""
    return reify(pat).fast(arg)


@partial_decorator
def slow(arg: int | float, pat: Any):
    """Override for `slow` method"""
    return reify(pat).slow(arg)


@partial_decorator
def early(arg: int | float, pat: Any):
    """Override for `early` method"""
    return reify(pat).early(arg)


@partial_decorator
def late(arg: int | float, pat: Any):
    """Override for `late` method"""
    return reify(pat).late(arg)


@partial_decorator
def jux(arg: Callable, pat: Any):
    """Override for `jux` method"""
    return reify(pat).jux(arg)


@partial_decorator
def union(pat_a, pat_b):
    """Override for `union` method"""
    return reify(pat_b).union(pat_a)


def rev(pat):
    """Override for `rev` method"""
    return reify(pat).rev()


def degrade(pat):
    return reify(pat).degrade()


## Combinators


def run(n):
    return sequence(list(range(n)))


def scan(n):
    return slowcat(*[run(k) for k in range(1, n + 1)])


def _choose_with(pat, *vals):
    return pat.range(0, len(vals)).with_value(lambda v: reify(vals[math.floor(v)]))


def choose_with(pat, *vals):
    """
    Choose from the list of values (or patterns of values) using the given
    pattern of numbers, which should be in the range of 0..1

    """
    return _choose_with(pat, *vals).outer_join()


def choose(*vals):
    """Chooses randomly from the given list of values."""
    return choose_with(rand(), *vals)


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


def wchoose(*vals):
    """Like @choose@, but works on an a list of tuples of values and weights"""
    return wchoose_with(rand(), *vals)


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
        return [Event(None, span, func(span.midpoint()))]

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


def saw() -> Pattern:
    """Returns a pattern that generates a saw wave between 0 and 1"""
    return signal(lambda t: t % 1)


def saw2() -> Pattern:
    """Returns a pattern that generates a saw wave between -1 and 1"""
    return signal(lambda t: (t % 1) * 2)


def isaw() -> Pattern:
    """Returns a pattern that generates an inverted saw wave between 0 and 1"""
    return signal(lambda t: 1 - (t % 1))


def isaw2() -> Pattern:
    """Returns a pattern that generates an inverted saw wave between -1 and 1"""
    return signal(lambda t: (1 - (t % 1)) * 2)


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
    return signal(lambda t: (math.floor((t * 2) % 2) * 2) - 1)


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
        .app_both(pa.with_value(time_to_rand))
        .app_both(pb.with_value(time_to_rand))
    )


def perlin(p: Optional[Pattern] = None) -> Pattern:
    """
    1D Perlin (smooth) noise, works like rand but smoothly moves between random
    values each cycle.

    """
    if not p:
        p = signal(identity)
    return _perlin_with(p)


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
        arranged.append((accum, accum + TidalFraction(time), reify(pat)))
        accum += time
    return stack(
        *[pat.compress(TidalFraction(s, total), TidalFraction(e, total)) for s, e, pat in arranged]
    )
