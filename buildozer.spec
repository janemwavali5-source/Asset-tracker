[app]
title = Asset Tracker
package.name = assettracker
package.domain = org.assettracker

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas

version = 1.0.0
requirements = python3,kivy,android

orientation = portrait
fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
