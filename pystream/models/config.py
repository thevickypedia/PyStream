import json
import os
import pathlib
import socket
from ipaddress import IPv4Address
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from cryptography.fernet import Fernet
from pydantic import (BaseModel, DirectoryPath, Field, PositiveInt, SecretStr,
                      field_validator)
from pydantic_settings import BaseSettings

template_storage = os.path.join(pathlib.Path(__file__).parent.parent, "templates")


def as_dict(pairs: List[Tuple[str, str]]) -> Dict[str, str]:
    """Custom decoder for ``json.loads`` passed via ``object_pairs_hook`` raising error on duplicate keys.

    Args:
        pairs: Takes the ordered list of pairs as an argument.

    Returns:
        Dict[str, str]:
        A dictionary of key-value pairs.
    """
    dictionary = {}
    for key, value in pairs:
        if key in dictionary:
            raise ValueError(f"Duplicate key: {key!r}")
        else:
            dictionary[key.strip()] = value.strip()
    return dictionary


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    # type hint is set to Any to catch duplicate keys in env files, python's default behavior is to overwrite the values
    authorization: Any
    video_source: DirectoryPath

    video_host: IPv4Address = socket.gethostbyname("localhost")
    video_port: PositiveInt = 8000
    session_duration: int = Field(default=3_600, ge=300)  # Defaults to 1 hour, should at least be 5 minutes
    file_formats: Sequence[str] = (".mov", ".mp4")

    workers: int = Field(1, le=os.cpu_count(), ge=1, env="WORKERS")
    website: Union[List[str], None] = []
    auto_thumbnail: bool = True

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        env_file = os.environ.get("env_file") or os.environ.get("ENV_FILE") or ".env"
        extra = "ignore"  # Ignores additional environment variables present in env files
        hide_input_in_errors = True  # Avoids revealing sensitive information in validation error messages

    # noinspection PyMethodParameters
    @field_validator("authorization", mode='before', check_fields=False)
    def parse_authorization(cls, value: Any) -> Dict[str, SecretStr]:
        """Validates the authorization parameter and converts plain text passwords into ``SecretStr`` objects."""
        if isinstance(value, dict):
            val = value
        else:
            val = json.loads(value, object_pairs_hook=as_dict)
            if not isinstance(val, dict):
                raise ValueError("input should be a valid dictionary with username as key and password as value")
        r = {}
        for k, v_ in val.items():
            v = SecretStr(v_)
            if len(k) < 4:
                raise ValueError(f"[{k}: {v}] username should be at least 4 or more characters, received {len(k)}")
            if len(v) < 8:
                raise ValueError(f"[{k}: {v}] password should be at least 8 or more characters, received {len(v_)}")
            r[k] = v
        return r

    # noinspection PyMethodParameters
    @field_validator("video_host", mode='after', check_fields=True)
    def parse_video_host(cls, value: IPv4Address) -> str:
        """Returns the string notion of IPv4Address object."""
        return str(value)

    # noinspection PyMethodParameters
    @field_validator("website", mode='before', check_fields=True)
    def parse_website(cls, value: str) -> List[str]:
        """Evaluates the string as a list and returns the list of strings."""
        if not value:
            return []
        val = eval(value)
        if isinstance(val, list):
            return val
        raise ValueError(
            f"Invalid value for website, must be a list of strings, got {type(val)}"
        )


class FileIO(BaseModel):
    """Loads all the files' path required/created.

    >>> FileIO

    """

    index: str = "index.html"
    listing: str = "list.html"
    landing: str = "land.html"


class Static(BaseModel):
    """Object to store static values.

    >>> Static

    """

    track: str = "track"
    stream: str = "stream"
    preview: str = "preview"
    query_param: str = "file"
    home_endpoint: str = "/home"
    login_endpoint: str = "/login"
    logout_endpoint: str = "/logout"
    streaming_endpoint: str = "/video"
    chunk_size: PositiveInt = 1024 * 1024
    deletions: Set[pathlib.PosixPath] = set()
    cipher_suite: Fernet = Fernet(Fernet.generate_key())

    class Config:
        """Static configuration."""

        arbitrary_types_allowed = True


class Session(BaseModel):
    """Object to store session information.

    >>> Session

    """

    info: dict = {}
    invalid: dict = {}
    mapping: dict = {}


class WebToken(BaseModel):
    """Object to store and validate the symmetric ecrypted payload.

    >>> WebToken

    """

    # Use a minimum length so empty tokens cannot get passed when assigning default value for a dict value
    token: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    timestamp: int = Field(..., gt=0)


class RedirectException(Exception):
    """Custom ``RedirectException`` raised within the API since HTTPException doesn't support returning HTML content.

    >>> RedirectException

    See Also:
        - RedirectException allows the API to redirect on demand in cases where returning is not a solution.
        - There are alternatives to raise HTML content as an exception but none work with our use-case with JavaScript.
        - This way of exception handling comes handy for many unexpected scenarios.

    References:
        https://fastapi.tiangolo.com/tutorial/handling-errors/#install-custom-exception-handlers
    """

    def __init__(self,
                 location: str,
                 detail: Optional[str] = ""):
        """Instantiates the ``RedirectException`` object with the required parameters.

        Args:
            location: Location for redirect.
            detail: Reason for redirect.
        """
        self.location = location
        self.detail = detail


env = EnvConfig
fileio = FileIO()
static = Static()
session = Session()
