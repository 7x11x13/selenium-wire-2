import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

from mitmproxy.http import Headers, HTTPFlow
from mitmproxy.http import Request as MitmRequest
from mitmproxy.http import Response as MitmResponse

from seleniumwire2 import har
from seleniumwire2.request import Request, Response, WebSocketMessage

if TYPE_CHECKING:
    from seleniumwire2.server import MitmProxy

log = logging.getLogger(__name__)


class InterceptRequestHandler:
    """Mitmproxy add-on which is responsible for request modification
    and capture.
    """

    def __init__(self, proxy: "MitmProxy"):
        self.proxy = proxy

    def requestheaders(self, flow: HTTPFlow):
        # Requests that are being captured are not streamed.
        if self._should_capture(flow.request):
            flow.request.stream = False

    def request(self, flow: HTTPFlow):
        # Convert to one of our requests for handling
        request = self._create_request(flow)

        if not self._should_capture(request):
            log.debug("Not capturing %s request: %s", request.method, request.url)
            return

        # Call the request interceptor if set
        if self.proxy.request_interceptor is not None:
            self.proxy.request_interceptor(request)

            if request.response:
                # The interceptor has created a response for us to send back immediately
                flow.response = MitmResponse.make(
                    status_code=int(request.response.status_code),
                    content=request.response.body,
                    headers=[(k.encode("utf-8"), v.encode("utf-8")) for k, v in request.response.headers.items()],
                )
            else:
                flow.request.method = request.method
                flow.request.url = request.url.replace("wss://", "https://", 1)
                flow.request.headers = self._to_headers_obj(request.headers)
                flow.request.raw_content = request.body

        log.info("Capturing request: %s", request.url)

        self.proxy.storage.save_request(request)

        if request.id is not None:  # Will not be None when captured
            setattr(flow.request, "id", request.id)

        if request.response:
            # This response will be a mocked response. Capture it for completeness.
            self.proxy.storage.save_response(request.id, request.response)

    def _should_capture(self, request: MitmRequest):
        if request.method in self.proxy.options.ignore_http_methods:
            return False

        include = self.proxy.include_urls or []
        exclude = self.proxy.exclude_urls or []

        if not include and not exclude:
            return True

        if ".*" in exclude:
            return False

        included = False
        for inc in include:
            match = re.match(inc, request.url)
            if match:
                included = True
                break

        if include and not included:
            # if include is empty, include all urls
            return False

        for ex in exclude:
            match = re.match(ex, request.url)
            if match:
                return False

        return True

    def responseheaders(self, flow: HTTPFlow):
        # Responses that are being captured are not streamed.
        if self._should_capture(flow.request):
            assert flow.response is not None
            flow.response.stream = False

    def response(self, flow: HTTPFlow):
        if not hasattr(flow.request, "id"):
            # Request was not stored
            return

        # Convert the mitmproxy specific response to one of our responses
        # for handling.
        response = self._create_response(flow)

        # Call the response interceptor if set
        if self.proxy.response_interceptor is not None:
            self.proxy.response_interceptor(self._create_request(flow, response), response)
            assert flow.response is not None
            flow.response.status_code = response.status_code
            flow.response.reason = response.reason
            flow.response.headers = self._to_headers_obj(response.headers)
            flow.response.raw_content = response.body

        log.info("Capturing response: %s %s %s", flow.request.url, response.status_code, response.reason)

        self.proxy.storage.save_response(flow.request.id, response)

        if self.proxy.options.enable_har:
            self.proxy.storage.save_har_entry(flow.request.id, har.create_har_entry(flow))

    def _create_request(self, flow: HTTPFlow, response=None):
        request = Request(
            method=flow.request.method,
            url=flow.request.url,
            headers=[(k, v) for k, v in flow.request.headers.items()],
            body=flow.request.raw_content or b"",
        )

        request.response = response

        return request

    def _create_response(self, flow: HTTPFlow):
        assert flow.response is not None
        response = Response(
            status_code=flow.response.status_code,
            reason=flow.response.reason,
            headers=[(k, v) for k, v in flow.response.headers.items(multi=True)],
            body=flow.response.raw_content,
        )

        response.certificate_list = list(flow.server_conn.certificate_list)

        return response

    def _to_headers_obj(self, headers: dict[str, Any]):
        return Headers([(k.encode("utf-8"), str(v).encode("utf-8")) for k, v in headers.items()])

    def websocket_message(self, flow: HTTPFlow):
        if hasattr(flow.request, "id") and flow.websocket:
            for message in flow.websocket.messages:
                ws_message = WebSocketMessage(
                    from_client=message.from_client,
                    content=message.content,
                    date=datetime.fromtimestamp(message.timestamp),
                )

                self.proxy.storage.save_ws_message(flow.request.id, ws_message)

                if message.from_client:
                    direction = "(client -> server)"
                else:
                    direction = "(server -> client)"

                log.debug("Capturing websocket message %s: %s", direction, ws_message)
