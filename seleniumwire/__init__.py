# -*- coding: utf-8 -*-

"""Top-level package for Selenium Wire."""

__author__ = """Will Keeling"""
__version__ = "5.1.0"

from mitmproxy.certs import Cert
from mitmproxy.http import Headers

from seleniumwire.exceptions import SeleniumWireException
from seleniumwire.options import ProxyConfig, SeleniumWireOptions
from seleniumwire.webdriver import Chrome, Edge, Firefox, Remote, Safari
