import os
import socket
from ipaddress import IPv4Address
from typing import Union

from pydantic import BaseModel, DirectoryPath, Field, HttpUrl, PositiveInt
from pydantic_settings import BaseSettings


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    username: str
    password: str
    video_source: DirectoryPath

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
