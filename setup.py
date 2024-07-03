#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

setup(
    author="7x11x13",
    author_email="x7x11x13@gmail.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    description="Extends Selenium to give you the ability to inspect requests made by the browser.",
    license="MIT",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[
        "mitmproxy>=10.3.0",
        "selenium>=4.0.0",
    ],
    package_data={"seleniumwire2": ["py.typed"]},
    extras_require={"test": ["httpbin", "pytest", "pytest-cov"]},
    keywords="selenium-wire-2",
    name="selenium-wire-2",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    setup_requires=[],
    test_suite="tests.seleniumwire",
    tests_require=["pytest"],
    url="https://github.com/7x11x13/selenium-wire-2",
    version="0.2.1",
    zip_safe=False,
)
