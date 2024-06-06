import functools
from unittest import TestCase
from unittest.mock import call, patch

from seleniumwire.options import ProxyConfig, SeleniumWireOptions
from seleniumwire.server import MitmProxy


class MitmProxyTest(TestCase):

    base_options_update = functools.partial(
        call,
        confdir="/some/dir",
        listen_host="somehost",
        listen_port=12345,
        ssl_insecure=True,
    )

    def test_creates_storage(self):
        proxy = MitmProxy(SeleniumWireOptions("somehost", 12345, request_storage_base_dir="/some/dir"))

        self.assertEqual(self.mock_storage.create.return_value, proxy.storage)
        self.mock_storage.create.assert_called_once_with(memory_only=False, base_dir="/some/dir", maxsize=None)

    def test_creates_in_memory_storage(self):
        proxy = MitmProxy(
            SeleniumWireOptions(
                "somehost",
                12345,
                request_storage_base_dir="/some/dir",
                request_storage="memory",
                request_storage_max_size=10,
            )
        )

        self.assertEqual(self.mock_storage.create.return_value, proxy.storage)
        self.mock_storage.create.assert_called_once_with(memory_only=True, base_dir="/some/dir", maxsize=10)

    def test_extracts_cert(self):
        self.mock_storage.create.return_value.home_dir = "/some/dir/.seleniumwire"
        MitmProxy(SeleniumWireOptions("somehost", 12345))

        self.mock_extract_cert_and_key.assert_called_once_with(
            "/some/dir/.seleniumwire", cert_path=None, key_path=None
        )

    def test_creates_master(self):
        self.mock_get_mitm_upstream_proxy_args.return_value = {"mock": "proxy"}
        self.mock_storage.create.return_value.home_dir = "/some/dir/.seleniumwire"
        proxy_conf = ProxyConfig(http="http://proxyserver:8080")
        proxy = MitmProxy(SeleniumWireOptions("somehost", 12345, upstream_proxy=proxy_conf))
        self.assertEqual(self.mock_master.return_value, proxy.master)
        self.mock_options.assert_called_once()
        self.mock_options.return_value.update.assert_has_calls(
            [
                self.base_options_update(
                    confdir="/some/dir/.seleniumwire",
                )
            ]
        )
        self.mock_master.return_value.addons.add.assert_has_calls(
            [call(), call(self.mock_logger.return_value), call(self.mock_handler.return_value)]
        )
        self.mock_addons.default_addons.assert_called_once_with()
        self.mock_handler.assert_called_once_with(proxy)
        self.mock_get_mitm_upstream_proxy_args.assert_called_once_with(proxy_conf)

    def test_update_mitmproxy_options(self):
        MitmProxy(SeleniumWireOptions("somehost", 12345, mitm_options={"test": "foobar"}))

        self.mock_options.return_value.update.assert_has_calls(
            [
                self.base_options_update(
                    test="foobar",
                ),
            ]
        )

    def test_disable_capture(self):
        proxy = MitmProxy(SeleniumWireOptions("somehost", 12345, disable_capture=True))
        self.assertEqual(["$^"], proxy.scopes)

    def test_new_event_loop(self):
        proxy = MitmProxy(SeleniumWireOptions("somehost", 12345))

        self.assertEqual(self.mock_asyncio.new_event_loop.return_value, proxy._event_loop)
        self.mock_asyncio.new_event_loop.assert_called_once_with()

    def test_shutdown(self):
        proxy = MitmProxy(SeleniumWireOptions("somehost", 12345))

        proxy.shutdown()

        self.mock_master.return_value.shutdown.assert_called_once_with()
        self.mock_storage.create.return_value.cleanup.assert_called_once_with()

    def test_verify_ssl(self):
        MitmProxy(SeleniumWireOptions("somehost", 12345, verify_ssl=True))

        self.mock_options.return_value.update.assert_has_calls(
            [
                self.base_options_update(
                    ssl_insecure=False,
                ),
            ]
        )

    def setUp(self):
        patcher = patch("seleniumwire.server.storage")
        self.mock_storage = patcher.start()
        self.mock_storage.create.return_value.home_dir = "/some/dir"
        self.addCleanup(patcher.stop)

        patcher = patch("seleniumwire.server.Options")
        self.mock_options = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("seleniumwire.server.Master")
        self.mock_master = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("seleniumwire.server.SendToLogger")
        self.mock_logger = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("seleniumwire.server.addons")
        self.mock_addons = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("seleniumwire.server.InterceptRequestHandler")
        self.mock_handler = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("seleniumwire.server.asyncio")
        self.mock_asyncio = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("seleniumwire.server.extract_cert_and_key")
        self.mock_extract_cert_and_key = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("seleniumwire.server.get_mitm_upstream_proxy_args")
        self.mock_get_mitm_upstream_proxy_args = patcher.start()
        self.addCleanup(patcher.stop)
