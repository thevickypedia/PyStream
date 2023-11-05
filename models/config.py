import os
import socket

from pydantic_settings import BaseSettings
from pydantic import (DirectoryPath, Field, HttpUrl,
                      IPvAnyAddress, PositiveInt)


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    username: str
    password: str

    video_port: PositiveInt = 8000
    website: HttpUrl | None = None
    ngrok_token: str | None = None
    video_source: DirectoryPath = "source"
    workers: int = Field(1, le=int(os.cpu_count() / 2), ge=1, env="WORKERS")
    video_host: IPvAnyAddress = socket.gethostbyname("localhost")

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        env_file = ".env"


class FileIO(BaseSettings):
    """Loads all the files' path required/created.

    >>> FileIO

    """

    name: str = "index.html"
    list_files: str = "list_files.html"


class Settings(BaseSettings):
    """Creates a class for the hosts and chunk size of the video.

    >>> Settings

    """

    HOSTS: list = []
    CHUNK_SIZE: PositiveInt = 1024 * 1024
    FAKE_DIR: str = "stream"


env = EnvConfig()
fileio = FileIO()
settings = Settings()

if not os.listdir(env.video_source):
    raise FileNotFoundError(f"no files found in {env.video_source!r}")
env.video_host = str(env.video_host)
