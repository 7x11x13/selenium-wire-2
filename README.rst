Selenium Wire 2
===============

Fork of Will Keeling's `Selenium Wire <https://github.com/wkeeling/selenium-wire>`_

Selenium Wire extends `Selenium's <https://www.selenium.dev/documentation/en/>`_ Python bindings to give you access to the underlying requests made by the browser. You author your code in the same way as you do with Selenium, but you get extra APIs for inspecting requests and responses and making changes to them on the fly.

.. image:: https://github.com/7x11x13/selenium-wire-2/workflows/build/badge.svg
        :target: https://github.com/7x11x13/selenium-wire-2/actions

.. image:: https://codecov.io/gh/7x11x13/selenium-wire-2/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/7x11x13/selenium-wire-2

.. image:: https://img.shields.io/badge/python-3.10%2C%203.11%2C%203.12-blue.svg
        :target: https://pypi.python.org/pypi/selenium-wire-2

.. image:: https://img.shields.io/pypi/v/selenium-wire-2.svg
        :target: https://pypi.python.org/pypi/selenium-wire-2

.. image:: https://img.shields.io/pypi/l/selenium-wire-2.svg
        :target: https://pypi.python.org/pypi/selenium-wire-2

.. image:: https://pepy.tech/badge/selenium-wire-2/month
        :target: https://pepy.tech/project/selenium-wire-2

Simple Example
~~~~~~~~~~~~~~

.. code:: python

    from seleniumwire2 import webdriver  # Import from seleniumwire

    # Create a new instance of the Chrome driver
    driver = webdriver.Chrome()

    # Go to the Google home page
    driver.get("https://www.google.com")

    # Access requests via the `requests` attribute
    for request in driver.requests:
        if request.response:
            print(
                request.url,
                request.response.status_code,
                request.response.headers["Content-Type"]
            )

Prints:

.. code:: bash

    https://www.google.com/ 200 text/html; charset=UTF-8
    https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_120x44dp.png 200 image/png
    https://consent.google.com/status?continue=https://www.google.com&pc=s&timestamp=1531511954&gl=GB 204 text/html; charset=utf-8
    https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png 200 image/png
    https://ssl.gstatic.com/gb/images/i2_2ec824b0.png 200 image/png
    https://www.google.com/gen_204?s=webaft&t=aft&atyp=csi&ei=kgRJW7DBONKTlwTK77wQ&rt=wsrt.366,aft.58,prt.58 204 text/html; charset=UTF-8
    ...

Features
~~~~~~~~

* Pure Python, user-friendly API
* HTTP and HTTPS requests captured
* Intercept requests and responses
* Modify headers, parameters, body content on the fly
* Capture websocket messages
* HAR format supported
* Proxy server support

Compatibilty
~~~~~~~~~~~~

* Python 3.10+
* Selenium 4.0.0+
* Chrome, Firefox, Edge, Safari, and Remote Webdriver supported

Table of Contents
~~~~~~~~~~~~~~~~~

- `Installation`_

  * `Browser Setup`_

  * `OpenSSL`_

  * `Certificates`_

- `Creating the Webdriver`_

- `Accessing Requests`_

- `Request Objects`_

- `Response Objects`_

- `Intercepting Requests and Responses`_

  * `Example: Add a request header`_
  * `Example: Replace an existing request header`_
  * `Example: Add a response header`_
  * `Example: Add a request parameter`_
  * `Example: Update JSON in a POST request body`_
  * `Example: Basic authentication`_
  * `Example: Block a request`_
  * `Example: Mock a response`_
  * `Unset an interceptor`_

- `Limiting Request Capture`_

- `Request Storage`_

  * `In-Memory Storage`_

- `Upstream Proxies`_

  * `SOCKS Upstream Proxy`_

  * `Switching Dynamically`_

- `All Options`_

- `License`_

Installation
~~~~~~~~~~~~

Install using pip:

.. code:: bash

    pip install selenium-wire-2

If you get an error about not being able to build cryptography you may be running an old version of pip. Try upgrading pip with ``python -m pip install --upgrade pip`` and then re-run the above command.

Browser Setup
-------------

No specific configuration should be necessary except to ensure that you have downloaded the relevent webdriver executable for your browser and placed it somewhere on your system PATH.

- `Download <https://sites.google.com/chromium.org/driver/>`__ webdriver for Chrome
- `Download <https://github.com/mozilla/geckodriver/>`__ webdriver for Firefox
- `Download <https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/>`__ webdriver for Edge

OpenSSL
-------

Selenium Wire requires OpenSSL for decrypting HTTPS requests. This is probably already installed on your system (you can check by running ``openssl version`` on the command line). If it's not installed you can install it with:

**Linux**

.. code:: bash

    # For apt based Linux systems
    sudo apt install openssl

    # For RPM based Linux systems
    sudo yum install openssl

    # For Linux alpine
    sudo apk add openssl

**MacOS**

.. code:: bash

    brew install openssl

**Windows**

No installation is required.

Certificates
------------

See https://docs.mitmproxy.org/stable/concepts-certificates/#the-mitmproxy-certificate-authority

The CA certificate is stored in the directory specified by ``storage_base_dir``.

Creating the Webdriver
~~~~~~~~~~~~~~~~~~~~~~

Ensure that you import ``webdriver`` from the ``seleniumwire2`` package:

.. code:: python

    from seleniumwire2 import webdriver

Then just instantiate the webdriver as you would if you were using Selenium directly. You can pass in any desired capabilities or browser specific options - such as the executable path, headless mode etc. Selenium Wire also has it's `own options`_ that can be passed in the ``seleniumwire_options`` attribute.

.. code:: python

    # Create the driver with no options (use defaults)
    driver = webdriver.Chrome()

    # Or create using browser specific options and/or seleniumwire_options options
    driver = webdriver.Chrome(
        options = webdriver.ChromeOptions(...),
        seleniumwire_options={...}
    )

.. _`own options`: #all-options

Note that for sub-packages of ``webdriver``, you should continue to import these directly from ``selenium``. For example, to import ``WebDriverWait``:

.. code:: python

    # Sub-packages of webdriver must still be imported from `selenium` itself
    from selenium.webdriver.support.ui import WebDriverWait

**Remote Webdriver**

Selenium Wire has limited support for using the remote webdriver client. When you create an instance of the remote webdriver, you need to specify the hostname or IP address of the machine (or container) running Selenium Wire. This allows the remote instance to communicate back to Selenium Wire with its requests and responses.

.. code:: python

    options = SeleniumWireOptions(
        host=hostname_or_ip  # Address of the machine running Selenium Wire. Explicitly use 127.0.0.1 rather than localhost if remote session is running locally.
    )
    driver = webdriver.Remote(
        command_executor="http://www.example.com",
        seleniumwire_options=options
    )

If the machine running the browser needs to use a different address to talk to the machine running Selenium Wire you need to configure the browser manually. `This issue <https://github.com/wkeeling/selenium-wire/issues/220>`_ goes into more detail.

Accessing Requests
~~~~~~~~~~~~~~~~~~

Selenium Wire captures all HTTP/HTTPS traffic made by the browser [1]_. The following attributes provide access to requests and responses.

``driver.requests``
    The list of captured requests in chronological order.

``driver.last_request``
    Convenience attribute for retrieving the most recently captured request. This is more efficient than using ``driver.requests[-1]``.

``driver.wait_for_request(pat, timeout=10)``
    This method will wait until it sees a request matching a pattern. The ``pat`` attribute will be matched within the request URL. ``pat`` can be a simple substring or a regular expression. Note that ``driver.wait_for_request()`` doesn't *make* a request, it just *waits* for a previous request made by some other action and it will return the first request it finds. Also note that since ``pat`` can be a regular expression, you must escape special characters such as question marks with a slash. A ``TimeoutException`` is raised if no match is found within the timeout period.

    For example, to wait for an AJAX request to return after a button is clicked:

    .. code:: python

        # Click a button that triggers a background request to https://server/api/products/12345/
        button_element.click()

        # Wait for the request/response to complete
        request = driver.wait_for_request("/api/products/12345/")

``driver.har``
    A JSON formatted HAR archive of HTTP transactions that have taken place. HAR capture is turned off by default and you must set the ``enable_har`` `option`_ to ``True`` before using ``driver.har``.

``driver.iter_requests()``
    Returns an iterator over captured requests. Useful when dealing with a large number of requests.

``driver.request_interceptor``
    Used to set a request interceptor. See `Intercepting Requests and Responses`_.

``driver.response_interceptor``
    Used to set a response interceptor.

**Clearing Requests**

To clear previously captured requests and HAR entries, use ``del``:

.. code:: python

    del driver.requests

.. [1] Selenium Wire ignores OPTIONS requests by default, as these are typically uninteresting and just add overhead. If you want to capture OPTIONS requests, you need to set the ``ignore_http_methods`` `option`_ to ``[]``.

.. _`option`: #all-options

Request Objects
~~~~~~~~~~~~~~~

Request objects have the following attributes.

``body``
    The request body as ``bytes``. If the request has no body the value of ``body`` will be empty, i.e. ``b""``.

``certificate_list``
    Information about the server SSL certificates. Empty for non-HTTPS requests.

``date``
    The datetime the request was made.

``headers``
    A dictionary-like object of request headers. Headers are case-insensitive and duplicates are permitted. Asking for ``request.headers["user-agent"]`` will return the value of the ``User-Agent`` header. If you wish to replace a header, make sure you delete the existing header first with ``del request.headers["header-name"]``, otherwise you'll create a duplicate.

``host``
    The request host, e.g. ``www.example.com``

``method``
    The HTTP method, e.g. ``GET`` or ``POST`` etc.

``params``
    A dictionary of request parameters. If a parameter with the same name appears more than once in the request, it's value in the dictionary will be a list.

``path``
    The request path, e.g. ``/some/path/index.html``

``querystring``
    The query string, e.g. ``foo=bar&spam=eggs``

``response``
   The `response object`_ associated with the request. This will be ``None`` if the request has no response.

``url``
    The request URL, e.g. ``https://www.example.com/some/path/index.html?foo=bar&spam=eggs``

``ws_messages``
    Where the request is a websocket handshake request (normally with a URL starting ``wss://``) then ``ws_messages`` will contain a list of any websocket messages sent and received. See `WebSocketMessage Objects`_.

Request objects have the following methods.

``abort(error_code=403)``
    Trigger immediate termination of the request with the supplied error code. For use within request interceptors. See `Example: Block a request`_.

``create_response(status_code, headers=(), body=b"")``
    Create a response and return it without sending any data to the remote server. For use within request interceptors. See `Example: Mock a response`_.

.. _`response object`: #response-objects

WebSocketMessage Objects
------------------------

These objects represent websocket messages sent between the browser and server and vice versa. They are held in a list by ``request.ws_messages`` on websocket handshake requests. They have the following attributes.

``content``
    The message content which may be either ``str`` or ``bytes``.

``date``
    The datetime of the message.

``from_client``
    ``True`` when the message was sent by the client and ``False`` when sent by the server.

Response Objects
~~~~~~~~~~~~~~~~

Response objects have the following attributes.

``body``
    The response body as ``bytes``. If the response has no body the value of ``body`` will be empty, i.e. ``b""``. Sometimes the body may have been compressed by the server. You can prevent this with the ``disable_encoding`` `option`_. To manually decode an encoded response body you can do:

.. code:: python

    from seleniumwire2.utils import decode

    body = decode(response.body, response.headers.get("Content-Encoding", "identity"))


``date``
    The datetime the response was received.

``headers``
     A dictionary-like object of response headers. Headers are case-insensitive and duplicates are permitted. Asking for ``response.headers["content-length"]`` will return the value of the ``Content-Length`` header. If you wish to replace a header, make sure you delete the existing header first with ``del response.headers["header-name"]``, otherwise you'll create a duplicate.

``reason``
    The reason phrase, e.g. ``OK`` or ``Not Found`` etc.

``status_code``
    The status code of the response, e.g. ``200`` or ``404`` etc.


Intercepting Requests and Responses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As well as capturing requests and responses, Selenium Wire allows you to modify them on the fly using interceptors. An interceptor is a function that gets invoked with requests and responses as they pass through Selenium Wire. Within an interceptor you can modify the request and response as you see fit.

You set your interceptor functions using the ``driver.request_interceptor`` and ``driver.response_interceptor`` attributes before you start using the driver. A request interceptor should accept a single argument for the request. A response interceptor should accept two arguments, one for the originating request and one for the response.

Example: Add a request header
-----------------------------

.. code:: python

    def interceptor(request):
        request.headers["New-Header"] = "Some Value"

    driver.request_interceptor = interceptor
    driver.get(...)

    # All requests will now contain New-Header

How can I check that a header has been set correctly? You can print the headers from captured requests after the page has loaded using ``driver.requests``, or alternatively point the webdriver at https://httpbin.org/headers which will echo the request headers back to the browser so you can view them.

Example: Replace an existing request header
-------------------------------------------

Duplicate header names are permitted in an HTTP request, so before setting the replacement header you must first delete the existing header using ``del`` like in the following example, otherwise two headers with the same name will exist (``request.headers`` is a special dictionary-like object that allows duplicates).

.. code:: python

    def interceptor(request):
        del request.headers["Referer"]  # Remember to delete the header first
        request.headers["Referer"] = "some_referer"  # Spoof the referer

    driver.request_interceptor = interceptor
    driver.get(...)

    # All requests will now use "some_referer" for the referer

Example: Add a response header
------------------------------

.. code:: python

    def interceptor(request, response):  # A response interceptor takes two args
        if request.url == "https://server.com/some/path":
            response.headers["New-Header"] = "Some Value"

    driver.response_interceptor = interceptor
    driver.get(...)

    # Responses from https://server.com/some/path will now contain New-Header

Example: Add a request parameter
--------------------------------

Request parameters work differently to headers in that they are calculated when they are set on the request. That means that you first have to read them, then update them, and then write them back - like in the following example. Parameters are held in a regular dictionary, so parameters with the same name will be overwritten.

.. code:: python

    def interceptor(request):
        params = request.params
        params["foo"] = "bar"
        request.params = params

    driver.request_interceptor = interceptor
    driver.get(...)

    # foo=bar will be added to all requests

Example: Update JSON in a POST request body
-----------------------------------------------

.. code:: python

    import json

    def interceptor(request):
        if request.method == "POST" and request.headers["Content-Type"] == "application/json":
            # The body is in bytes so convert to a string
            body = request.body.decode("utf-8")
            # Load the JSON
            data = json.loads(body)
            # Add a new property
            data["foo"] = "bar"
            # Set the JSON back on the request
            request.body = json.dumps(data).encode("utf-8")
            # Update the content length
            del request.headers["Content-Length"]
            request.headers["Content-Length"] = str(len(request.body))

    driver.request_interceptor = interceptor
    driver.get(...)

Example: Basic authentication
-----------------------------

If a site requires a username/password, you can use a request interceptor to add authentication credentials to each request. This will stop the browser from displaying a username/password pop-up.

.. code:: python

    import base64

    auth = (
        base64.encodebytes("my_username:my_password".encode())
        .decode()
        .strip()
    )

    def interceptor(request):
        if request.host == "host_that_needs_auth":
            request.headers["Authorization"] = f"Basic {auth}"

    driver.request_interceptor = interceptor
    driver.get(...)

    # Credentials will be transmitted with every request to "host_that_needs_auth"

Example: Block a request
------------------------

You can use ``request.abort()`` to block a request and send an immediate response back to the browser. An optional error code can be supplied. The default is 403 (forbidden).

.. code:: python

    def interceptor(request):
        # Block PNG, JPEG and GIF images
        if request.path.endswith((".png", ".jpg", ".gif")):
            request.abort()

    driver.request_interceptor = interceptor
    driver.get(...)

    # Requests for PNG, JPEG and GIF images will result in a 403 Forbidden

Example: Mock a response
------------------------

You can use ``request.create_response()`` to send a custom reply back to the browser. No data will be sent to the remote server.

.. code:: python

    def interceptor(request):
        if request.url == "https://server.com/some/path":
            request.create_response(
                status_code=200,
                headers={"Content-Type": "text/html"},  # Optional headers dictionary
                body="<html>Hello World!</html>"  # Optional body
            )

    driver.request_interceptor = interceptor
    driver.get(...)

    # Requests to https://server.com/some/path will have their responses mocked

*Have any other examples you think could be useful? Feel free to submit a PR.*

Unset an interceptor
--------------------

To unset an interceptor, use ``del``:

.. code:: python

    del driver.request_interceptor
    del driver.response_interceptor

Limiting Request Capture
~~~~~~~~~~~~~~~~~~~~~~~~

Selenium Wire works by redirecting browser traffic through an internal proxy server it spins up in the background. As requests flow through the proxy they are intercepted and captured. Capturing requests can slow things down a little but there are a few things you can do to restrict what gets captured.

``driver.include_urls`` and ``driver.exclude_urls``
    TODO This accepts a list of regular expressions that will match the URLs to be captured. It should be set on the driver before making any requests. When empty (the default) all URLs are captured.

    .. code:: python

        driver.include_urls = [
            ".*stackoverflow.*",
            ".*github.*"
        ]

        driver.get(...)  # Start making requests

        # Only request URLs containing "stackoverflow" or "github" will now be captured

    .. code:: python

        driver.exclude_urls = [
            ".*stackoverflow.*",
            ".*github.*"
        ]

        driver.get(...)  # Start making requests

        # Only request URLs not containing "stackoverflow" or "github" will now be captured

    Note that even if a request is out of scope and not captured, it will still travel through Selenium Wire.

``seleniumwire_options.disable_capture``
    Use this option to switch off request capture. Requests will still pass through Selenium Wire and through any upstream proxy you have configured but they won't be intercepted or stored. Request interceptors will not execute.

``seleniumwire_options.exclude_hosts``
    Use this option to bypass Selenium Wire entirely. Any requests made to addresses listed here will go direct from the browser to the server without involving Selenium Wire. Note that if you've configured an upstream proxy then these requests will also bypass that proxy.

``request.abort()``
    You can abort a request early by using ``request.abort()`` from within a `request interceptor`_. This will send an immediate response back to the client without the request travelling any further. You can use this mechanism to block certain types of requests (e.g. images) to improve page load performance.

    .. code:: python

        def interceptor(request):
            # Block PNG, JPEG and GIF images
            if request.path.endswith((".png", ".jpg", ".gif")):
                request.abort()

        driver.request_interceptor = interceptor

        driver.get(...)  # Start making requests

.. _`request interceptor`: #intercepting-requests-and-responses

Request Storage
~~~~~~~~~~~~~~~

Captured requests and responses are stored in the home folder by default (that's ``~/`` on Linux/Mac and usually ``C:\Users\<username>`` on Windows) in a sub-folder called ``.seleniumwire``. To change where the ``.seleniumwire`` folder gets created you can use the ``storage_base_dir`` option:

.. code:: python

    options = SeleniumWireOptions(
        storage_base_dir="/my/storage/folder"  # .seleniumwire will get created here
    )
    driver = webdriver.Chrome(seleniumwire_options=options)

In-Memory Storage
-----------------

Selenium Wire also supports storing requests and responses in memory only, which may be useful in certain situations - e.g. if you're running short lived Docker containers and don't want the overhead of disk persistence. You can enable in-memory storage by setting the ``request_storage`` option to ``memory``:

.. code:: python

    from seleniumwire2 import SeleniumWireOptions
    options = SeleniumWireOptions(request_storage="memory")
    driver = webdriver.Chrome(seleniumwire_options=options)

If you're concerned about the amount of memory that may be consumed, you can restrict the number of requests that are stored with the ``request_storage_max_size`` option:

.. code:: python

    from seleniumwire2 import SeleniumWireOptions
    options = SeleniumWireOptions(
        request_storage="memory",
        request_storage_max_size=100  # Store no more than 100 requests in memory
    )
    driver = webdriver.Chrome(seleniumwire_options=options)

When the max size is reached, older requests are discarded as newer requests arrive. Keep in mind that if you restrict the number of requests being stored, requests may have disappeared from storage by the time you come to retrieve them with ``driver.requests`` or ``driver.wait_for_request()`` etc.

Upstream Proxies
~~~~~~~~~~~~~~~~

If the site you are accessing sits behind a proxy server you can tell Selenium Wire about that proxy server in the options you pass to the webdriver.

The configuration takes the following format:

.. code:: python

    from seleniumwire2 import ProxyConfig, SeleniumWireOptions
    options = SeleniumWireOptions(
        upstream_proxy=ProxyConfig(
            http="http://192.168.10.100:8888",
            https="https://192.168.10.100:8888"
        )
    )
    driver = webdriver.Chrome(seleniumwire_options=options)

To use HTTP Basic Auth with your proxy, specify the username and password in the URL:

.. code:: python

    from seleniumwire2 import ProxyConfig, SeleniumWireOptions
    options = SeleniumWireOptions(
        upstream_proxy=ProxyConfig(
            https="https://user:pass@192.168.10.100:8888"
        }
    }

If no upstream proxy config is supplied, seleniumwire uses the ``HTTP_PROXY`` and ``HTTPS_PROXY`` environment variables:

.. code:: bash

    $ export HTTP_PROXY="http://192.168.10.100:8888"
    $ export HTTPS_PROXY="https://192.168.10.100:8888"

SOCKS Upstream Proxy
--------------------

SOCKS upstream proxies are not supported. See https://github.com/mitmproxy/mitmproxy/issues/211

**Using Selenium Wire with Tor**

See `this example <https://gist.github.com/woswos/38b921f0b82de009c12c6494db3f50c5>`_ if you want to run Selenium Wire with Tor.

Switching Dynamically
---------------------

If you want to change the proxy settings for an existing driver instance, use the ``driver.set_upstream_proxy`` and ``driver.remove_upstream_proxy`` methods:

.. code:: python

    driver.get(...)  # Using some initial proxy

    # Change the upstream proxy
    driver.set_upstream_proxy(ProxyConfig(https="https://user:pass@192.168.10.100:8888"))

    driver.get(...)  # These requests will use the new proxy

    # Remove the upstream proxy
    driver.remove_upstream_proxy()

All Options
~~~~~~~~~~~

A summary of all options that can be passed to Selenium Wire via the ``seleniumwire_options`` webdriver attribute.

``host``
    The IP address or hostname of the machine running Selenium Wire. This defaults to 127.0.0.1. You may want to change this to the public IP of the machine (or container) if you're using the `remote webdriver`_.

.. code:: python

    options = SeleniumWireOptions(
        host="192.168.0.10"  # Use the public IP of the machine
    )
    driver = webdriver.Chrome(seleniumwire_options=options)

.. _`remote webdriver`: #creating-the-webdriver

``port``
    The port number that Selenium Wire's backend listens on. Defaults to 0, which selects an available port automatically.

``auto_config``
    Whether Selenium Wire should auto-configure the browser for request capture. ``True`` by default.

``disable_capture``
    Disable request capture. When ``True`` nothing gets intercepted or stored. ``False`` by default.

``disable_encoding``
    Ask the server to send back uncompressed data. ``False`` by default. When ``True`` this sets the ``Accept-Encoding`` header to ``identity`` for all outbound requests. Note that it won't always work - sometimes the server may ignore it.

``enable_har``
    When ``True`` a HAR archive of HTTP transactions will be kept which can be retrieved with ``driver.har``. ``False`` by default.

``exclude_hosts``
    A list of addresses for which Selenium Wire should be bypassed entirely. Note that if you have configured an upstream proxy then requests to excluded hosts will also bypass that proxy.

``ignore_http_methods``
    A list of HTTP methods (specified as uppercase strings) that should be ignored by Selenium Wire and not captured. The default is ``["OPTIONS"]`` which ignores all OPTIONS requests. To capture all request methods, set ``ignore_http_methods`` to an empty list:

``request_storage``
    The type of storage to use. Selenium Wire defaults to disk based storage, but you can switch to in-memory storage by setting this option to ``memory``:

``request_storage_max_size``
    The maximum number of requests to store when using in-memory storage. Unlimited by default. This option currently has no effect when using the default disk based storage.

``storage_base_dir``
    The base location where Selenium Wire stores captured requests and responses when using its default disk based storage. This defaults to the home folder (that's ``~/`` on Linux/Mac and usually ``C:\Users\<username>\`` on Windows). A sub-folder called ``.seleniumwire`` will get created here to store the captured data and mitmproxy certificates.

``upstream_proxy``
    The upstream `proxy server <https://github.com/7x11x13/selenium-wire-2#Upstream Proxies>`__ configuration if you're using a proxy.

``verify_ssl``
    Whether SSL certificates should be verified. ``False`` by default, which prevents errors with self-signed certificates.

``mitm_options``
    Dictionary of options to pass to the underlying mitmproxy server. See https://docs.mitmproxy.org/stable/concepts-options/

License
~~~~~~~

MIT
