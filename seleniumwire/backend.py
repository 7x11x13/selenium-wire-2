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
    backend = MitmProxy(options)

    t = threading.Thread(
        name="Selenium Wire Proxy Server", target=backend.serve_forever, daemon=not options.standalone
    )
    t.start()

    # wait for proxyserver to start
    asyncio.run(backend.wait_for_proxyserver())

    addr, port, *_ = backend.address()
    log.info("Created proxy listening on %s:%s", addr, port)

    return backend
