import base64
import os
import socket
import uuid
from typing import Union

from pydantic import BaseSettings, DirectoryPath, Field, FilePath, PositiveInt


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    username: str = Field(default=..., env="USERNAME")
    password: str = Field(..., env="PASSWORD")

    video_file: str = Field(default="video.mp4", env="VIDEO_FILE")
    video_title: str = Field(default="Video Streaming via FastAPI", env="VIDEO_TITLE")
    video_host: str = Field(default=socket.gethostbyname("localhost"), env="VIDEO_HOST")
    video_port: PositiveInt = Field(default=8000, env="VIDEO_PORT")
    website: str = Field(default="vigneshrao.com", env="WEBSITE")
    auth_timeout: PositiveInt = Field(default=900, env="AUTH_TIMEOUT")

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        env_file = ".env"


class FileIO(BaseSettings):
    """Loads all the files' path required/created.

    >>> FileIO

    """

    name: str = "index.html"
    templates: DirectoryPath = os.path.join(os.getcwd(), "templates")
    html: Union[FilePath, str] = os.path.join(templates, name)


class Settings(BaseSettings):
    """Creates a class for the hosts and chunk size of the video.

    >>> Settings

    """

    HOSTS: list = []
    CHUNK_SIZE: PositiveInt = 1024 * 1024
    SESSION_TOKEN: Union[uuid.UUID, str] = base64.urlsafe_b64encode(uuid.uuid1().bytes).rstrip(b'=').decode('ascii')


env = EnvConfig()
fileio = FileIO()
settings = Settings()
