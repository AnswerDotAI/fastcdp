r"""Work with Chrome through the DevTools Protocol: inspect pages, interact with controls, and diagnose browser applications.

Choose the browser before connecting. Acting in an everyday browser uses the user's logged-in sessions. Do that only when the user has named that browser. If a task needs logins and the browser is unspecified, ask. Otherwise use a separate automation profile.

# Choose a connection

Use the companion extension (`ExtCDP`) for an explicitly requested everyday browser when available. Direct everyday-browser access (`CDP.connect`) requires the user to enable remote debugging and approve the connection popup. A dedicated debug browser uses `CDP.remote`; `fastcdp-setup` creates a launcher for it. For a separate automation profile, inspect `CDP.launch`.

Read the chosen connection method's docs before calling it. Once connected, inspect the connection to discover tab creation, attachment, and cleanup. Keep work in background tabs unless bringing a tab forward is part of the request. Do not close the user's tabs or quit their browser as routine cleanup. Read the relevant `close` or `quit` docs: tab ownership and connection ownership are different.

# Discover the actual object

Read `doc(page)` after obtaining a page. It lists this page's bound helpers and protocol domains. Connection-wide operations remain on `page.cdp`. Search large surfaces by name, then read the selected operation in full:

    xdir(page, 'wait|click|text')
    doc(page.goto, page.fill_text)
    xdir(page.DOM, 'focus')
    doc(page.DOM.focus)

Use `cdp_search` when you need to search protocol descriptions rather than names. Inspect returned tree/result types for their own APIs; displaying a tree shows page content, not method documentation.

Overview lines are not full operation docs. Read the actual bound callable before using it, including parameter comments and usage notes. Those details distinguish text insertion from key events, document readiness from application readiness, and protocol result fields from returned values. Browser commands are async; tree inspection is synchronous, and context managers use `async with`.

# Read, act, verify

Use the accessibility tree to understand a page. Locate relevant content before expanding large subtrees. Use observed node ids or known selectors rather than guessed coordinates. Choose activation and input methods for the events the application needs.

Wait for an observable result instead of sleeping and retrying. Subscribe before actions when their events are the evidence. After a timed-out activation, inspect the page before considering another attempt: the action may already have happened.

For debugging, start the relevant console, network, or websocket capture before reproducing the problem. Dialog auto-answering changes page behavior; configure it deliberately, not as incidental logging setup. Use the captured evidence to distinguish a missing request from a missing UI update.

For design work, compare computed styles with matching rules before changing CSS. Try changes in the live page, verify them at the relevant viewport sizes, then copy the verified change into the source stylesheet. Temporary page changes do not update project files.

In safepyrun, browser-control permission is a host decision. Importing this skill does not grant it; inspect `cdp_yolo` when that permission is explicitly needed.
"""

from fastcdp.core import *
from fastcdp.ext import *

__all__ = ['CDP', 'Page', 'ExtCDP', 'Rung', 'Rungs', 'cdp_search', 'cdp_conninfo', 'cdp_yolo']
