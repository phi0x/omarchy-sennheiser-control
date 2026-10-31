# Changelog

## 0.1.1

- Stop recurring bulk HID/GAIA status queries during playback. A listening
  comparison was clean with polling paused and crackled when polling resumed;
  the fixed controller has remained clean in subsequent listening so far.
- Keep cached settings between explicit reads. Refresh on opening, requested
  refresh, control changes and new device connections. Passive USB enumeration
  and socket checks retain unplug detection and reconnect behavior.
- Keep local preset operations and plugin update checks free of additional
  device status queries.
- Add an on-demand plugin update check in Updates, using public stable GitHub
  Releases and the local manifest version. Show version comparisons, failure
  states, release notes and installation-specific update guidance. Mark Updates
  with a dot when a newer release is found.

Plugin updates are manual. Firmware installation remains unsupported. Hardware
reads and mocked tests do not establish firmware flashing or recovery safety.
All existing license, no-warranty and liability terms continue to apply.
