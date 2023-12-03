import os
import socket
from ipaddress import IPv4Address
from typing import Union

from pydantic import (DirectoryPath, Field, HttpUrl, field_validator, PositiveInt, ValidationInfo, BaseModel)
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
    website: HttpUrl | None = None
    ngrok_token: str | None = None
    video_host: IPv4Address = socket.gethostbyname("localhost")
    workers: int = Field(1, le=os.cpu_count(), ge=1, env="WORKERS")

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        env_file = ".env"
        extra = "ignore"

    # noinspection PyMethodParameters
    @field_validator('video_host', mode='after', check_fields=True)
    def validate_video_host(cls, var: IPv4Address, values: ValidationInfo) -> str:
        """Set `video_host` to local IP address if `ip_hosted` flag is set to True.

        Args:
            var: Variable value of `video_host`
            values: Values of all object.

        Returns:
            str:
            Local IP address as a string.
        """
        if values.data.get('ip_hosted') and str(var) == socket.gethostbyname("localhost"):
            return ip_address()


class FileIO(BaseModel):
    """Loads all the files' path required/created.

    >>> FileIO

    """

    name: str = "index.html"
    list_files: str = "list_files.html"


class Settings(BaseModel):
    """Creates a class for the hosts and chunk size of the video.

    >>> Settings

    """

    HOSTS: list = []
    CHUNK_SIZE: PositiveInt = 1024 * 1024
    VAULT: str = "stream"  # Use a masked location to hide the real path in the UI


env = EnvConfig()
fileio = FileIO()
settings = Settings()

if not os.listdir(env.video_source):
    raise FileNotFoundError(f"no files found in {env.video_source!r}")
env.video_host = str(env.video_host)
