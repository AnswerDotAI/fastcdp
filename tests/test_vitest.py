import asyncio
from pathlib import Path
from fastcdp.vitest import Vitest


def test_vitest_browser():
    async def story():
        async with Vitest(Path(__file__).resolve().parents[1]) as vt:
            result = await vt.run()
            assert result.success, vt.output
            assert result.testResults[0].assertionResults[0].status == 'passed'
            target = vt.page.t
            failed = await vt.run(env={'FASTCDP_TEST_FAILURE': '1'})
            assert not failed.success
            failure = failed.testResults[0].assertionResults[-1]
            assert failure.status == 'failed' and 'Expected heading' in failure.failureMessages[0]
            assert vt.page.t == target
            frame = await vt.page.wait_for_child_frame('iframeId=')
            assert 'Inspect this failure' in str(await vt.page.ax_tree(frame_id=frame.id))
            cdp = vt.cdp
        assert not cdp.is_open
    asyncio.run(story())
