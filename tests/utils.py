import os
import subprocess
from pathlib import Path


def get_chromium_path() -> str:
    """Get the path to a headless chromium executable uncompressing the
    executable if required.

    Returns: The path.
    """

    if os.name == "nt":
        return "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"

    return os.getenv("CHROMIUM_PATH")


class Proxy:
    """Create and manage a mitmdump proxy server.

    The proxy supports two URL schemes which based on the supplied mode: 'http'
    (the default) and 'socks'.

    The proxy will modify HTML responses by adding a comment just before the
    closing </body> tag. The text of the comment will depend on what mode the
    proxy is running in and whether authentication has been specified, but will
    be one of:

        This passed through a http proxy
        This passed through a authenticated http proxy
        This passed through a socks proxy

    Note: authenticated socks proxy not currently supported by mitmdump.

    Clients should call the shutdown() method when they are finished with the
    server.
    """

    def __init__(self, port: int = 8086, mode: str = "http", auth: str = ""):
        """Create a new mitmdump proxy server.

        Args:
            port: Optional port number the proxy server should listen on.
            mode: Optional mode the proxy server will be started in.
                Either 'http' (the default) or 'socks'.
            auth: When supplied, proxy authentication will be enabled.
                The value should be a string in the format: 'username:password'
        """
        assert mode in ("http", "socks"), "mode must be one of 'http' or 'socks'"

        mode_map = {
            "http": "regular",
            "socks": "socks5",
        }

        auth_args = ["--set", f"proxyauth={auth}"] if auth else []

        message = f"This passed through a {'authenticated ' if auth else ''}{mode} proxy"

        self.proc = subprocess.Popen(
            [
                "mitmdump",
                "--listen-port",
                f"{port}",
                "--set",
                f"mode={mode_map[mode]}",
                "--set",
                "flow_detail=0",
                "--set",
                "ssl_insecure",
                *auth_args,
                "-s",
                Path(__file__).parent / "inject_message.py",
                "--set",
                f"message={message}",
            ],
            bufsize=0,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            self.proc.wait(timeout=2)
            # If we're here, wait() has returned meaning no process
            raise RuntimeError(f"Proxy server failed to start: {self.proc.stderr.read().decode()}")
        except subprocess.TimeoutExpired:
            # Server running
            if auth:
                auth = f"{auth}@"
            if mode == "http":
                self.url = f"https://{auth}localhost:{port}"
            else:
                self.url = f"socks5://{auth}localhost:{port}"
            print(f"Created new proxy server at {self.url}")

    def shutdown(self):
        """Shutdown the proxy server."""
        self.proc.terminate()

    def __str__(self):
        return self.url
