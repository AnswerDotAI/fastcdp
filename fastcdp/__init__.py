"""Lightweight Chrome Debug Protocol (CDP) client for python

Modules:

- `fastcdp.skill`: Work with Chrome through the DevTools Protocol: open pages, click and type, read a page as an accessibility tree, keep a log of console and network activity for debugging, and call any CDP command."""

__version__ = "0.0.8"
from .core import *
from .ext import *
