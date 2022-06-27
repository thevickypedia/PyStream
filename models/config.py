import socket

from pydantic import Field, PositiveInt, BaseSettings
from typing import AnyStr


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    video_title: AnyStr = Field(default="Video Streaming via FastAPI", env='VIDEO_TITLE')
    video_host: str = Field(default=socket.gethostbyname('localhost'), env='VIDEO_HOST')
    video_port: PositiveInt = Field(default=8000, env='VIDEO_PORT')

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        env_file = ".env"


env = EnvConfig()

if isinstance(env.video_title, bytes):
    env.video_title = env.video_title.decode(encoding="utf-8")
