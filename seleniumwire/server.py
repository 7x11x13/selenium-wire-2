import asyncio
import logging
from typing import Callable, Iterable, Optional

from mitmproxy import addons
from mitmproxy.connection import Address
from mitmproxy.master import Master
from mitmproxy.options import Options
from mitmproxy.proxy.mode_servers import ServerInstance

from seleniumwire import storage
from seleniumwire.handler import InterceptRequestHandler
from seleniumwire.options import SeleniumWireOptions
from seleniumwire.request import Request, Response
from seleniumwire.utils import get_mitm_upstream_proxy_args

logger = logging.getLogger(__name__)


class MitmProxy:
    """Run and manage a mitmproxy server instance."""

    def __init__(self, options: SeleniumWireOptions):
        self.options = options

        # Used to stored captured requests
        self.storage = storage.create(**self._get_storage_args())

        # The scope of requests we're interested in capturing
        self.include_urls = []
        self.exclude_urls = []

        self.request_interceptor: Optional[Callable[[Request], None]] = None
        self.response_interceptor: Optional[Callable[[Request, Response], None]] = None

        self._event_loop = asyncio.new_event_loop()

        mitmproxy_opts = Options()

        self.master = Master(
            mitmproxy_opts,
            event_loop=self._event_loop,
        )
        self.master.addons.add(*addons.default_addons())
        self.master.addons.add(SendToLogger())
        self.master.addons.add(InterceptRequestHandler(self))

        mitmproxy_opts.update(
            confdir=self.storage.home_dir,
            listen_host=options.addr,
            listen_port=options.port,
            ssl_insecure=not options.verify_ssl,
            **get_mitm_upstream_proxy_args(self.options.upstream_proxy),
            # mitm_options are passed through to mitmproxy
            **options.mitm_options,
        )

        if options.disable_capture:
            self.include_urls = []
            self.exclude_urls = [".*"]

    @property
    def include_urls(self) -> list[str]:
        return self._include_urls

    @include_urls.setter
    def include_urls(self, new_include_urls: str | Iterable[str]):
        if isinstance(new_include_urls, str):
            self._include_urls = [new_include_urls]
        else:
            self._include_urls = list(new_include_urls)

    @property
    def exclude_urls(self) -> list[str]:
        return self._exclude_urls

    @exclude_urls.setter
    def exclude_urls(self, new_exclude_urls: str | Iterable[str]):
        if isinstance(new_exclude_urls, str):
            self._exclude_urls = [new_exclude_urls]
        else:
            self._exclude_urls = list(new_exclude_urls)

    @property
    def server(self) -> ServerInstance:
        return next(iter(self.master.addons.get("proxyserver").servers))

    async def wait_for_proxyserver(self):
        while not self.master.addons.get("proxyserver").is_running:
            await asyncio.sleep(0.01)

    def serve_forever(self):
        """Run the server."""
        asyncio.run(self.master.run())

    def address(self) -> Address:
        """Get a tuple of the address and port the proxy server
        is listening on.
        """
        return self.master.addons.get("proxyserver").listen_addrs()[0]

    def shutdown(self):
        """Shutdown the server and perform any cleanup."""
        self.master.shutdown()
        self.storage.cleanup()

    def _get_storage_args(self):
        storage_args = {
            "memory_only": self.options.request_storage == "memory",
            "base_dir": self.options.request_storage_base_dir,
            "maxsize": self.options.request_storage_max_size,
        }

        return storage_args


class SendToLogger:
    def log(self, entry):
        """Send a mitmproxy log message through our own logger."""
        getattr(logger, entry.level.replace("warn", "warning"), logger.info)(entry.msg)
