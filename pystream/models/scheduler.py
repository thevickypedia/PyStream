import threading
from typing import Any, Callable, Dict, Tuple


class RepeatedTimer:
    """Instantiates RepeatedTimer object to kick off the threading.Timer object with custom intervals.

    >>> RepeatedTimer

    """

    def __init__(
        self,
        interval: int,
        function: Callable,
        args: Tuple = None,
        kwargs: Dict[str, Any] = None,
    ):
        """Repeats the ``Timer`` object from threading.

        Args:
            interval: Interval in seconds.
            function: Function to trigger with intervals.
            args: Arguments for the function.
            kwargs: Keyword arguments for the function.
        """
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.is_running = False

    def _run(self):
        """Triggers the target function."""
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        """Trigger target function if timer isn't running already."""
        if not self.is_running:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        """Stop the timer and cancel all futures."""
        self._timer.cancel()
        self.is_running = False

    def cancel(self):
        """Initiate cancellation."""
        self.stop()
