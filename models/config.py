import os
import socket

from pydantic import (BaseSettings, DirectoryPath, Field, HttpUrl,
                      IPvAnyAddress, PositiveInt)


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    username: str = Field(default=..., env="USERNAME")
    password: str = Field(default=..., env="PASSWORD")

    video_host: IPvAnyAddress = Field(default=socket.gethostbyname("localhost"), env="VIDEO_HOST")
    video_source: DirectoryPath = Field(default="source", env="VIDEO_SOURCE")
    video_port: PositiveInt = Field(default=8000, env="VIDEO_PORT")
    website: HttpUrl = Field(default=None, env="WEBSITE")
    workers: int = Field(default=1, le=int(os.cpu_count() / 2), ge=1, env="WORKERS")

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
if env.website:
    env.website = env.website.lstrip(f"{env.website.scheme}://")
env.video_host = str(env.video_host)
