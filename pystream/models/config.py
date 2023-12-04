import os
import socket
from ipaddress import IPv4Address
from typing import Union

from pydantic import (BaseModel, DirectoryPath, Field, HttpUrl, PositiveInt,
                      ValidationInfo, field_validator)
from pydantic_settings import BaseSettings


def ip_address() -> Union[str, None]:
    """Uses simple check on network id to see if it is connected to local host or not.

    Returns:
        str:
        Private IP address of host machine.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as socket_:
        try:
            socket_.connect(("8.8.8.8", 80))
            return socket_.getsockname()[0]
        except OSError:
            raise OSError(
                "\n\tUnable to fetch local IP, please set it manually or set `ip_hosted` to `False`"
            )


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    username: str
    password: str
    video_source: DirectoryPath

    ip_hosted: bool = False
    video_port: PositiveInt = 8000
    website: Union[HttpUrl, None] = None
    ngrok_token: Union[str, None] = None
    video_host: IPv4Address = socket.gethostbyname("localhost")
    workers: int = Field(1, le=os.cpu_count(), ge=1, env="WORKERS")

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        env_file = os.environ.get("env_file") or os.environ.get("ENV_FILE") or ".env"
        extra = "ignore"

    # noinspection PyMethodParameters
    @field_validator('video_host', mode='after', check_fields=True)
    def validate_video_host(cls, video_host: IPv4Address, values: ValidationInfo) -> str:
        """Set `video_host` to local IP address if `ip_hosted` flag is set to True and `video_host` is set to default.

        Args:
            video_host: Variable value of `video_host`
            values: Values of all object.

        Returns:
            str:
            Local IP address as a string.
        """
        if values.data.get('ip_hosted') and str(video_host) == socket.gethostbyname("localhost"):
            return ip_address()
        return str(video_host)


class FileIO(BaseModel):
    """Loads all the files' path required/created.

    >>> FileIO

    """

    index: str = "index.html"
    list_files: str = "list_files.html"


class Static(BaseModel):
    """Object to store static values.

    >>> Static

    """

    CHUNK_SIZE: PositiveInt = 1024 * 1024
    VAULT: str = "stream"  # Use a masked location to hide the real path in the UI


class Session(BaseModel):
    """Object to store session information.

    >>> Session

    """

    info: dict = {}


env = EnvConfig
fileio = FileIO()
static = Static()
session = Session()
