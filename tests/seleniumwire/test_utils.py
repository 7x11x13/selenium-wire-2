import gzip
import zlib
from io import BytesIO
from pathlib import Path
from unittest import TestCase
from unittest.mock import call, mock_open, patch

from seleniumwire.options import ProxyConfig
from seleniumwire.utils import decode, extract_cert_and_key, get_mitm_upstream_proxy_args, urlsafe_address


class BuildProxyArgsTest(TestCase):
    def test_args_both_schemes(self):
        args = get_mitm_upstream_proxy_args(
            ProxyConfig(http="http://proxyserver:8080", https="https://proxyserver:8080")
        )
        self.assertEqual(args, {"mode": "upstream:https://proxyserver:8080"})

    def test_args_single_scheme(self):
        args = get_mitm_upstream_proxy_args(ProxyConfig(http="http://proxyserver:8080"))

        self.assertEqual(args, {"mode": "upstream:http://proxyserver:8080"})

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

        self.assertEqual(args, {"mode": "upstream:https://proxyserver:8080", "upstream_auth": "user:pass"})

    def test_args_auth_empty_password(self):
        args = get_mitm_upstream_proxy_args(ProxyConfig(https="https://user:@proxyserver:8080"))

        self.assertEqual(args, {"mode": "upstream:https://proxyserver:8080", "upstream_auth": "user:"})


class ExtractCertTest(TestCase):

    @patch("seleniumwire.utils.os")
    @patch("seleniumwire.utils.pkgutil")
    @patch("seleniumwire.utils.Path")
    def test_extract_cert_and_key(self, mock_path, mock_pkgutil, mock_os):
        mock_path.return_value.exists.return_value = False
        mock_pkgutil.get_data.side_effect = (b"cert_data", b"key_data")
        m_open = mock_open()

        with patch("seleniumwire.utils.open", m_open):
            extract_cert_and_key(Path("some", "path"))

        mock_os.makedirs.assert_called_once_with(Path("some", "path"), exist_ok=True)
        mock_path.assert_called_once_with(Path("some", "path"), "seleniumwire-ca.pem")
        mock_pkgutil.get_data.assert_has_calls([call("seleniumwire", "ca.crt"), call("seleniumwire", "ca.key")])
        m_open.assert_called_once_with(mock_path.return_value, "wb")
        m_open.return_value.write.assert_called_once_with(b"cert_data\nkey_data")

    @patch("seleniumwire.utils.os")
    @patch("seleniumwire.utils.pkgutil")
    @patch("seleniumwire.utils.Path")
    def test_extract_user_supplied_cert_and_key(self, mock_path, mock_pkgutil, mock_os):
        mock_path.return_value.exists.return_value = False
        mock_path.return_value.read_bytes.side_effect = (b"cert_data", b"key_data")
        m_open = mock_open()

        with patch("seleniumwire.utils.open", m_open):
            extract_cert_and_key(Path("some", "path"), cert_path="cert_path", key_path="key_path")

        mock_os.makedirs.assert_called_once_with(Path("some", "path"), exist_ok=True)
        mock_path.assert_has_calls(
            [
                call(Path("some", "path"), "seleniumwire-ca.pem"),
                call().exists(),
                call("cert_path"),
                call().read_bytes(),
                call("key_path"),
                call().read_bytes(),
            ]
        )
        assert mock_pkgutil.get_data.call_count == 0
        m_open.assert_called_once_with(mock_path.return_value, "wb")
        m_open.return_value.write.assert_called_once_with(b"cert_data\nkey_data")

    @patch("seleniumwire.utils.Path")
    def test_extract_user_supplied_cert_missing_key(self, mock_path):
        mock_path.return_value.exists.return_value = False

        with patch("seleniumwire.utils.os"), self.assertRaises(ValueError):
            extract_cert_and_key(Path("some", "path"), cert_path="cert_path")

    @patch("seleniumwire.utils.Path")
    def test_extract_cert_and_key_exists(self, mock_path):
        mock_path.return_value.exists.return_value = True
        m_open = mock_open()

        with patch("seleniumwire.utils.os"), patch("seleniumwire.utils.open", m_open):
            extract_cert_and_key(Path("some", "path"))

        m_open.assert_not_called()

    @patch("seleniumwire.utils.Path")
    def test_extract_cert_and_key_no_check(self, mock_path):
        mock_path.return_value.exists.return_value = True
        m_open = mock_open()

        with patch("seleniumwire.utils.os"), patch("seleniumwire.utils.open", m_open):
            extract_cert_and_key(Path("some", "path"), check_exists=False)

        m_open.assert_called_once()


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
