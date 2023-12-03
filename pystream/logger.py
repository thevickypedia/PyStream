import logging

from uvicorn.logging import ColourizedFormatter

from pystream.models import filters

logging.getLogger("uvicorn.access").addFilter(filters.VideoFilter())
logging.getLogger("uvicorn.access").addFilter(filters.RootFilter())

logger = logging.getLogger(name="uvicorn.default")
console_formatter = ColourizedFormatter(fmt="{levelprefix} [{module}:{lineno}] - {message}", style="{",
                                        use_colors=True)
handler = logging.StreamHandler()
handler.setFormatter(fmt=console_formatter)
logger.addHandler(hdlr=handler)
