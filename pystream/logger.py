import logging

from uvicorn.logging import ColourizedFormatter


class RootFilter(logging.Filter):
    """Class to initiate ``/`` filter in logs while preserving other access logs.

    >>> RootFilter

    See Also:
        - Filters ``"GET /login HTTP/1.1" 200 OK``, ``"GET / HTTP/1.1" 307 Temporary Redirect``, ``/video?vid_name=...``
        - Includes redundant logging for each iterable passed in ``StreamingResponse``
        - Overrides logging by implementing a subclass of ``logging.Filter``
        - The method ``filter(record)``, that examines the log record and returns True to log it or False to discard it.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out logging at ``/`` from log streams.

        Args:
            record: ``LogRecord`` represents an event which is created every time something is logged.

        Returns:
            bool:
            False flag for the endpoint that needs to be filtered.
        """
        return record.getMessage().find("/") == -1


logging.getLogger("uvicorn.access").addFilter(RootFilter())

logger = logging.getLogger(name="uvicorn.default")
# Use ColourizedFormatter for the logs to blend in with uvicorn's loging
color_formatter = ColourizedFormatter(fmt="{levelprefix} [{module}:{lineno}] - {message}", style="{", use_colors=True)
handler = logging.StreamHandler()
handler.setFormatter(fmt=color_formatter)
logger.addHandler(hdlr=handler)
