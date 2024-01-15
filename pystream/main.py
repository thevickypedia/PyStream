import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pystream.logger import logger
from pystream.models import config
from pystream.routers import auth, basics, video

app = FastAPI()
app.include_router(auth.router)
app.include_router(basics.router)
app.include_router(video.router)


# noinspection HttpUrlsUsage
def startup_tasks() -> None:
    """Tasks that need to run during the API startup."""
    logger.info('Setting CORS policy.')
    origins = ["http://localhost.com", "https://localhost.com"]
    origins.extend(config.env.website)
    origins.extend(map((lambda x: x + '/*'), config.env.website))
    app.add_middleware(CORSMiddleware, allow_origins=origins)


def start(**kwargs) -> None:
    """Starter function for the streaming API.

    Args:
        **kwargs: Keyword arguments to load the env config.
    """
    # todo: Implement websockets to set a counter clock and logout automatically after a set timeout
    # Load and validate env vars/arguments
    config.env = config.EnvConfig(**kwargs)

    # Configure uvicorn server with custom logging
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s\t%(levelname)8s\t%(module)10s:%(lineno)d\t\t%(message)s"
    # reload flag is set to false,
    #   1: reloading in the middle of streaming will make the process to wait for the connection to close
    #   2: connection will be open until the streaming stops (this is a circular dependency)
    argument_dict = {
        "app": f"{__name__}:app",
        "host": config.env.video_host,
        "port": config.env.video_port,
        "reload": False,
        "log_config": log_config,
        "workers": config.env.workers
    }

    # Run startup tasks
    startup_tasks()
    uvicorn.run(**argument_dict)
