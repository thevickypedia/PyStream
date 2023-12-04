import socket
from ipaddress import IPv4Address

import requests


def get_local_ip() -> IPv4Address:
    """Uses simple check on network id to retrieve the local IP address.

    Returns:
        IPv4Address:
        Private IP address of host machine.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as socket_:
        socket_.connect(("8.8.8.8", 80))
        return IPv4Address(socket_.getsockname()[0])


def get_public_ip() -> IPv4Address:
    """Extract public IP address of the connection by making a request to external source.

    Returns:
        IPv4Address:
        Public IP address of host machine's connection.
    """
    return IPv4Address(requests.get('https://checkip.amazonaws.com').text.strip())
