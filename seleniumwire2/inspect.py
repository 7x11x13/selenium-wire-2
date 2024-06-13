import inspect
import time
from typing import Callable, Iterator, Optional, Union

from selenium.common.exceptions import TimeoutException

from seleniumwire2 import har
from seleniumwire2.request import Request, Response
from seleniumwire2.server import MitmProxy


class InspectRequestsMixin:
    """Mixin class that provides functions to inspect and modify browser requests."""

    backend: MitmProxy

    @property
    def requests(self) -> list[Request]:
        """Retrieves the requests made between the browser and server.

        Captured requests can be cleared with 'del', e.g:

            del firefox.requests

        Returns:
            A list of Request instances representing the requests made
            between the browser and server.
        """
        return self.backend.storage.load_requests()

    @requests.deleter
    def requests(self):
        self.backend.storage.clear_requests()

    def iter_requests(self) -> Iterator[Request]:
        """Return an iterator of requests.

        Returns: An iterator.
        """
        yield from self.backend.storage.iter_requests()

    @property
    def last_request(self) -> Optional[Request]:
        """Retrieve the last request made between the browser and server.

        Note that this is more efficient than running requests[-1]

        Returns:
            A Request instance representing the last request made, or
            None if no requests have been made.
        """
        return self.backend.storage.load_last_request()

    def wait_for_request(self, pat: str, timeout: Union[int, float] = 10) -> Request:
        """Wait up to the timeout period for a request matching the specified
        pattern to be seen.

        The pat attribute can be can be a simple substring or a regex that will
        be searched in the full request URL. If a request is not seen before the
        timeout then a TimeoutException is raised. Only requests with corresponding
        responses are considered.

        Given that pat can be a regex, ensure that any special characters
        (e.g. question marks) are escaped.

        Args:
            pat: The pat of the request to look for. A regex can be supplied.
            timeout: The maximum time to wait in seconds. Default 10s.

        Returns:
            The request.
        Raises:
            TimeoutException if a request is not seen within the timeout
                period.
        """
        start = time.time()

        while time.time() - start < timeout:
            request = self.backend.storage.find(pat)

            if request is None:
                time.sleep(1 / 5)
            else:
                return request

        raise TimeoutException("Timed out after {}s waiting for request matching {}".format(timeout, pat))

    @property
    def har(self) -> str:
        """Get a HAR archive of HTTP transactions that have taken place.

        Note that the enable_har option needs to be set before HAR
        data will be captured.

        Returns: A JSON string of HAR data.
        """
        return har.generate_har(self.backend.storage.load_har_entries())

    @property
    def include_urls(self) -> list[str]:
        """The URL patterns used to scope request capture. Used
        in conjunction with exclude_urls.

        The value should be a list of regular expressions.

        For example:
            driver.include_urls = [
                '.*stackoverflow.*',
                '.*github.*'
            ]
        """
        return self.backend.include_urls

    @include_urls.setter
    def include_urls(self, new_include_urls: list[str]):
        self.backend.include_urls = new_include_urls

    @include_urls.deleter
    def include_urls(self):
        self.backend.include_urls = []

    @property
    def exclude_urls(self) -> list[str]:
        """The URL patterns used to scope request capture. Used
        in conjunction with include_urls.

        The value should be a list of regular expressions.

        For example:
            driver.exclude_urls = [
                '.*/favicon.ico'
            ]
        """
        return self.backend.exclude_urls

    @exclude_urls.setter
    def exclude_urls(self, new_exclude_urls: list[str]):
        self.backend.exclude_urls = new_exclude_urls

    @exclude_urls.deleter
    def exclude_urls(self):
        self.backend.exclude_urls = []

    @property
    def request_interceptor(self) -> Optional[Callable[[Request], None]]:
        """A callable that will be used to intercept/modify requests.

        The callable must accept a single argument for the request
        being intercepted.
        """
        return self.backend.request_interceptor

    @request_interceptor.setter
    def request_interceptor(self, interceptor: Optional[Callable[[Request], None]]):
        self.backend.request_interceptor = interceptor

    @request_interceptor.deleter
    def request_interceptor(self):
        self.backend.request_interceptor = None

    @property
    def response_interceptor(self) -> Optional[Callable[[Request, Response], None]]:
        """A callable that will be used to intercept/modify responses.

        The callable must accept two arguments: the response being
        intercepted and the originating request.
        """
        return self.backend.response_interceptor

    @response_interceptor.setter
    def response_interceptor(self, interceptor: Optional[Callable[[Request, Response], None]]):
        if len(inspect.signature(interceptor).parameters) != 2:  # type: ignore
            raise RuntimeError("A response interceptor takes two parameters: the request and response")
        self.backend.response_interceptor = interceptor

    @response_interceptor.deleter
    def response_interceptor(self):
        self.backend.response_interceptor = None
