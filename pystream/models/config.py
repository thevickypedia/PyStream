import os
import socket
from ipaddress import IPv4Address
from typing import Sequence, Union

from pydantic import (BaseModel, DirectoryPath, Field, HttpUrl, PositiveInt,
                      SecretStr, field_validator)
from pydantic_settings import BaseSettings


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    username: str
    password: SecretStr
    video_source: DirectoryPath

    video_host: IPv4Address = socket.gethostbyname("localhost")
    video_port: PositiveInt = 8000
    file_formats: Sequence[str] = (".mov", ".mp4")

    workers: int = Field(1, le=os.cpu_count(), ge=1, env="WORKERS")
    website: Union[HttpUrl, None] = None
    auto_thumbnail: bool = True

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        env_file = os.environ.get("env_file") or os.environ.get("ENV_FILE") or ".env"
        extra = "ignore"  # Ignores additional environment variables present in env files
        hide_input_in_errors = True  # Avoids revealing sensitive information in validation error messages

    # noinspection PyMethodParameters
    @field_validator("video_host", mode='after', check_fields=True)
    def parse_video_host(cls, value: IPv4Address) -> str:
        """Returns the string notion of IPv4Address object."""
        return str(value)


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

    vault: str = "stream"  # Use a masked location to hide real path in the URL (will still be visible in html though)
    preview: str = "preview"
    query_param: str = "file"
    index_endpoint: str = "/index"
    logout_endpoint: str = "/logout"
    streaming_endpoint: str = "/video"
    chunk_size: PositiveInt = 1024 * 1024


class Session(BaseModel):
    """Object to store session information.

    >>> Session

    """

    info: dict = {}


env = EnvConfig
fileio = FileIO()
static = Static()
session = Session()
