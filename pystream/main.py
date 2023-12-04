from multiprocessing import Process

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pystream.logger import logger
from pystream.models import config, ngrok
from pystream.routers import auth, basics, video

app = FastAPI()
app.include_router(auth.router)
app.include_router(basics.router)
app.include_router(video.router)


def startup_tasks() -> None:
    """Tasks that need to run during the API startup."""
    config.env.video_host = str(config.env.video_host)
    logger.info('Setting CORS policy.')
    origins = ["http://localhost.com", "https://localhost.com"]
    if config.env.website:
        origins.extend([
            f"http://{config.env.website.host}",
            f"https://{config.env.website.host}",
            f"http://{config.env.website.host}/*",
            f"https://{config.env.website.host}/*"
        ])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex='https://.*\.ngrok\.io/*',  # noqa: W605
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def start(**kwargs) -> None:
    """Starter function for the streaming API.

    Args:
        **kwargs: Keyword arguments to load the env config.
    """
    # todo: Implement websockets to set a counter clock and logout automatically after a set timeout
    config.env = config.EnvConfig(**kwargs)
    startup_tasks()
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(levelprefix)s [%(module)s:%(lineno)d] - %(message)s"
    # reload flag is set to false,
    #   1: reloading in the middle of streaming will make the process to wait for the connection to close
    #   2: connection will be open as long as the streaming stops (this is a circular dependency)
    argument_dict = {
        "app": f"{__name__}:app",
        "host": config.env.video_host,
        "port": config.env.video_port,
        "reload": False,
        "log_config": log_config,
        "workers": config.env.workers
    }
    if config.env.ngrok_token:
        try:
            import pyngrok  # noqa: F401
        except ImportError as error:
            raise ImportError(
                f"\n\n{error.name}\n\tpip install 'stream-localhost[ngrok]'"
            )
        Process(target=ngrok.run_tunnel, args=(logger,), kwargs=kwargs).start()
    uvicorn.run(**argument_dict)
