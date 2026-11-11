"""Lightweight Chrome Debug Protocol (CDP) client for python

Modules:

- `fastcdp.skill`: Work with Chrome through the DevTools Protocol: inspect pages, interact with controls, and diagnose browser applications.
- `fastcdp.vitest`: Run Vitest against an existing Chrome through fastcdp"""

__version__ = "0.0.26"
from .core import *
from .ext import *
