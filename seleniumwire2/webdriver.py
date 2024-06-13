from typing import Protocol, TypedDict

from selenium.webdriver import Chrome as _Chrome
from selenium.webdriver import ChromeOptions
from selenium.webdriver import Edge as _Edge
from selenium.webdriver import EdgeOptions
from selenium.webdriver import Firefox as _Firefox
from selenium.webdriver import FirefoxOptions
from selenium.webdriver import Remote as _Remote
from selenium.webdriver import Safari as _Safari
from selenium.webdriver import SafariOptions
from selenium.webdriver.common.options import BaseOptions
from selenium.webdriver.common.proxy import Proxy

from seleniumwire2 import backend, utils
from seleniumwire2.inspect import InspectRequestsMixin
from seleniumwire2.options import ProxyConfig, SeleniumWireOptions
from seleniumwire2.server import MitmProxy


class Capabilities(TypedDict):
    proxy: dict
    acceptInsecureCerts: bool


class WebDriverProtocol(Protocol):
    backend: MitmProxy

    def refresh(self) -> None: ...
    def quit(self) -> None: ...


def _set_options(options: BaseOptions, capabilities: Capabilities):
    if isinstance(options, ChromeOptions) or isinstance(options, EdgeOptions):
        # Prevent Chrome from bypassing the Selenium Wire proxy
        # for localhost addresses.
        options.add_argument("--proxy-bypass-list=<-loopback>")
        for key, value in capabilities.items():
            options.set_capability(key, value)
    elif isinstance(options, FirefoxOptions):
        # Prevent Firefox from bypassing the Selenium Wire proxy
        # for localhost addresses.
        options.set_preference("network.proxy.allow_hijacking_localhost", True)
        try:
            options.accept_insecure_certs = capabilities["acceptInsecureCerts"]
        except KeyError:
            pass
        # From Selenium v4.0.0 the browser's proxy settings can no longer
        # be passed using desired capabilities and we must use the options
        # object instead.
        try:
            proxy = Proxy()
            proxy.http_proxy = capabilities["proxy"]["httpProxy"]
            proxy.ssl_proxy = capabilities["proxy"]["sslProxy"]
            try:
                proxy.no_proxy = capabilities["proxy"]["noProxy"]
            except KeyError:
                pass
        except KeyError:
            pass
        options.proxy = proxy
    elif isinstance(options, SafariOptions):
        try:
            options.accept_insecure_certs = capabilities["acceptInsecureCerts"]
        except KeyError:
            pass
        # Safari does not support automatic proxy configuration through the
        # DesiredCapabilities API, and thus has to be configured manually.
        # Whatever port number is chosen for that manual configuration has to
        # be passed in the options.
    else:
        raise ValueError(f"Unsupported options type: {options.__class__.__name__}")


class DriverCommonMixin:
    """Attributes common to all webdriver types."""

    def _setup_backend(
        self: WebDriverProtocol, seleniumwire_options: SeleniumWireOptions, webdriver_options: BaseOptions
    ):
        """Create the backend proxy server and return its configuration
        in a dictionary.
        """
        self.backend = backend.create(
            seleniumwire_options,
        )

        if seleniumwire_options.auto_config:
            addr, port = utils.urlsafe_address(self.backend.address)

            capabilities: Capabilities = {
                "proxy": {
                    "proxyType": "manual",
                    "httpProxy": "{}:{}".format(addr, port),
                    "sslProxy": "{}:{}".format(addr, port),
                },
                "acceptInsecureCerts": not seleniumwire_options.verify_ssl,
            }

            if seleniumwire_options.exclude_hosts:
                # Only pass noProxy when we have a value to pass
                capabilities["proxy"]["noProxy"] = seleniumwire_options.exclude_hosts
        else:
            capabilities = webdriver_options.to_capabilities()

        _set_options(webdriver_options, capabilities)

    def quit(self: WebDriverProtocol):
        """Shutdown Selenium Wire and then quit the webdriver."""
        self.backend.shutdown()
        super().quit()  # type: ignore

    def remove_upstream_proxy(self: WebDriverProtocol):
        """Remove upstream proxy"""
        self.backend.update_server_mode(None)
        self.refresh()

    def set_upstream_proxy(self: WebDriverProtocol, proxy_config: ProxyConfig):
        """Change the upstream proxy configuration.

        webdriver.set_upstream_proxy(
            ProxyConfig(
                https='https://user:pass@server:port'
            )
        )

        Args:
            proxy_config: The proxy configuration.
        """
        self.backend.update_server_mode(proxy_config)
        self.refresh()


class Firefox(InspectRequestsMixin, DriverCommonMixin, _Firefox):
    """Extend the Firefox webdriver to provide additional methods for inspecting requests."""

    def __init__(self, *args, seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(), **kwargs):
        """Initialise a new Firefox WebDriver instance."""
        options = kwargs.get("options", FirefoxOptions())
        kwargs["options"] = options
        self._setup_backend(seleniumwire_options, options)
        super().__init__(*args, **kwargs)


class Chrome(InspectRequestsMixin, DriverCommonMixin, _Chrome):
    """Extend the Chrome webdriver to provide additional methods for inspecting requests."""

    def __init__(self, *args, seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(), **kwargs):
        """Initialise a new Chrome WebDriver instance."""
        options = kwargs.get("options", ChromeOptions())
        kwargs["options"] = options
        self._setup_backend(seleniumwire_options, options)
        super().__init__(*args, **kwargs)


class Safari(InspectRequestsMixin, DriverCommonMixin, _Safari):
    """Extend the Safari webdriver to provide additional methods for inspecting requests."""

    def __init__(self, *args, seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(), **kwargs):
        """Initialise a new Safari WebDriver instance."""
        options = kwargs.get("options", SafariOptions())
        kwargs["options"] = options
        self._setup_backend(seleniumwire_options, options)
        super().__init__(*args, **kwargs)


class Edge(InspectRequestsMixin, DriverCommonMixin, _Edge):
    """Extend the Edge webdriver to provide additional methods for inspecting requests."""

    def __init__(self, *args, seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(), **kwargs):
        """Initialise a new Edge WebDriver instance."""
        options = kwargs.get("options", EdgeOptions())
        kwargs["options"] = options
        self._setup_backend(seleniumwire_options, options)
        super().__init__(*args, **kwargs)


class Remote(InspectRequestsMixin, DriverCommonMixin, _Remote):
    """Extend the Remote webdriver to provide additional methods for inspecting requests."""

    def __init__(self, *args, seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(), **kwargs):
        """Initialise a new Remote WebDriver instance."""
        try:
            options = kwargs["options"]
        except KeyError:
            raise ValueError("Remote driver must be initialized with 'options' kwarg")
        self._setup_backend(seleniumwire_options, options)
        super().__init__(*args, **kwargs)
