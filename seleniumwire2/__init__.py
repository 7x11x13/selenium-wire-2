# -*- coding: utf-8 -*-

"""Top-level package for Selenium Wire."""

__author__ = """7x11x13"""
__version__ = "0.1.0"

from mitmproxy.certs import Cert
from mitmproxy.http import Headers

from seleniumwire2.exceptions import SeleniumWireException
from seleniumwire2.options import ProxyConfig, SeleniumWireOptions
from seleniumwire2.webdriver import Chrome, Edge, Firefox, Remote, Safari
