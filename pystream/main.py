from multiprocessing import Process

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pystream.logger import logger
from pystream.models import config, ngrok, scheduler, squire
from pystream.routers import auth, basics, video

app = FastAPI()
app.include_router(auth.router)
app.include_router(basics.router)
app.include_router(video.router)


def task() -> None:
    """Update the shared static object member to response from stream all content."""
    config.static.landing_page = squire.get_all_stream_content()


def startup_tasks() -> None:
    """Tasks that need to run during the API startup."""
    origins = ["http://localhost.com", "https://localhost.com"]
    if config.env.website:
        logger.info('Setting CORS policy.')
        origins.extend([
            f"http://{config.env.website.host}",
            f"https://{config.env.website.host}",
            f"http://{config.env.website.host}/*",
            f"https://{config.env.website.host}/*"
        ])
    kwargs = dict(allow_origins=origins)
    if config.env.ngrok_token:
        kwargs['allow_origin_regex'] = 'https://.*\.ngrok\.io/*'  # noqa: W605
    app.add_middleware(CORSMiddleware, **kwargs)
    task()


async def start(**kwargs) -> None:
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
    uvicorn_config = uvicorn.Config(**argument_dict)
    uvicorn_server = uvicorn.Server(config=uvicorn_config)

    # Validate and initiate tunneling via ngrok (if chosen)
    if config.env.ngrok_token:
        try:
            import pyngrok  # noqa: F401
        except ImportError as error:
            raise ImportError(
                f"\n\n{error.name}\n\tpip install 'stream-localhost[ngrok]'"
            )
        Process(target=ngrok.run_tunnel, args=(logger,), kwargs=kwargs).start()

    # Run startup tasks
    startup_tasks()
    if config.env.scan_interval:
        # Initiate background task with repeated timer
        background_task = scheduler.RepeatedTimer(function=task, interval=config.env.scan_interval)
        background_task.start()  # Start background task
    else:
        logger.warning("Without background scans, new .mp4 files at %s will not reflect in the UI",
                       config.env.video_source)
        background_task = None
    await uvicorn_server.serve()  # Await uvicorn server
    if background_task:
        background_task.stop()  # Stop background task when server process has finished
