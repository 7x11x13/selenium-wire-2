import asyncio
import logging
import threading

from seleniumwire.server import MitmProxy, SeleniumWireOptions

log = logging.getLogger(__name__)


def create(options: SeleniumWireOptions = SeleniumWireOptions()):
    """Create a new proxy backend.

    Args:
        options: Options to configure the proxy.

    Returns:
        An instance of the proxy backend.
    """

    event_loop = asyncio.new_event_loop()

    t = threading.Thread(name="Selenium Wire Proxy Server", target=event_loop.run_forever, daemon=True)
    t.start()

    backend = MitmProxy(options, event_loop)
    backend.start()

    addr, port, *_ = backend.address
    log.info("Created proxy listening on %s:%s", addr, port)

    return backend
