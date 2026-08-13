[app]
title = Car Trump Battle
package.name = cartrumpbattle
package.domain = org.nithvin

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json
source.exclude_dirs = .git,.github,.buildozer,.venv,server

version = 1.0

requirements = python3,kivy,websocket-client

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 24
android.archs = arm64-v8a

android.permissions = INTERNET
android.debug_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 1
