import gzip
import zlib
from io import BytesIO
from unittest import TestCase

from seleniumwire2.options import ProxyConfig
from seleniumwire2.utils import decode, get_mitm_upstream_proxy_args, urlsafe_address


class BuildProxyArgsTest(TestCase):
    def test_args_both_schemes(self):
        args = get_mitm_upstream_proxy_args(
            ProxyConfig(http="http://proxyserver:8080", https="https://proxyserver:8080")
        )
        self.assertEqual(args, {"mode": ["upstream:https://proxyserver:8080"], "upstream_auth": None})

    def test_args_single_scheme(self):
        args = get_mitm_upstream_proxy_args(ProxyConfig(http="http://proxyserver:8080"))

        self.assertEqual(args, {"mode": ["upstream:http://proxyserver:8080"], "upstream_auth": None})

    def test_different_schemes(self):
        with self.assertRaises(ValueError):
            get_mitm_upstream_proxy_args(
                ProxyConfig(http="http://proxyserver1:8080", https="https://proxyserver2:8080")
            )

    def test_args_auth(self):
        options = {
            "proxy": {
                "https": "https://user:pass@proxyserver:8080",
            },
        }

        args = get_mitm_upstream_proxy_args(ProxyConfig(https="https://user:pass@proxyserver:8080"))

        self.assertEqual(args, {"mode": ["upstream:https://proxyserver:8080"], "upstream_auth": "user:pass"})

    def test_args_auth_empty_password(self):
        args = get_mitm_upstream_proxy_args(ProxyConfig(https="https://user:@proxyserver:8080"))

        self.assertEqual(args, {"mode": ["upstream:https://proxyserver:8080"], "upstream_auth": "user:"})


def test_urlsafe_address_ipv4():
    assert urlsafe_address(("192.168.0.1", 9999)) == ("192.168.0.1", 9999)


def test_urlsafe_address_ipv6():
    assert urlsafe_address(("::ffff:127.0.0.1", 9999, 0, 0)) == ("[::ffff:127.0.0.1]", 9999)


class DecodeTest(TestCase):
    def test_decode_gzip_data(self):
        data = b"test response body"
        compressed = BytesIO()

        with gzip.GzipFile(fileobj=compressed, mode="wb") as f:
            f.write(data)

        self.assertEqual(decode(compressed.getvalue(), "gzip"), data)

    def test_decode_zlib_data(self):
        data = b"test response body"
        compressed = zlib.compress(data)

        self.assertEqual(decode(compressed, "deflate"), data)

    def test_decode_error(self):
        data = b"test response body"

        with self.assertRaises(ValueError):
            self.assertEqual(decode(data, "gzip"), data)
