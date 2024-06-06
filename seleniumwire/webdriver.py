from typing import Any

from selenium.webdriver import Chrome as _Chrome
from selenium.webdriver import ChromeOptions, DesiredCapabilities
from selenium.webdriver import Edge as _Edge
from selenium.webdriver import EdgeOptions
from selenium.webdriver import Firefox as _Firefox
from selenium.webdriver import FirefoxOptions
from selenium.webdriver import Remote as _Remote
from selenium.webdriver import Safari as _Safari
from selenium.webdriver.common.proxy import Proxy, ProxyType

from seleniumwire import backend, utils
from seleniumwire.inspect import InspectRequestsMixin
from seleniumwire.options import ProxyConfig, SeleniumWireOptions


class DriverCommonMixin:
    """Attributes common to all webdriver types."""

    def _setup_backend(self, seleniumwire_options: SeleniumWireOptions) -> dict[str, Any]:
        """Create the backend proxy server and return its configuration
        in a dictionary.
        """
        self.backend = backend.create(
            seleniumwire_options,
        )

        addr, port = utils.urlsafe_address(self.backend.address())

        config = {
            "proxy": {
                "proxyType": ProxyType.MANUAL,
                "httpProxy": "{}:{}".format(addr, port),
                "sslProxy": "{}:{}".format(addr, port),
            },
            "acceptInsecureCerts": True,
        }

        if seleniumwire_options.exclude_hosts:
            # Only pass noProxy when we have a value to pass
            config["proxy"]["noProxy"] = seleniumwire_options.exclude_hosts

        return config

    def quit(self):
        """Shutdown Selenium Wire and then quit the webdriver."""
        self.backend.shutdown()
        super().quit()

    # @property
    # def proxy(self) -> ProxyConfig:
    #     """Get the proxy configuration for the driver."""

    #     return self.backend.options.upstream_proxy

    #     conf = {}
    #     mode: str = self.backend.master.options.mode

    #     if mode and mode.startswith('upstream'):
    #         upstream = mode.split('upstream:')[1]
    #         scheme, *rest = upstream.split('://')

    #         auth = self.backend.master.options.upstream_auth

    #         if auth:
    #             conf[scheme] = f'{scheme}://{auth}@{rest[0]}'
    #         else:
    #             conf[scheme] = f'{scheme}://{rest[0]}'

    #     # no_proxy = self.backend.master.options.no_proxy

    #     # if no_proxy:
    #     #     conf['no_proxy'] = ','.join(no_proxy)

    #     # custom_auth = getattr(self.backend.master.options, 'upstream_custom_auth')

    #     # if custom_auth:
    #     #     conf['custom_authorization'] = custom_auth

    #     return conf

    def remove_upstream_proxy(self):
        """Remove upstream proxy"""
        options = self.backend.master.options
        options.update(
            **{
                utils.MITM_MODE: options.default(utils.MITM_MODE),
                utils.MITM_UPSTREAM_AUTH: options.default(utils.MITM_UPSTREAM_AUTH),
            }
        )

    def set_upstream_proxy(self, proxy_config: ProxyConfig):
        """Change the upstream proxy configuration.

        webdriver.set_upstream_proxy(
            ProxyConfig(
                https='https://user:pass@server:port'
            )
        )

        Args:
            proxy_config: The proxy configuration.
        """
        self.backend.master.options.update(**utils.get_mitm_upstream_proxy_args(proxy_config))


class Firefox(InspectRequestsMixin, DriverCommonMixin, _Firefox):
    """Extend the Firefox webdriver to provide additional methods for inspecting requests."""

    def __init__(self, *args, seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(), **kwargs):
        """Initialise a new Firefox WebDriver instance."""
        try:
            firefox_options = kwargs["options"]
        except KeyError:
            firefox_options = FirefoxOptions()
            kwargs["options"] = firefox_options

        # Prevent Firefox from bypassing the Selenium Wire proxy
        # for localhost addresses.
        firefox_options.set_preference("network.proxy.allow_hijacking_localhost", True)
        firefox_options.accept_insecure_certs = True

        config = self._setup_backend(seleniumwire_options)

        if seleniumwire_options.auto_config:
            # From Selenium v4.0.0 the browser's proxy settings can no longer
            # be passed using desired capabilities and we must use the options
            # object instead.
            proxy = Proxy()
            proxy.http_proxy = config["proxy"]["httpProxy"]
            proxy.ssl_proxy = config["proxy"]["sslProxy"]

            try:
                proxy.no_proxy = config["proxy"]["noProxy"]
            except KeyError:
                pass

            firefox_options.proxy = proxy

        super().__init__(*args, **kwargs)


class Chrome(InspectRequestsMixin, DriverCommonMixin, _Chrome):
    """Extend the Chrome webdriver to provide additional methods for inspecting requests."""

    def __init__(self, *args, seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(), **kwargs):
        """Initialise a new Chrome WebDriver instance."""
        try:
            # Pop-out the chrome_options argument and always use the options
            # argument to pass to the superclass.
            chrome_options = kwargs.pop("chrome_options", None) or kwargs["options"]
        except KeyError:
            chrome_options = ChromeOptions()

        # Prevent Chrome from bypassing the Selenium Wire proxy
        # for localhost addresses.
        chrome_options.add_argument("--proxy-bypass-list=<-loopback>")
        kwargs["options"] = chrome_options

        config = self._setup_backend(seleniumwire_options)

        if seleniumwire_options.auto_config:
            try:
                for key, value in config.items():
                    chrome_options.set_capability(key, value)
            except AttributeError:
                # Earlier versions of the Chromium webdriver API require the
                # DesiredCapabilities to be explicitly passed.
                caps = kwargs.setdefault("desired_capabilities", DesiredCapabilities.CHROME.copy())
                caps.update(config)

        super().__init__(*args, **kwargs)


class Safari(InspectRequestsMixin, DriverCommonMixin, _Safari):
    """Extend the Safari webdriver to provide additional methods for inspecting requests."""

    def __init__(self, seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(), *args, **kwargs):
        """Initialise a new Safari WebDriver instance."""
        # Safari does not support automatic proxy configuration through the
        # DesiredCapabilities API, and thus has to be configured manually.
        # Whatever port number is chosen for that manual configuration has to
        # be passed in the options.
        self._setup_backend(seleniumwire_options)

        super().__init__(*args, **kwargs)


class Edge(InspectRequestsMixin, DriverCommonMixin, _Edge):
    """Extend the Edge webdriver to provide additional methods for inspecting requests."""

    def __init__(self, seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(), *args, **kwargs):
        """Initialise a new Edge WebDriver instance."""
        try:
            # Pop-out the edge_options argument and always use the options
            # argument to pass to the superclass.
            edge_options = kwargs.pop("edge_options", None) or kwargs["options"]
        except KeyError:
            edge_options = EdgeOptions()

        # Prevent Edge from bypassing the Selenium Wire proxy
        # for localhost addresses.
        edge_options.add_argument("--proxy-bypass-list=<-loopback>")
        kwargs["options"] = edge_options

        config = self._setup_backend(seleniumwire_options)

        if seleniumwire_options.auto_config:
            try:
                for key, value in config.items():
                    edge_options.set_capability(key, value)
            except AttributeError:
                # Earlier versions of the Chromium webdriver API require the
                # DesiredCapabilities to be explicitly passed.
                caps = kwargs.setdefault("desired_capabilities", DesiredCapabilities.CHROME.copy())
                caps.update(config)

        super().__init__(*args, **kwargs)


class Remote(InspectRequestsMixin, DriverCommonMixin, _Remote):
    """Extend the Remote webdriver to provide additional methods for inspecting requests."""

    def __init__(self, *args, seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(), **kwargs):
        """Initialise a new Remote WebDriver instance."""
        config = self._setup_backend(seleniumwire_options)

        if seleniumwire_options.auto_config:
            capabilities = kwargs.get("desired_capabilities")
            if capabilities is None:
                capabilities = DesiredCapabilities.FIREFOX.copy()
            else:
                capabilities = capabilities.copy()

            capabilities.update(config)

            kwargs["desired_capabilities"] = capabilities

        super().__init__(*args, **kwargs)
