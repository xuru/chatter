========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/chatter/badge/?style=flat
    :target: https://readthedocs.org/projects/chatter
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/xuru/chatter.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/xuru/chatter

.. |codecov| image:: https://codecov.io/github/xuru/chatter/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/xuru/chatter

.. |version| image:: https://img.shields.io/pypi/v/chatter.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/chatter

.. |commits-since| image:: https://img.shields.io/github/commits-since/xuru/chatter/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/xuru/chatter/compare/v0.1.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/chatter.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/chatter

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/chatter.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/chatter

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/chatter.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/chatter


.. end-badges

A natural language generation app, for creating RASA NLU training data

* Free software: MIT license

Installation
============

::

    pip install chatter

Documentation
=============

https://chatter.readthedocs.io/

Development
===========

To run all tests, open a terminal, and type::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox

