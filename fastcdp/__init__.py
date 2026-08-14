"""Lightweight Chrome Debug Protocol (CDP) client for python

Modules:

- `fastcdp.skill`: Drive Chrome via the DevTools Protocol: navigate, click and fill pages, read them as an LLM-friendly accessibility tree, buffer console/network/dialog activity for debugging, and call any raw CDP command."""

__version__ = "0.0.8"
from .core import *
from .ext import *
