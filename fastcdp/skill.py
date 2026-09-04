r"""Work with Chrome through the DevTools Protocol: open pages, click and type, read a page as an accessibility tree, keep a log of console and network activity for debugging, and call any CDP command.

Everything is async: `await` every call (notebooks support top-level `await`).

# Connecting (prerequisites)

Which browser to drive is the user's decision, never a default: driving their everyday browser means acting inside their logged-in sessions, so NEVER do that without an explicit request naming it. Some users instead keep a dedicated "CDP Chrome" (option 4) logged in to exactly the accounts they're happy to automate, so a bare "do this in the browser" has three readings -- when the task needs real logins and the user hasn't said which browser, ask; when it doesn't, `launch` a fresh instance (option 2). Once the user *has* pointed at their everyday browser, the extension (option 1) is the best way in: nothing to click or approve, connected in a few seconds.

1. *The user's everyday Chrome via the fastcdp companion extension* -- the kernel listens, and the extension dials in:

        cdp = await ExtCDP.listen(timeout=40)

   This is how an agent works in the tab the user is looking at: `await cdp.active_page()` returns that tab as a driveable `Page`, `await cdp.pages` lists every tab, and `await cdp.attach_page(tid)` drives any of them. Filling a form in the user's live session and leaving them just the submit click is one connect and three calls. Tabs a client attached are detached when it disconnects, so no debug banner outlives the work. A timeout means the extension isn't installed or enabled. `chrome://` pages (including a fresh New Tab) can't be attached: when the user's active tab is one, `new_page()` your own tab instead of fighting it.

2. *Launch a fresh instance of the user's installed Chrome* (visible by default; `headless=True` for headless; `user_data_dir=` to override the default `~/.cache/fastcdp/profile`) -- zero prerequisites, but its own profile, not the user's:

        cdp = await CDP.launch()
        ...
        await cdp.quit()      # quits the browser; close() only drops the connection

   A second `launch` on the same profile dir connects to the already-running instance (`reuse=False` to make it raise instead); `quit()` when done. NB: `launch`, `remote` and `remote_page` are patched classmethods that `doc(CDP)` currently doesn't list.

3. *The user's everyday Chrome without the extension* (146+), after they enable **Allow remote debugging** in `chrome://inspect/#remote-debugging`:

        cdp = await CDP.connect()

   Chrome asks the user to approve each newly connecting client, so warn them a popup is coming. `connect` waits up to 60 seconds for approval. A `TimeoutError` during the websocket handshake usually means the popup wasn't answered in time: ask the user to watch for it and retry. `active_page()` skips `chrome://` and `devtools://` targets; create a new page when it returns `None`.

4. *A separate "debug Chrome"* -- a browser used only for automation, logged in to just what you want automated. Run `fastcdp-setup` once to create a "CDP Chrome" launcher (macOS app / Linux desktop entry / Windows shortcut) that starts it on port 9223 with its own profile; or start one by hand (since Chrome 136 a non-default profile dir is required):

        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
          --remote-debugging-port=9223 --user-data-dir=$HOME/.cache/fastcdp/cdp-chrome

   Then `cdp = await CDP.remote()` connects (no approval popups), and `page = await CDP.remote_page()` shortcuts to driving its focused tab. Both default to port 9223, matching the launcher; 9222 is avoided because a main browser with built-in debugging enabled (option 3) already holds it.

# Working with pages

`page = await cdp.new_page()` opens a tab and returns a `Page`: a thin proxy binding that tab's session onto everything `CDP` offers, so no `sid` threading is needed; `await cdp.attach_page(tid)` returns the same proxy for an existing tab, taking either id a `pages` row carries (integer `tabId` or hex target id); `await cdp.active_page()` drives the frontmost tab (the one the user is looking at). `doc(CDP)` shows the full helper inventory (navigation and waits, clicking/filling, screenshots, the debugging buffers); it all works on a `Page`. `eval` returns the expression's value as a Python object (JSON-serializable results only) and raises on a JS exception. Beyond the helpers, the *entire* protocol is exposed dynamically as `page.<domain>.<command>`; `doc()` any such method (e.g. `doc(page.dom.focus)`) for its protocol docs, and find commands with `cdp_search('querytext')` (whole-protocol description search) or `pyskills.xdir(page.css, 'style')` (filter one domain's command names). One shape note: a command result containing a single key is unwrapped, so e.g. `getWindowBounds` returns the bounds dict itself, one level less nesting than the protocol docs describe.

    page = await cdp.new_page()
    await page.goto('https://example.com')          # waits for load
    root = await page.ax_tree()                     # accessibility tree, markdown repr
    await page.fill_text(root.find_id('textbox', 'Customer name'), 'Jeremy')
    await page.click_and_wait(root.find_id('button', 'Submit order'))
    img  = await page.screenshot(full=True)
    await page.close()

`ax_tree()` is the main way to *read* a page. Pass `frame_id=` to read a child frame directly. On a page you already know, display the tree bare and use `find`/`find_id`/`find_all` (role and/or name substring) to target elements by backend node id. On an unfamiliar or large page, don't read the whole tree: `root.grep(pattern)` regex-searches every node name and shows one line per hit -- backend id, role, name, and ancestor path -- so it locates; then `hit.up()` climbs from a leaf to its enclosing widget and `node.view(depth=2)` renders just that subtree. grep to locate, view to read, find_id to act.

Choose activation semantics deliberately. `click(backend_id)` moves the real mouse before pressing and releasing, which hover and mouse-event behavior need. `tap(backend_id)` sends Chrome's trusted tap gesture without moving the mouse; use it when mouse movement is unreliable or hover is undesirable. `dom_click(backend_id)` calls the element's DOM `click()` method and does not produce trusted input. All three bound the whole action to five seconds. Never retry a timed-out activation automatically: inspect the resulting page first, because the action may already have happened.

Keyboard input has two levels. `fill_text(backend_id, text)` replaces a control's contents without key events. `press('Enter', mod=True)` sends a real `keydown`/`keyup` pair (modifier booleans: `ctrl`/`shift`/`alt`/`meta`, or `mod` for the platform primary), and `type(text)` presses each character, for UI that reacts per keystroke.

Waiting is built in -- never `sleep` and re-read. `goto` waits for `load` by default; pass `wait='idle'` only when initial requests must settle, or `wait=None` before an application-specific content wait. `click_and_wait` uses `click`, requires a top-frame navigation, and uses the same wait modes. Wrap `tap`, `dom_click`, or any other navigation action in `expect_navigation`, and an action that triggers an htmx request in `expect_htmx(path)`, which waits for that request's swap to settle; never try to wait for navigation after the action, because its events may already be gone. For content that changes *in place* (tab panels, htmx swaps, SPAs), activate it and then use `wait_for_ax(role, name, frame_id=...)`, `wait_for_text`, `wait_for_selector`, or `wait_for(js_expr)`. `set_content(html)` replaces the document wholesale -- the way to put fixture HTML in a page, since `data:` URLs can't be navigated to on the extension path (`goto` raises `net::ERR_ABORTED`).

Every CDP command also has the connection's `command_timeout` (10 seconds by default), so a reply lost during navigation cannot wedge the caller or kernel.

# Debugging an app

Call the `start_*` helpers right after creating the page -- CDP only delivers events from enablement on:

    await page.start_console(); await page.start_network(); await page.handle_dialogs()
    await page.goto('http://localhost:5001')
    await page.console(r'error:')                   # buffered logs + uncaught exceptions
    st,url,rid = first(await page.requests(r'api/'))
    await page.response_body(rid)
    page.dialogs                                    # dialogs seen (auto-answered)

Without `handle_dialogs`, a JS `alert`/`confirm` blocks its page (and whatever `eval` triggered it) indefinitely.

For tests against a live app, `Rung` names each step: a failure inside the context re-raises with the rung's name and `page.evidence()`, a report from whichever debugging buffers were started. `hover`/`sel_hover` engage CSS `:hover` and mouse events, and `sel_attr`/`sel_count` read an attribute or count matches by selector, and `sel_map`/`sel_attrs` map a JS function or attribute over every match.
`Rungs(page)` is the factory form: it binds the page once and logs each rung's duration, and its display is the timing profile.

# Live CSS and design iteration

Design tweaks iterate fastest in the live page, with no file writes and no reloads. Read computed values with `eval` and `getComputedStyle`; try a change by injecting a `<style>` tag (or setting `el.style`); read back, adjust, and copy into the real stylesheet once it looks right. `emulation.setDeviceMetricsOverride(width=390, height=844, deviceScaleFactor=2, mobile=True)` tests responsive layouts, `clearDeviceMetricsOverride` restores, and screenshots capture at the overridden size. That covers everything except *why* a style won, which computed values can't answer. `matched_styles` can:

    await page.matched_styles('table caption')            # every matching rule, cascade order, winners last
    await page.matched_styles(root.find_id('button'))     # same, straight from an ax find/grep hit

That is the DevTools Styles panel as a query: one line per rule with its origin (`user-agent` vs `regular`), selector, and declarations, and `.raw` on each row keeps the full protocol record. It takes a selector or an ax backend id, bridging the two id spaces (ax speaks *backend* ids; the `DOM`/`CSS` domains want front-end `nodeId`s, which `sel_node(sel)` resolves). `CSS.setStyleTexts` edits an existing rule in place, for when stacking override styles would muddy the experiment.

# Gotchas

- Unknown attribute names on `CDP`/`Page` currently become dynamic domain objects rather than raising `AttributeError`, so a typo'd helper name fails later as `'PageDomain' object is not callable`.
- In safepyrun sandboxes, run `cdp_yolo()` once to allow all fastcdp classes (it is *not* called at import: it opens up full browser control, which is a policy decision for the host).
"""

from fastcdp.core import *
from fastcdp.ext import *

__all__ = ['CDP', 'Page', 'ExtCDP', 'cdp_search', 'cdp_conninfo', 'cdp_yolo']
