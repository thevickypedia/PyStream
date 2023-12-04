import functools
import time
from typing import Callable


def timed_cache(max_age: int, maxsize: int = 128, typed: bool = False):
    """Least-recently-used cache decorator with time-based cache invalidation.

    Args:
        max_age: Time to live for cached results (in seconds).
        maxsize: Maximum cache size (see `functools.lru_cache`).
        typed: Cache on distinct input types (see `functools.lru_cache`).

    See Also:
        - ``lru_cache`` takes all params of the function and creates a key
        - If even one key is changed, it will map to new entry thus refreshed.
        - This is just a trick to force lrc_cache lib to provide TTL on top of max size.
        - Uses ``time.monotonic`` since ``time.time`` relies on the system clock and may not be monotonic
        - | It's not guaranteed to always increase, it may in fact decrease if
          | the machine syncs its system clock over a network
    """

    def _decorator(fn: Callable):
        @functools.lru_cache(maxsize=maxsize, typed=typed)
        def _new(*args, __timed_hash, **kwargs):
            return fn(*args, **kwargs)

        @functools.wraps(fn)
        def _wrapped(*args, **kwargs):
            return _new(*args, **kwargs, __timed_hash=int(time.monotonic() / max_age))

        return _wrapped

    return _decorator


if __name__ == '__main__':
    def expensive_function():
        """Function that performs an expensive task."""
        print('Not cached')
        return "response"

    @timed_cache(max_age=5)
    def cacher():
        """Function that's being called frequently, which caches the result of expensive function."""
        return expensive_function()

    for _ in range(10):
        print(cacher())
        time.sleep(1)
