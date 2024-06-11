from collections.abc import Iterator
from unittest import TestCase
from unittest.mock import Mock, patch

from seleniumwire2.inspect import InspectRequestsMixin, TimeoutException


class Driver(InspectRequestsMixin):
    def __init__(self, backend):
        self.backend = backend


class InspectRequestsMixinTest(TestCase):
    def setUp(self):
        self.mock_backend = Mock()
        self.driver = Driver(self.mock_backend)

    def test_get_requests(self):
        self.mock_backend.storage.load_requests.return_value = [Mock()]

        requests = self.driver.requests

        self.mock_backend.storage.load_requests.assert_called_once_with()
        self.assertEqual(1, len(requests))

    def test_set_requests(self):
        with self.assertRaises(AttributeError):
            self.driver.requests = [Mock()]

    def test_delete_requests(self):
        del self.driver.requests

        self.mock_backend.storage.clear_requests.assert_called_once_with()

    def test_iter_requests(self):
        self.mock_backend.storage.iter_requests.return_value = iter([Mock()])

        self.assertIsInstance(self.driver.iter_requests(), Iterator)

    def test_last_request(self):
        self.mock_backend.storage.load_last_request.return_value = Mock()

        last_request = self.driver.last_request

        self.assertIsNotNone(last_request)
        self.mock_backend.storage.load_last_request.assert_called_once_with()

    def test_last_request_none(self):
        self.mock_backend.storage.load_last_request.return_value = None

        last_request = self.driver.last_request

        self.assertIsNone(last_request)
        self.mock_backend.storage.load_last_request.assert_called_once_with()

    def test_wait_for_request(self):
        self.mock_backend.storage.find.return_value = Mock()

        request = self.driver.wait_for_request("/some/path")

        self.assertIsNotNone(request)
        self.mock_backend.storage.find.assert_called_once_with("/some/path")

    def test_wait_for_request_timeout(self):
        self.mock_backend.storage.find.return_value = None

        with self.assertRaises(TimeoutException):
            self.driver.wait_for_request("/some/path", timeout=1)

        self.assertTrue(self.mock_backend.storage.find.call_count > 0)
        self.assertTrue(self.mock_backend.storage.find.call_count <= 5)

    @patch("seleniumwire2.inspect.har")
    def test_har(self, mock_har):
        self.mock_backend.storage.load_har_entries.return_value = [
            "test_entry1",
            "test_entry2",
        ]
        mock_har.generate_har.return_value = "test_har"

        har = self.driver.har

        self.assertEqual("test_har", har)
        self.mock_backend.storage.load_har_entries.assert_called_once_with()
        mock_har.generate_har.assert_called_once_with(
            [
                "test_entry1",
                "test_entry2",
            ]
        )

    def test_set_include_urls(self):
        scopes = [".*stackoverflow.*", ".*github.*"]

        self.driver.include_urls = scopes

        self.assertEqual(scopes, self.mock_backend.include_urls)

    def test_get_include_urls(self):
        scopes = [".*stackoverflow.*", ".*github.*"]

        self.mock_backend.include_urls = scopes

        self.assertEqual(scopes, self.driver.include_urls)

    def test_set_exclude_urls(self):
        scopes = [".*stackoverflow.*", ".*github.*"]

        self.driver.exclude_urls = scopes

        self.assertEqual(scopes, self.mock_backend.exclude_urls)

    def test_get_exclude_urls(self):
        scopes = [".*stackoverflow.*", ".*github.*"]

        self.mock_backend.exclude_urls = scopes

        self.assertEqual(scopes, self.driver.exclude_urls)

    def test_set_request_interceptor(self):
        def interceptor(r):
            pass

        self.driver.request_interceptor = interceptor

        self.assertEqual(interceptor, self.mock_backend.request_interceptor)

    def test_delete_request_interceptor(self):
        def interceptor(r):
            pass

        self.mock_backend.request_interceptor = interceptor

        del self.driver.request_interceptor

        self.assertIsNone(self.mock_backend.request_interceptor)

    def test_get_request_interceptor(self):
        def interceptor(r):
            pass

        self.mock_backend.request_interceptor = interceptor

        self.assertEqual(interceptor, self.driver.request_interceptor)

    def test_set_response_interceptor(self):
        def interceptor(req, res):
            pass

        self.driver.response_interceptor = interceptor

        self.assertEqual(interceptor, self.mock_backend.response_interceptor)

    def test_set_response_interceptor_invalid_signature(self):
        def interceptor(res):
            pass

        with self.assertRaises(RuntimeError):
            self.driver.response_interceptor = interceptor

    def test_delete_response_interceptor(self):
        def interceptor(req, res):
            pass

        self.mock_backend.response_interceptor = interceptor

        del self.driver.response_interceptor

        self.assertIsNone(self.mock_backend.response_interceptor)

    def test_get_response_interceptor(self):
        def interceptor(req, res):
            pass

        self.mock_backend.response_interceptor = interceptor

        self.assertEqual(interceptor, self.driver.response_interceptor)
