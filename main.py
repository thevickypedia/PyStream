import contextlib
import os
from multiprocessing import Process
from typing import NoReturn

import uvicorn

from models.config import env, fileio


class APIServer(uvicorn.Server):
    """Shared servers state that is available between all protocol instances.

    >>> APIServer

    See Also:
        Overrides `uvicorn.server.Server <https://github.com/encode/uvicorn/blob/master/uvicorn/server.py#L48>`__

    References:
        https://github.com/encode/uvicorn/issues/742#issuecomment-674411676
    """

    def install_signal_handlers(self) -> NoReturn:
        """Overrides ``install_signal_handlers`` in ``uvicorn.Server`` module."""
        pass

    @contextlib.contextmanager
    def run_in_parallel(self) -> None:
        """Initiates ``Server.run`` in a dedicated process."""
        self.run()


class APIHandler(Process):
    """Initiates the fast API in a dedicated process using uvicorn server.

    >>> APIHandler

    """

    def __init__(self):
        """Instantiates the class as a sub process."""
        super(APIHandler, self).__init__()

    def __del__(self):
        """Removes the html file."""
        os.remove(fileio.html) if os.path.isfile(fileio.html) else None

    def run(self) -> NoReturn:
        """Creates a custom log wrapper and triggers the server."""
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["formatters"]["default"]["fmt"] = "%(levelprefix)s [%(module)s:%(lineno)d] - %(message)s"

        argument_dict = {
            "app": "fast:app",
            "host": env.video_host,
            "port": env.video_port,
            "reload": True,
            "log_config": log_config
        }

        config = uvicorn.Config(**argument_dict)
        try:
            APIServer(config=config).run_in_parallel()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    APIHandler().run()
