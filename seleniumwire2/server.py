import asyncio
import logging
from typing import Callable, Iterable, Optional

from mitmproxy import addons
from mitmproxy.addons.proxyserver import Proxyserver
from mitmproxy.connection import Address
from mitmproxy.master import Master
from mitmproxy.options import Options
from mitmproxy.proxy.mode_servers import ServerInstance

from seleniumwire2 import storage
from seleniumwire2.exceptions import SeleniumWireException
from seleniumwire2.handler import InterceptRequestHandler
from seleniumwire2.options import ProxyConfig, SeleniumWireOptions
from seleniumwire2.request import Request, Response
from seleniumwire2.utils import get_mitm_upstream_proxy_args

logger = logging.getLogger(__name__)


class MitmProxy:
    """Run and manage a mitmproxy server instance."""

    def __init__(self, options: SeleniumWireOptions, event_loop: Optional[asyncio.AbstractEventLoop] = None):

        if event_loop is None:
            event_loop = asyncio.get_running_loop()

        self.event_loop = event_loop

        self.options = options

        # Used to stored captured requests
        self.storage = storage.create(**self._get_storage_args())

        # The scope of requests we're interested in capturing
        self.include_urls = []
        self.exclude_urls = []

        self.request_interceptor: Optional[Callable[[Request], None]] = None
        self.response_interceptor: Optional[Callable[[Request, Response], None]] = None

        if options.disable_capture:
            self.include_urls = []
            self.exclude_urls = [".*"]

        self._init_master()

    def _init_master(self):
        mitmproxy_opts = Options()

        self.master = Master(mitmproxy_opts, event_loop=self.event_loop)
        self.master.addons.add(*addons.default_addons())
        self.master.addons.add(SendToLogger())
        self.master.addons.add(InterceptRequestHandler(self))

        options = self.options

        mitmproxy_opts.update(
            confdir=self.storage.home_dir,
            listen_host=options.host,
            listen_port=options.port,
            ssl_insecure=not options.verify_ssl,
            anticomp=options.disable_encoding,
            **get_mitm_upstream_proxy_args(self.options.upstream_proxy),
            # mitm_options are passed through to mitmproxy
            **options.mitm_options,
        )

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
    def server(self) -> Optional[ServerInstance]:
        servers = list(self.master.addons.get("proxyserver").servers)
        if servers:
            return servers[0]
        else:
            return None

    async def _wait_for_proxyserver(self):
        while not (
            self.master and self.master.addons.get("proxyserver") and self.master.addons.get("proxyserver").is_running
        ):
            await asyncio.sleep(0.01)

    def update_server_mode(self, proxy_conf: Optional[ProxyConfig]):
        # save mitmproxy listen address
        host, port, *_ = self.address
        # shutdown mitmproxy
        self._shutdown_mitmproxy()
        # update proxy options
        self.options.upstream_proxy = proxy_conf
        self.options.host = host
        self.options.port = port
        # recreate mitmproxy on same address
        self._init_master()
        self.start()

    def start(self):
        """Run the server."""
        asyncio.run_coroutine_threadsafe(self.master.run(), self.event_loop)
        # wait for proxyserver to start
        asyncio.run(self._wait_for_proxyserver())

    @property
    def address(self) -> Address:
        """Get a tuple of the address and port the proxy server
        is listening on.
        """
        try:
            return self.master.addons.get("proxyserver").listen_addrs()[0]
        except IndexError:
            raise SeleniumWireException("Proxy is not running")

    def _shutdown_mitmproxy(self):
        self.master.shutdown()
        proxyserver: Proxyserver = self.master.addons.get("proxyserver")  # type: ignore
        future = asyncio.run_coroutine_threadsafe(proxyserver.servers.update([]), self.event_loop)
        future.result()

    def shutdown(self):
        """Shutdown the server and perform any cleanup."""
        self._shutdown_mitmproxy()
        self.storage.cleanup()

    def _get_storage_args(self):
        storage_args = {
            "memory_only": self.options.request_storage == "memory",
            "base_dir": self.options.storage_base_dir,
            "maxsize": self.options.request_storage_max_size,
        }

        return storage_args


class SendToLogger:
    def log(self, entry):
        """Send a mitmproxy log message through our own logger."""
        getattr(logger, entry.level.replace("warn", "warning"), logger.info)(entry.msg)
