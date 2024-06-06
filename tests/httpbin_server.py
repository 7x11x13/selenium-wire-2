import threading
from pathlib import Path

from flask import Flask
from httpbin import app
from werkzeug.serving import make_server


class ServerThread(threading.Thread):

    def __init__(self, app: Flask, host: str, port: int, ssl_context):
        super().__init__(daemon=True)
        self.server = make_server(host, port, app, ssl_context=ssl_context)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


class Httpbin:
    """Create and manage a httpbin server.

    Creating a new instance of this class will spawn a httpbin server
    in a subprocess. Clients should call the shutdown() method when they
    are finished with the server.
    """

    def __init__(self, port: int = 8085, use_https: bool = True):
        """Create a new httpbin server.

        Args:
            port:
                Optional port number that the httpbin instance should listen on.
            use_https:
                Whether the httpbin instance should use https. When True (the default)
                the httpbin instance will be addressable as 'https://' otherwise 'http://'.
        """
        scheme = "https" if use_https else "http"
        self.url = f"{scheme}://localhost:{port}"

        ssl_context = None
        if use_https:
            cert = Path(__file__).parent / "server.crt"
            key = Path(__file__).parent / "server.key"
            ssl_context = (cert, key)

        self.app = app
        self.t = ServerThread(app, "0.0.0.0", port, ssl_context)
        self.t.start()
        print(f"Created new httpbin server at {self.url}")

    def shutdown(self):
        """Shutdownthe httpbin server."""
        self.t.shutdown()

    def __str__(self):
        return self.url
