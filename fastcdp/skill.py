r"""Work with Chrome through the DevTools Protocol: inspect pages, interact with controls, and diagnose browser applications.

Choose the browser before connecting. An everyday browser carries the user's logged-in sessions: use one only when the user names it; if a task needs logins and none is named, ask; otherwise use a separate automation profile.

# Choose a connection

- Explicitly requested everyday browser: the companion extension (`ExtCDP`) when available. Direct access (`CDP.connect`) requires the user to enable remote debugging and approve the connection popup; it finds the browser with `cdp_conninfo`, which reads a profile's `DevToolsActivePort`.
- Dedicated debug browser: `CDP.remote`; `fastcdp-setup` creates its launcher.
- Separate automation profile: inspect `CDP.launch`.
- Isolated tests, no existing cookies/logins: `async with CDP.testing(headless=True) as cdp:` owns a Chrome for Testing process and temporary profile, both cleaned up on exit. Install it explicitly with `fastcdp-setup --install stable` (`--with-deps` on Debian/Ubuntu); real-Chrome launchers, profiles, and connection modes are untouched.

Read the chosen method's docs before calling it; once connected, inspect the connection for tab creation, attachment, and cleanup. Work in background tabs unless bringing one forward is part of the request. Don't close the user's tabs or quit their browser as routine cleanup; read the relevant `close`/`quit` docs: tab ownership and connection ownership are different.

# Discover the actual object

Read `doc(page)` after obtaining a page: it lists its bound helpers and protocol domains; connection-wide operations stay on `page.cdp`. Search large surfaces by name, then read the chosen operation in full:

    xdir(page, 'wait|click|text')
    doc(page.goto, page.fill_text)
    xdir(page.DOM, 'focus')
    doc(page.DOM.focus)

Use `cdp_search` to search protocol descriptions rather than names. Inspect returned tree/result types for their own APIs; displaying a tree shows page content, not method docs. Overview lines aren't full docs: read the bound callable, with its parameter comments and usage notes, before use. Those distinguish text insertion from key events, document readiness from application readiness, and protocol result fields from returned values. Browser commands are async; tree inspection is sync; context managers use `async with`.

# Read, act, verify

Understand a page through its accessibility tree; locate relevant content before expanding large subtrees; use observed node ids or known selectors rather than guessed coordinates; choose activation/input methods for the events the application needs. Wait for an observable result instead of sleeping and retrying; subscribe before an action when its events are the evidence. After a timed-out activation, inspect the page before considering another attempt: the action may already have happened.

Debugging: start the relevant console/network/websocket capture before reproducing. Dialog auto-answering changes page behaviour, so configure it deliberately, not as incidental logging setup. Use the captured evidence to tell a missing request from a missing UI update. Wrap each reproduction step in a rung from `Rungs(page)`: a failing rung names its step and carries the page's captured evidence; displaying the `Rungs` shows each step's time.

Design: compare computed styles with matching rules before changing CSS; try changes in the live page, verify them at the relevant viewport sizes, then copy them into the source stylesheet (page changes don't update project files).

In safepyrun, browser-control permission is the host's decision; importing this skill doesn't grant it; inspect `cdp_yolo` when that permission is explicitly needed.
"""

from fastcdp.core import *
from fastcdp.ext import *

__all__ = ['CDP', 'Page', 'ExtCDP', 'Rung', 'Rungs', 'cdp_search', 'cdp_conninfo', 'cdp_yolo']
