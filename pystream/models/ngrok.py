import socket
from logging import Logger
from typing import NoReturn, Union

import requests
from pydantic import HttpUrl

from pystream.models import config


def get_tunnel(logger: Logger) -> Union[HttpUrl, NoReturn]:
    """Checks for any active public URL tunneled using Ngrok.

    Returns:
        HttpUrl:
        Ngrok public URL.
    """
    try:
        response = requests.get(url="http://localhost:4040/api/tunnels")
        if response.ok:
            tunnels = response.json().get('tunnels', [])
            protocols = list(filter(None, [tunnel.get('proto') for tunnel in tunnels]))
            for tunnel in tunnels:
                if 'https' in protocols and tunnel.get('proto') != 'https':
                    continue
                if hosted := tunnel.get('config', {}).get('addr'):
                    if int(hosted.split(':')[-1]) == config.env.video_port:
                        return tunnel.get('public_url')
    except (requests.exceptions.RequestException, requests.exceptions.Timeout, ConnectionError, TimeoutError,
            requests.exceptions.JSONDecodeError) as error:
        logger.error(error)


def run_tunnel(logger: Logger) -> None:
    """Runs reverse proxy on video port to expose it using a public URL.

    Args:
        logger: Takes uvicorn custom logger as an argument.
    """
    if public_url := get_tunnel(logger=logger):
        logger.info(f"Already hosting {config.env.video_port} on {public_url}")
        return

    from pyngrok import ngrok
    from pyngrok.exception import PyngrokError
    ngrok.set_auth_token(token=config.env.ngrok_token)
    try:
        endpoint = ngrok.connect(config.env.video_port, "http",
                                 options={"remote_addr": f"{config.env.video_host}:{config.env.video_port}"})
        public_url = endpoint.public_url.replace('http', 'https')
    except PyngrokError as error:
        logger.error(error)
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.listen(1)
    connection = None

    print(public_url)
    logger.info(f'Tunneling http://{config.env.video_host}:{config.env.video_port} through public URL: {public_url}')
    try:
        connection, client_address = sock.accept()
    except KeyboardInterrupt:
        logger.warning('Interrupted manually.')
        if connection:
            connection.close()
        logger.info("Connection closed.")
    ngrok.kill(pyngrok_config=None)  # uses default config when None is passed
    sock.close()
