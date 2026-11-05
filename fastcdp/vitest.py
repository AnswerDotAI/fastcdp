"""Run Vitest against an existing Chrome through fastcdp

`Vitest` owns the test runner and its tabs. It connects to CDP Chrome on port 9223 unless you pass an existing `CDP` connection. It never launches or quits Chrome.

Install the provider in your JavaScript project with `@fastcdp/vitest` and its `vitest` and `@vitest/browser` peers. In a local checkout, use a `file:` dependency pointing at this repository. Configure Browser Mode with `provider: fastcdp()` from `@fastcdp/vitest` and one `{ browser: 'chromium' }` instance.

Use ordinary `vitest-browser-svelte` rendering, Vitest locators and `expect.element`. Clicks, filling, typing, modifier shortcuts and Tab use native Chrome input. Holding non-modifier keys and unsupported action options raise errors. The provider does not install or launch a browser.

`run` accepts the same filename filters as Vitest. Its result contains `success`, `testModules` and `unhandledErrors`. Each module contains test names, result states, diagnostics and assertion errors. Runner output is in `output`. Repeating `run` reuses the owned tab. The last component remains available for inspection until `close`.

```python
from fastcdp.vitest import Vitest

async with Vitest('/path/to/svelte-project') as vt:
    result = await vt.run()
    result
    await vt.page.screenshot()
```
"""

__all__ = ['Vitest']

from fastcore.utils import *
from .core import CDP
from .ext import ExtChannel
from importlib.resources import files
from tempfile import TemporaryDirectory
import asyncio, contextlib, json, secrets

class Vitest:
    "Run browser tests with fastcdp; retain the last test page until `close`."
    def __init__(self,
        root:str|Path='.', # JavaScript project containing the Vitest config and dependencies
        cdp:CDP=None, # Existing connection; otherwise connect to CDP Chrome on 9223
    ):
        self.root,self.cdp,self._owned = Path(root).resolve(),cdp,cdp is None
        self.page,self._proc = None,None

    async def __aenter__(self):
        if self.cdp is None: self.cdp = await CDP.remote()
        return self

    async def __aexit__(self, *exc): await self.close()

    async def close(self):
        "Close the owned test tab and connection, leaving Chrome running."
        if self.page: await self.page.close()
        if self._owned and self.cdp: await self.cdp.close()

    async def run(self,
        *filters:str, # Standard Vitest test-file filters
        env:dict=None, # Additional environment, e.g. the app's Rustygate URL
        timeout:float=60, # Seconds to wait for the Node runner; shutdown gets another five seconds
    ):
        "Return structured Vitest results, including failed assertions and unhandled errors."
        if self._proc is not None: raise RuntimeError('A Vitest run is already active')
        if self.cdp is None: self.cdp = await CDP.remote()
        token = secrets.token_urlsafe()
        chan = await ExtChannel.listen(port=0, token=token)
        pump = asyncio.create_task(self._commands(chan))
        try:
            with TemporaryDirectory(prefix='fastcdp-vitest-') as tmp:
                report = Path(tmp)/'results.json'
                run_env = {**os.environ, **(env or {}), 'FASTCDP_VITEST': f'ws://127.0.0.1:{chan.port}/?token={token}'}
                self._proc = await asyncio.create_subprocess_exec('node', str(files('fastcdp')/'vitest-runner.mjs'),
                    str(self.root), str(report), *filters, cwd=self.root, env=run_env,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
                comm = asyncio.create_task(self._proc.communicate())
                try:
                    out,_ = await asyncio.wait_for(asyncio.shield(comm), timeout)
                    self.output = out.decode()
                    if not report.exists(): raise RuntimeError(self.output)
                    return dict2obj(report.read_json())
                finally:
                    if self._proc.returncode is None:
                        self._proc.terminate()
                        try: await asyncio.wait_for(self._proc.wait(), 5)
                        except TimeoutError:
                            self._proc.kill()
                            await self._proc.wait()
                    out,_ = await comm
                    self.output = out.decode()
        finally:
            self._proc = None
            pump.cancel()
            with contextlib.suppress(asyncio.CancelledError): await pump
            await chan.close()

    async def _commands(self, chan):
        while True:
            msg = await chan.events.get()
            try: await chan.send(id=msg.id, result=await self._action(msg))
            except Exception as e: await chan.send(id=msg.id, error=f'{type(e).__name__}: {e}')

@patch
async def _node(self:Vitest, msg, target):
    p = self.page
    options = {k:v for k,v in (msg.get('options') or {}).items() if k in ('timeout','strict')}
    expr = f"""[...document.querySelectorAll('iframe[data-vitest]')]
        .find(f => new URL(f.src).searchParams.get('iframeId') === {json.dumps(msg.testPath)})
        .contentWindow.__fastcdp_find({json.dumps(target['selector'])}, {json.dumps(options)})"""
    r = await p.runtime.evaluate(expression=expr, awaitPromise=True)
    if 'exceptionDetails' in r:
        e = r['exceptionDetails']
        raise RuntimeError(e.get('exception', {}).get('description', e['text']))
    obj = r['objectId']
    try: return (await p.DOM.describeNode(objectId=obj))['backendNodeId']
    finally: await p.runtime.releaseObject(objectId=obj)

@patch
async def _keyboard(self:Vitest, actions, unreleased=(), auto_close=False):
    modifiers = ('Alt','Control','Meta','Shift')
    pressed = set(unreleased)
    p = self.page
    def flags(): return dict(alt='Alt' in pressed, ctrl='Control' in pressed, meta='Meta' in pressed, shift='Shift' in pressed)
    async def modifier(key, down):
        if down: pressed.add(key)
        else: pressed.discard(key)
        await p.press(key, down=down, **flags())
    for a in actions:
        key = a['keyDef']['key']
        if key in ('\n','\r'): key = 'Enter'
        if key in modifiers:
            if key in pressed: await modifier(key, False)
            if not a['releasePrevious']:
                await modifier(key, True)
                if a['releaseSelf']: await modifier(key, False)
            continue
        if not a['releaseSelf'] or a['releasePrevious']: raise ValueError('Holding non-modifier keys is not supported')
        for _ in range(a['repeat']):
            await p.press(key, **flags())
    if auto_close:
        for key in tuple(pressed): await modifier(key, False)
    return dict(unreleased=list(pressed))

@patch
async def _action(self:Vitest, m):
    if m.action == 'open':
        if self.page is None: self.page = await self.cdp.new_page(background=True)
        self.url = m.url
        await self.page.network.enable()
        await self.page.network.setCacheDisabled(cacheDisabled=True)
        await self.page.goto(m.url)
        return
    p = self.page
    if m.action == 'viewport':
        return await p.emulation.setDeviceMetricsOverride(width=m.width, height=m.height, deviceScaleFactor=1, mobile=False)
    if m.action == 'keyboard': return await self._keyboard(m.actions, m.unreleased)
    if m.action == 'cleanup': return await self._keyboard([], m.unreleased, auto_close=True)
    if m.action == 'tab': return await p.press('Tab', shift=m.get('shift', False))
    target = await self._node(m, m.get('target') or dict(selector='body'))
    options = m.get('options') or {}
    if m.action == 'click': return await p.click(target, timeout=options.get('timeout', 5000)/1000)
    if m.action == 'hover': return await p.hover(target, timeout=options.get('timeout', 5000)/1000)
    if m.action in ('fill', 'clear'): return await p.fill_text(target, m.get('text', ''))
    if m.action == 'type':
        if not options.get('skipClick'): await p.DOM.focus(backendNodeId=target)
        return await self._keyboard(m.actions, options.get('unreleased', []), not options.get('skipAutoClose', False))
    if m.action == 'screenshot':
        box = (await p.DOM.getBoxModel(backendNodeId=target))['border']
        xs,ys = box[::2],box[1::2]
        return await p.page.captureScreenshot(clip=dict(x=min(xs), y=min(ys), width=max(xs)-min(xs), height=max(ys)-min(ys), scale=1),
            captureBeyondViewport=True)
    raise ValueError(f'Unsupported fastcdp action: {m.action}')
