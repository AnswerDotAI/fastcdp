# Release notes

<!-- do not remove -->

## 0.0.12

### New Features

- Add `expect_htmx` context manager for awaiting htmx swaps ([#20](https://github.com/AnswerDotAI/fastcdp/issues/20))


## 0.0.11

### New Features

- Drive child frames wherever Chrome renders them, and wait for the composited scroll before pointer events ([#19](https://github.com/AnswerDotAI/fastcdp/pull/19)), thanks to [@jph00](https://github.com/jph00)
- Add tap gesture, hover/frame helpers, `wait_for_new_page`, focus emulation for all pages, and per-frame `ax_tree` support ([#18](https://github.com/AnswerDotAI/fastcdp/issues/18))


## 0.0.10

### New Features

- Bound CDP commands and make navigation waits explicit ([#17](https://github.com/AnswerDotAI/fastcdp/pull/17)), thanks to [@jph00](https://github.com/jph00)


## 0.0.9

### New Features

- Add press/type keyboard input, hover and `sel_`* helpers, Rung test steps with evidence, in-flight request tracking for readiness waits ([#16](https://github.com/AnswerDotAI/fastcdp/issues/16))

### Bugs Squashed

- Handle missing page bodies in `wait_for_text` ([#15](https://github.com/AnswerDotAI/fastcdp/pull/15)), thanks to [@jph00](https://github.com/jph00)


## 0.0.8

### New Features

- Handle everyday Chrome approval and internal tabs ([#14](https://github.com/AnswerDotAI/fastcdp/pull/14)), thanks to [@jph00](https://github.com/jph00)
- Make navigation and text filling resilient ([#13](https://github.com/AnswerDotAI/fastcdp/pull/13)), thanks to [@jph00](https://github.com/jph00)
- Add docments to public API params, `sel_`* CSS helpers, `wait_for_frame`, `wait_for_selector` present flag, and `wait_for_text` sel arg ([#12](https://github.com/AnswerDotAI/fastcdp/issues/12))
- Add websocket frame capture: `start_ws`/`ws_frames` with WSFrame/WSFrames for inspecting htmx swaps over CDP ([#11](https://github.com/AnswerDotAI/fastcdp/issues/11))
- Add ax-tree orientation helpers (grep/view/up/path), `set_content`, `wait_for_ax`, `matched_styles`, and navigation error handling ([#10](https://github.com/AnswerDotAI/fastcdp/issues/10))
- Add type hints, refactor `active_page` to return Page, support hex target ids in ExtCDP.`attach_page`, and rewrite connection docs ([#9](https://github.com/AnswerDotAI/fastcdp/issues/9))
- Add instance reuse on launch, stale-port detection, `attach_page` for existing tabs, exception-raising eval ([#8](https://github.com/AnswerDotAI/fastcdp/issues/8))
- Replace httpbin.org with fast-http-bin.pla.sh across docs and notebooks ([#6](https://github.com/AnswerDotAI/fastcdp/pull/6)), thanks to [@RensDimmendaal](https://github.com/RensDimmendaal)


## 0.0.7

### New Features

- Add Chrome launch/quit, extension transport, debugging helpers, and setup launcher ([#7](https://github.com/AnswerDotAI/fastcdp/issues/7))


## 0.0.6

### New Features

- Add Chromium browser support alongside Chrome ([#5](https://github.com/AnswerDotAI/fastcdp/pull/5)), thanks to [@ncoop57](https://github.com/ncoop57)


## 0.0.5

### New Features

- Add remote()/`remote_page`()/`active_page`() for Chrome remote debugging via HTTP endpoint ([#3](https://github.com/AnswerDotAI/fastcdp/issues/3))


## 0.0.4

### New Features

- Refactor CDP connection to extract `cdp_conninfo` helper ([#2](https://github.com/AnswerDotAI/fastcdp/issues/2))


## 0.0.3

### New Features

- Add accessibility tree support, form interaction helpers, and network-idle wait ([#1](https://github.com/AnswerDotAI/fastcdp/issues/1))


## 0.0.2

- package json


## 0.0.1

- init release
