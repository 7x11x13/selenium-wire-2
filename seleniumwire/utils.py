import logging
import os
import pkgutil
from collections import namedtuple
from pathlib import Path
from typing import Optional
from urllib.request import _parse_proxy as _urllib_parse_proxy  # type: ignore[attr-defined]

from mitmproxy.net import encoding as decoder

from seleniumwire.options import ProxyConfig

log = logging.getLogger(__name__)

ROOT_CERT = "ca.crt"
ROOT_KEY = "ca.key"
COMBINED_CERT = "seleniumwire-ca.pem"

MITM_MODE = "mode"
MITM_UPSTREAM_AUTH = "upstream_auth"


def _parse_proxy(url: Optional[str]):
    if url is None:
        return None
    ProxyConf = namedtuple("ProxyConf", "scheme username password hostport")
    return ProxyConf(*_urllib_parse_proxy(url))


def get_mitm_upstream_proxy_args(upstream_proxy: Optional[ProxyConfig]) -> dict[str, str]:
    """Build the arguments needed to pass an upstream proxy to mitmproxy.

    Args:
        proxy_config: The upstream proxy config parsed out of the Selenium Wire options.
    Returns: A dictionary of arguments suitable for passing to mitmproxy.
    """

    if upstream_proxy is None:
        return {}

    http_proxy = _parse_proxy(upstream_proxy.http)
    https_proxy = _parse_proxy(upstream_proxy.https)

    conf = None
    if http_proxy and https_proxy:
        if http_proxy.hostport != https_proxy.hostport:  # noqa
            # We only support a single upstream proxy server
            raise ValueError("Different settings for http and https proxy servers not supported")
        conf = https_proxy
    elif http_proxy:
        conf = http_proxy
    elif https_proxy:
        conf = https_proxy

    args = {}

    if conf:
        scheme, username, password, hostport = conf

        args[MITM_MODE] = f"upstream:{scheme}://{hostport}"

        if username:
            args[MITM_UPSTREAM_AUTH] = f"{username}:{password}"

    return args


def extract_cert_and_key(dest_folder, cert_path=None, key_path=None, check_exists=True):
    """Extracts the root certificate and key and combines them into a
    single file called seleniumwire-ca.pem in the specified destination
    folder.

    Args:
        dest_folder: The destination folder that the combined certificate
            and key will be written to.
        cert_path: Optional path to the root certificate. When not supplied
            selenium wire's own root certificate will be used.
        key_path: Optional path to the private key. When not supplied
            selenium wire's own private key will be used. Note that the key
            must always be supplied when a certificate is supplied.
        check_exists: If True the combined file will not be overwritten
            if it already exists in the destination folder.
    """
    os.makedirs(dest_folder, exist_ok=True)
    combined_path = Path(dest_folder, COMBINED_CERT)
    if check_exists and combined_path.exists():
        return

    if cert_path is not None and key_path is not None:
        root_cert = Path(cert_path).read_bytes()
        root_key = Path(key_path).read_bytes()
    elif cert_path is not None or key_path is not None:
        raise ValueError("A certificate and key must both be supplied")
    else:
        root_cert = pkgutil.get_data(__package__, ROOT_CERT)
        root_key = pkgutil.get_data(__package__, ROOT_KEY)

    with open(combined_path, "wb") as f_out:
        f_out.write(root_cert + b"\n" + root_key)


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
