# Security

This is an unofficial, experimental Omarchy plugin. It runs with the desktop
user's permissions inside Omarchy's shell and starts a local Python controller.
Review the source before installation. The backend uses a private Unix socket
and no network listener.

The only network feature is an explicitly requested check of Sennheiser's official
firmware catalog using verified HTTPS. It sends public product identifiers, not
Bluetooth addresses or device serials. Firmware images are not downloaded or
flashed. External updater buttons open official product/software pages.

Broadcast passwords are forwarded locally to the dongle and are not returned in
shared status or written to the preset library. The active desktop user can
inspect their own process memory; this is not a separate security boundary.

The optional udev rule grants only the active local user HID access to the BTD 700
USB product identifier 3542:3001. The controller does not run as root.

Do not include secrets or identifying device data in public issues. For a
security-sensitive report, use the repository's private vulnerability reporting
feature when available; avoid publishing exploit details before a fix is ready.
