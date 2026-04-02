[app]
title = My Clicker
package.name = myclicker
package.domain = org.yourname

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3,ico

version = 1.0.0
requirements = python3,kivy==2.2.0
orientation = portrait
fullscreen = 1

p4a.source_dir =
p4a.bootstrap = sdl2

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.arch = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
