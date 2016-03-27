""" The Observable Monad

* https://www.youtube.com/watch?v=looJcaeboBY&feature=youtu.be
* https://wiki.haskell.org/MonadCont_under_the_hood
* http://blog.sigfpe.com/2008/12/mother-of-all-monads.html
* http://www.haskellforall.com/2012/12/the-continuation-monad.html

"""

from typing import Any, Callable

from .util import identity, compose
from .abc import Monad, Functor


class Observable(Monad, Functor):

    """The Rx Observable Monad.

    The Rx Observable monad is based on the Continuation monad
    representing suspended computations in continuation-passing style
    (CPS).
    """

    def __init__(self, subscribe: Callable[[Callable], Any]):
        """Observable constructor.

        Keyword arguments:
        on_next -- A callable
        """
        self._get_value = lambda: subscribe

    @classmethod
    def unit(cls, x: Any) -> 'Observable':
        """x -> Observable x"""
        return cls(lambda on_next: on_next(x))
    just = unit

    def map(self, mapper: Callable[[Any], Any]) -> 'Observable':
        r"""Map a function over an on_next continuation.

        Haskell: fmap f m = Cont $ \c -> runCont m (c . f)
        """
        source = self
        return Observable(lambda on_next: source.subscribe(compose(on_next, mapper)))

    def bind(self, fn: Callable[[Any], 'Observable']) -> 'Observable':
        r"""Chain continuation passing on_next functions.

        Haskell: m >>= k = Cont $ \c -> runCont m $ \a -> runCont (k a) c
        """
        return Observable(lambda on_next: self.subscribe(lambda a: fn(a).subscribe(on_next)))
    flat_map = bind

    def filter(self, predicate) -> 'Observable':
        """Filter the on_next continuation functions"""
        source = self

        def subscribe(on_next):
            def _next(x):
                if predicate(x):
                    on_next(x)

            return source.subscribe(_next)
        return Observable(subscribe)

    @staticmethod
    def call_cc(fn: Callable) -> 'Observable':
        r"""call-with-current-continuation.

        Haskell: callCC f = Cont $ \c -> runCont (f (\a -> Cont $ \_ -> c a )) c
        """
        def subscribe(on_next):
            return fn(lambda a: Observable(lambda _: on_next(a))).subscribe(on_next)

        return Observable(subscribe)

    def subscribe(self, on_next) -> Any:
        return self._get_value()(on_next)

    def __eq__(self, other) -> bool:
        return self.subscribe(identity) == other.subscribe(identity)
