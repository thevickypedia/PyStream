from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from pystream.logger import logger
app = FastAPI()


@app.route('/{_:path}')
async def https_redirect(request: Request) -> RedirectResponse:
    """Redirects HTTP connection to HTTPS.

    Args:
        request: Takes the ``Request`` object as an argument.

    Returns:
        RedirectResponse:
        Returns a RedirectResponse changing the scheme to https.
    """
    logger.info("Received HTTP request from %s, redirecting to HTTPS", request.client.host)
    return RedirectResponse(request.url.replace(scheme='https'))
