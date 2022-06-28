import logging


class VideoFilter(logging.Filter):
    """Class to initiate ``/video`` filter in logs while preserving other access logs.

    >>> VideoFilter

    See Also:
        - Overrides logging by implementing a subclass of ``logging.Filter``
        - The method ``filter(record)``, that examines the log record and returns True to log it or False to discard it.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out logging at ``/video`` from log streams.

        Args:
            record: ``LogRecord`` represents an event which is created every time something is logged.

        Returns:
            bool:
            False flag for the endpoint that needs to be filtered.
        """
        return record.getMessage().find("/video") == -1


class RootFilter(logging.Filter):
    """Class to initiate ``/`` filter in logs while preserving other access logs.

    >>> RootFilter

    See Also:
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
