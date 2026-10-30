# Contributing

Issues and pull requests are welcome. Include the Omarchy version, headset and
dongle model, firmware versions, and steps to reproduce. Remove Bluetooth
addresses, device serials, broadcast passwords, tokens, and private desktop
content from logs and screenshots before sharing them.

The supported hardware is HDB 630 with BTD 700. Other Sennheiser devices may use
different protocols; do not send unverified commands to them. Firmware checks are
read-only. This project does not implement firmware flashing.

Run:

```
python -m unittest discover -s tests -v
node tests/test_ui_rules.js
```

The shared-controller integration tests need local Unix socket access.
For QML changes, validate against a matching installed Omarchy shell:

```
/usr/lib/qt6/bin/qmllint -I /usr/share/omarchy/shell Widget.qml HelpCard.qml
omarchy plugin validate .
```

Use mock transports for write-path tests. Describe any hardware testing precisely:
reading status does not validate a firmware write or update recovery. Keep hardware
writes serialized through the shared controller. Do not add another per-monitor
hardware worker or replay settings on reconnection.

Runtime user state is outside the checkout in XDG_STATE_HOME, XDG_CACHE_HOME and
XDG_RUNTIME_DIR. Do not commit it. Preserve all third-party license notices.
