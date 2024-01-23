import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from pystream.logger import logger
from pystream.models import config
from pystream.routers import auth, basics, video

app = FastAPI()
app.include_router(auth.router)
app.include_router(basics.router)
app.include_router(video.router)


# Exception handler for RedirectException
@app.exception_handler(config.RedirectException)
async def redirect_exception_handler(request: Request, exception: config.RedirectException) -> JSONResponse:
    """Custom exception handler to handle redirect.

    Args:
        request: Takes the ``Request`` object as an argument.
        exception: Takes the ``RedirectException`` object inherited from ``Exception`` as an argument.

    Returns:
        JSONResponse:
        Returns the JSONResponse with content, status code and cookie.
    """
    logger.debug("Exception headers: %s", request.headers)
    logger.debug("Exception cookies: %s", request.cookies)
    if request.url.path == config.static.login_endpoint:
        response = JSONResponse(content={"redirect_url": exception.location}, status_code=200)
    else:
        response = RedirectResponse(url=exception.location)
    if exception.detail:
        response.set_cookie("detail", exception.detail.upper())
    return response


async def startup_tasks() -> None:
    """Tasks that need to run during the API startup."""
    logger.info('Setting CORS policy.')
    origins = ["http://localhost.com", "https://localhost.com"]
    origins.extend(config.env.website)
    origins.extend(map((lambda x: x + '/*'), config.env.website))
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"])


async def shutdown_tasks() -> None:
    """Tasks that need to run during the API shutdown."""
    logger.info('Deleting %d files created during runtime.', len(config.static.deletions))
    logger.debug(config.static.deletions)
    for file in config.static.deletions:
        if file.exists():
            logger.debug("Deleting file: %s", file)
            os.remove(file)
        else:
            logger.warning("File '%s' does not exist", file)


async def start(**kwargs) -> None:
    """Starter function for the streaming API.

    Args:
        **kwargs: Keyword arguments to load the env config.
    """
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

    # Run startup tasks
    logger.info("Initiating startup tasks")
    await startup_tasks()
    await uvicorn_server.serve()  # Await uvicorn server
    logger.info("Initiating shutdown tasks")
    await shutdown_tasks()
