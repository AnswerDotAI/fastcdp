r"""Drive Chrome via the DevTools Protocol: navigate, click and fill pages, read them as an LLM-friendly accessibility tree, buffer console/network/dialog activity for debugging, and call any raw CDP command.

Everything is async: `await` every call (notebooks support top-level `await`).

# Connecting (prerequisites)

Which browser to drive is the user's decision, never a default: driving their everyday browser means acting inside their logged-in sessions, so NEVER do that without an explicit request naming it. Some users instead keep a dedicated "CDP Chrome" (option 4) logged in to exactly the accounts they're happy to automate, so a bare "do this in the browser" has three readings -- when the task needs real logins and the user hasn't said which browser, ask; when it doesn't, `launch` a fresh instance (option 2). Once the user *has* pointed at their everyday browser, the extension (option 1) is the best way in: nothing to click or approve, connected in a few seconds.

1. *The user's everyday Chrome via the fastcdp companion extension* -- the kernel listens, and the extension dials in:

        cdp = await ExtCDP.listen(timeout=40)

   This is how an agent works in the tab the user is looking at: `await cdp.active_page()` returns that tab as a driveable `Page`, `await cdp.pages` lists every tab, and `await cdp.attach_page(tid)` drives any of them. Filling a form in the user's live session and leaving them just the submit click is one connect and three calls. Tabs a client attached are detached when it disconnects, so no debug banner outlives the work. A timeout means the extension isn't installed or enabled.

2. *Launch a fresh instance of the user's installed Chrome* (visible by default; `headless=True` for headless; `user_data_dir=` to override the default `~/.cache/fastcdp/profile`) -- zero prerequisites, but its own profile, not the user's:

        cdp = await CDP.launch()
        ...
        await cdp.quit()      # quits the browser; close() only drops the connection

   A second `launch` on the same profile dir connects to the already-running instance (`reuse=False` to make it raise instead); `quit()` when done. NB: `launch`, `remote` and `remote_page` are patched classmethods that `doc(CDP)` currently doesn't list.

3. *The user's everyday Chrome without the extension* (146+), after they enable **Allow remote debugging** in `chrome://inspect`:

        cdp = await CDP.connect()

   Chrome asks the user to approve each newly connecting client, so warn them a popup is coming. A `TimeoutError` during the websocket handshake usually means the popup wasn't answered in time (~10s): ask the user to watch for it and retry.

4. *A separate "debug Chrome"* -- a browser used only for automation, logged in to just what you want automated. Run `fastcdp-setup` once to create a "CDP Chrome" launcher (macOS app / Linux desktop entry / Windows shortcut) that starts it on port 9223 with its own profile; or start one by hand (since Chrome 136 a non-default profile dir is required):

        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
          --remote-debugging-port=9223 --user-data-dir=$HOME/.cache/fastcdp/cdp-chrome

   Then `cdp = await CDP.remote()` connects (no approval popups), and `page = await CDP.remote_page()` shortcuts to driving its focused tab. Both default to port 9223, matching the launcher; 9222 is avoided because a main browser with built-in debugging enabled (option 3) already holds it.

# Working with pages

`page = await cdp.new_page()` opens a tab and returns a `Page`: a thin proxy binding that tab's session onto everything `CDP` offers, so no `sid` threading is needed; `await cdp.attach_page(tid)` returns the same proxy for an existing tab, taking either id a `pages` row carries (integer `tabId` or hex target id); `await cdp.active_page()` drives the frontmost tab (the one the user is looking at). `doc(CDP)` shows the full helper inventory (navigation and waits, clicking/filling, screenshots, the debugging buffers); it all works on a `Page`. `eval` returns the expression's value as a Python object (JSON-serializable results only) and raises on a JS exception. Beyond the helpers, the *entire* protocol is exposed dynamically as `page.<domain>.<command>`; `doc()` any such method (e.g. `doc(page.dom.focus)`) for its protocol docs, and find commands with `cdp_search('querytext')`. One shape note: a command result containing a single key is unwrapped, so e.g. `getWindowBounds` returns the bounds dict itself, one level less nesting than the protocol docs describe.

    page = await cdp.new_page()
    await page.goto('https://example.com')          # waits for load + network idle
    root = await page.ax_tree()                     # accessibility tree, markdown repr
    await page.fill_text(root.find_id('textbox', 'Customer name'), 'Jeremy')
    await page.click_and_wait(root.find_id('button', 'Submit order'))
    img  = await page.screenshot(full=True)
    await page.close()

`ax_tree()` is the main way to *read* a page: display it bare, and use `find`/`find_id`/`find_all` (role and/or name substring) to target elements by backend node id.

# Debugging an app

Call the `start_*` helpers right after creating the page -- CDP only delivers events from enablement on:

    await page.start_console(); await page.start_network(); await page.handle_dialogs()
    await page.goto('http://localhost:5001')
    await page.console(r'error:')                   # buffered logs + uncaught exceptions
    st,url,rid = first(await page.requests(r'api/'))
    await page.response_body(rid)
    page.dialogs                                    # dialogs seen (auto-answered)

Without `handle_dialogs`, a JS `alert`/`confirm` blocks its page (and whatever `eval` triggered it) indefinitely.

# Gotchas

- Unknown attribute names on `CDP`/`Page` currently become dynamic domain objects rather than raising `AttributeError`, so a typo'd helper name fails later as `'PageDomain' object is not callable`.
- In safepyrun sandboxes, run `cdp_yolo()` once to allow all fastcdp classes (it is *not* called at import: it opens up full browser control, which is a policy decision for the host).
"""

from fastcdp.core import *
from fastcdp.ext import *

__all__ = ['CDP', 'Page', 'ExtCDP', 'cdp_search', 'cdp_conninfo', 'cdp_yolo']
