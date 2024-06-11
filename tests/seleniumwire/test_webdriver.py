from unittest.mock import Mock, patch

import pytest
from selenium.webdriver.common.proxy import ProxyType

from seleniumwire2.options import SeleniumWireOptions
from seleniumwire2.webdriver import Chrome, Firefox


@pytest.fixture(autouse=True)
def mock_backend():
    with patch("seleniumwire2.webdriver.backend") as mock_backend:
        mock_proxy = Mock()
        mock_proxy.address = ("127.0.0.1", 12345)
        mock_backend.create.return_value = mock_proxy
        yield mock_backend


@pytest.fixture(autouse=True)
def firefox_super_kwargs():
    with patch("seleniumwire2.webdriver._Firefox.__init__") as base_init:
        kwargs = {}
        base_init.side_effect = lambda *a, **k: kwargs.update(k)
        yield kwargs


@pytest.fixture(autouse=True)
def chrome_super_kwargs():
    with patch("seleniumwire2.webdriver._Chrome.__init__") as base_init:
        kwargs = {}
        base_init.side_effect = lambda *a, **k: kwargs.update(k)
        yield kwargs


class TestFirefoxWebDriver:
    def test_create_backend(self, mock_backend):
        firefox = Firefox()

        assert firefox.backend
        mock_backend.create.assert_called_once_with(SeleniumWireOptions())

    def test_allow_hijacking_localhost(self, firefox_super_kwargs):
        Firefox()

        firefox_options = firefox_super_kwargs["options"]
        assert firefox_options.preferences["network.proxy.allow_hijacking_localhost"] is True

    def test_accept_insecure_certs(self, firefox_super_kwargs):
        Firefox()

        firefox_options = firefox_super_kwargs["options"]
        assert firefox_options.accept_insecure_certs is True

    def test_no_proxy(self, firefox_super_kwargs):
        Firefox(seleniumwire_options=SeleniumWireOptions(exclude_hosts=["test_host"]))
        proxy = firefox_super_kwargs["options"].proxy
        assert proxy.noProxy == ["test_host"]

    def test_existing_capability(self, firefox_super_kwargs):
        Firefox(desired_capabilities={"test": "capability"})
        capabilties = firefox_super_kwargs["desired_capabilities"]
        assert capabilties["test"] == "capability"

    def test_no_auto_config_(self, firefox_super_kwargs):
        Firefox(seleniumwire_options=SeleniumWireOptions(auto_config=False), capabilities={"test": "capability"})
        assert (
            firefox_super_kwargs["options"].proxy is None
            or firefox_super_kwargs["options"].proxy.proxy_type == ProxyType.UNSPECIFIED
        )


class TestChromeWebDriver:
    def test_create_backend(self, mock_backend):
        chrome = Chrome()

        assert chrome.backend
        mock_backend.create.assert_called_once_with(SeleniumWireOptions())

    def test_proxy_bypass_list(self, chrome_super_kwargs):
        Chrome()

        chrome_options = chrome_super_kwargs["options"]
        assert "--proxy-bypass-list=<-loopback>" in chrome_options.arguments

    def test_accept_insecure_certs(self, chrome_super_kwargs):
        Chrome()

        chrome_options = chrome_super_kwargs["options"]
        assert "acceptInsecureCerts" in chrome_options.capabilities

    def test_set_proxy_config(self, chrome_super_kwargs):
        Chrome()

        options = chrome_super_kwargs["options"]

        assert options.capabilities["proxy"]["proxyType"] == "manual"
        assert options.capabilities["proxy"]["httpProxy"] == "127.0.0.1:12345"
        assert options.capabilities["proxy"]["sslProxy"] == "127.0.0.1:12345"
        assert "noProxy" not in options.capabilities["proxy"]
        assert options.capabilities["acceptInsecureCerts"] is True

    def test_no_proxy(self, chrome_super_kwargs):
        Chrome(seleniumwire_options=SeleniumWireOptions(exclude_hosts=["test_host"]))

        options = chrome_super_kwargs["options"]

        assert options.capabilities["proxy"]["noProxy"] == ["test_host"]

    def test_existing_capability(self, chrome_super_kwargs):
        Chrome(desired_capabilities={"test": "capability"})

        capabilties = chrome_super_kwargs["desired_capabilities"]

        assert capabilties["test"] == "capability"

    def test_no_auto_config(self, chrome_super_kwargs):
        Chrome(seleniumwire_options=SeleniumWireOptions(auto_config=False), capabilities={"test": "capability"})

        assert "proxy" not in chrome_super_kwargs["options"].capabilities
