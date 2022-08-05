import base64
import os
import socket
import uuid
from pathlib import Path
from typing import Callable, Generator, Union

from pydantic import (BaseSettings, DirectoryPath, Field, FilePath, HttpUrl,
                      IPvAnyAddress, PositiveInt)
from pydantic.validators import path_validator


class PotentialPath(Path):
    """Custom class for ``PotentialPath`` when the path doesn't exist but the parent does.

    >>> PotentialPath

    """

    @classmethod
    def __get_validators__(cls) -> Union[Callable, Generator]:
        """Override built-in.

        Returns:
            CallableGenerator:
        """
        yield path_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Path) -> Path:
        """Validator method.

        Args:
            value: Path to be validated.

        Returns:
            Path:
            Validated path if it doesn't exist.

        Raises:
            ValueError:
            If path actually exists.
        """
        if value.exists():
            raise ValueError(f'file or directory at path "{value}" exists')

        return value


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    username: str = Field(default=..., env="USERNAME")
    password: str = Field(..., env="PASSWORD")

    video_title: str = Field(default="Video Streaming via FastAPI", env="VIDEO_TITLE")
    video_host: IPvAnyAddress = Field(default=socket.gethostbyname("localhost"), env="VIDEO_HOST")
    video_file: FilePath = Field(default=Path(os.path.join(os.getcwd(), "video.mp4")), env="VIDEO_FILE")
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
    templates: DirectoryPath = os.path.join(os.getcwd(), "templates")
    html: PotentialPath = os.path.join(templates, name)


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

env.website = env.website.lstrip(f"{env.website.scheme}://")
env.video_host = str(env.video_host)
