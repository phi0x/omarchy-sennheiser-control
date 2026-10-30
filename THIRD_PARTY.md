Protocol references inspected when implementing this app:

* sobalap/btd700ctl, commit 747f3d6bcac91bdb36872038225e06eebc93f07a
  https://github.com/sobalap/btd700ctl — LGPL-2.1.
  The Python HID transport uses its protocol map and implementation as a reference.
  As a conservative licensing choice, backend/dongle.py is distributed under
  LGPL-2.1-only, including our additions. Its license is included in licenses/.
* hatemosphere/hdb630-control-macos, commit af0a23059f33f7b6ebe4de62e9af351116fc20ee
  https://github.com/hatemosphere/hdb630-control-macos — MIT.
  GAIA framing, command IDs, PEQ encodings and bounds informed the Python port.
  backend/headphones.py, including our additions, is distributed under MIT.
  See licenses/hdb630-MIT.txt for upstream notice.

The widget imports the installed Omarchy shell's shared UI components at runtime.
This app is unofficial and is not affiliated with Sennheiser or Sonova.

Additional research references (not bundled as executable code):

* DuroCodes/btd700 — https://github.com/DuroCodes/btd700
  Used to cross-check BTD 700 broadcast framing and field lengths.
* hhh2210/btd600-fw — https://github.com/hhh2210/btd600-fw
  Used to locate and inspect the official firmware metadata catalog and to compare
  update interfaces. Its BTD 600 flashing implementation is not included.

Omarchy and its QML components, hidapi, BlueZ/libbluetooth, Python, python-dbus,
GCC, and installed fonts remain separately installed dependencies under their own
licenses. No vendor updater, SDK, firmware image, encryption key, font file, or
Sennheiser logo is bundled. The C helper links to the system libbluetooth;
its source is included, and no prebuilt binary is distributed in this repository.

Any custom no-resale condition on the rest of this application does not restrict
rights granted by the LGPL or MIT licenses for the components identified above.
