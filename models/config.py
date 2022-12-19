import os
import socket

from pydantic import (BaseSettings, DirectoryPath, Field, HttpUrl,
                      IPvAnyAddress, PositiveInt)


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    username: str = Field(default=..., env="USERNAME")
    password: str = Field(..., env="PASSWORD")

    video_title: str = Field(default="Video Streaming via FastAPI", env="VIDEO_TITLE")
    video_host: IPvAnyAddress = Field(default=socket.gethostbyname("localhost"), env="VIDEO_HOST")
    video_source: DirectoryPath = Field(default="source", env="VIDEO_SOURCE")
    video_port: PositiveInt = Field(default=8000, env="VIDEO_PORT")
    website: HttpUrl = Field(default="https://vigneshrao.com", env="WEBSITE")

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
    templates: DirectoryPath = os.path.join(os.getcwd(), "templates")


class Settings(BaseSettings):
    """Creates a class for the hosts and chunk size of the video.

    >>> Settings

    """

    HOSTS: list = []
    CHUNK_SIZE: PositiveInt = 1024 * 1024


env = EnvConfig()
fileio = FileIO()
settings = Settings()

env.website = env.website.lstrip(f"{env.website.scheme}://")
env.video_host = str(env.video_host)
