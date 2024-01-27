import base64
import binascii
import hashlib
import string
from typing import Any

UNICODE_PREFIX = (
        base64.b64decode(b"XA==").decode(encoding="ascii")
        + string.ascii_letters[20]
        + string.digits[:1] * 2
)


async def calculate_hash(value: Any) -> str:
    """Generate hash value for the given payload."""
    return hashlib.sha512(bytes(value, "utf-8")).hexdigest()


async def base64_encode(value: Any) -> str:
    """Base64 encode the given payload."""
    encoded_bytes = base64.b64encode(value.encode("utf-8"))
    return encoded_bytes.decode("utf-8")


async def base64_decode(value: Any) -> str:
    """Base64 decode the given payload."""
    return base64.b64decode(value).decode("utf-8")


async def hex_decode(value: Any) -> str:
    """Convert hex value to a string."""
    return bytes(value, "utf-8").decode(encoding="unicode_escape")


async def hex_encode(value: str):
    """Convert string value to hex."""
    return UNICODE_PREFIX + UNICODE_PREFIX.join(
        binascii.hexlify(data=value.encode(encoding="utf-8"), sep="-")
        .decode(encoding="utf-8")
        .split(sep="-")
    )
