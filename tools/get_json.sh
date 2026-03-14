#!/usr/bin/env bash
cd "$(dirname "$0")"/../fastcdp

wget https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/master/json/browser_protocol.json
wget https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/master/json/js_protocol.json

