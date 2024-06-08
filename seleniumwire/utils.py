import logging
import os
from collections import namedtuple
from typing import Optional
from urllib.request import _parse_proxy as _urllib_parse_proxy  # type: ignore[attr-defined]

from mitmproxy.net import encoding as decoder

from seleniumwire.options import ProxyConfig

log = logging.getLogger(__name__)

MITM_MODE = "mode"
MITM_UPSTREAM_AUTH = "upstream_auth"


def _parse_proxy(url: Optional[str]):
    if url is None:
        return None
    ProxyConf = namedtuple("ProxyConf", "scheme username password hostport")
    return ProxyConf(*_urllib_parse_proxy(url))


def get_mitm_upstream_proxy_args(upstream_proxy: Optional[ProxyConfig]) -> dict:
    """Build the arguments needed to pass an upstream proxy to mitmproxy.

    Args:
        proxy_config: The upstream proxy config parsed out of the Selenium Wire options.
    Returns: A dictionary of arguments suitable for passing to mitmproxy.
    """

    if upstream_proxy is None or (upstream_proxy.http is None and upstream_proxy.https is None):
        upstream_proxy = ProxyConfig(http=os.getenv("HTTP_PROXY"), https=os.getenv("HTTPS_PROXY"))

    http_proxy = _parse_proxy(upstream_proxy.http)
    https_proxy = _parse_proxy(upstream_proxy.https)

    if http_proxy and https_proxy:
        if http_proxy.hostport != https_proxy.hostport:  # noqa
            # We only support a single upstream proxy server
            raise ValueError("Different settings for http and https proxy servers not supported")
        conf = https_proxy
    elif http_proxy:
        conf = http_proxy
    elif https_proxy:
        conf = https_proxy
    else:
        return {MITM_MODE: ["regular"]}

    args: dict = {}
    scheme, username, password, hostport = conf
    args[MITM_MODE] = [f"upstream:{scheme}://{hostport}"]
    args[MITM_UPSTREAM_AUTH] = None
    if username:
        args[MITM_UPSTREAM_AUTH] = f"{username}:{password}"

    return args


def urlsafe_address(address):
    """Make an address safe to use in a URL.

    Args:
        address: A tuple of address information.
    Returns:
        A 2-tuple of url-safe (address, port)
    """
    addr, port, *rest = address

    if rest:
        # An IPv6 address needs to be surrounded by square brackets
        addr = f"[{addr}]"

    return addr, port


def decode(data: bytes, encoding: str) -> str | bytes:
    """Attempt to decode data based on the supplied encoding.

    If decoding fails a ValueError is raised.

    Args:
        data: The encoded data.
        encoding: The encoding type.
    Returns: The decoded data.
    Raises: ValueError if the data could not be decoded.
    """
    return decoder.decode(data, encoding)
