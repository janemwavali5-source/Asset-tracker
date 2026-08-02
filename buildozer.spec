[app]

# App title
title = Asset Tracker

# Package name (one word, no spaces)
package.name = assettracker

# Package domain
package.domain = org.assettracker

# Where your source code is
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas

# App version
version = 1.0.0

# Requirements
requirements = python3,kivy,sqlite3,android

# Orientation
orientation = portrait
fullscreen = 0

# Android permissions (for backup/export)
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Android settings
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1

