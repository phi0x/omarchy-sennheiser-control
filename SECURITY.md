# Security

This is an unofficial, experimental Omarchy plugin. It runs with the desktop
user's permissions inside Omarchy's shell and starts a local Python controller.
Review the source before installation. The backend uses a private Unix socket
and no network listener.

Network access happens only for explicitly requested version checks over verified
HTTPS: Sennheiser's official firmware catalog, and the public GitHub Releases API
for this plugin. Firmware checks send public product identifiers, not Bluetooth
addresses or device serials. Plugin checks require no GitHub credentials and fetch
release metadata only. No firmware images or plugin packages are downloaded or
installed. External buttons open official software pages or this project's release
notes. A failed check is never reported as an up-to-date result.

Broadcast passwords are forwarded locally to the dongle and are not returned in
shared status or written to the preset library. The active desktop user can
inspect their own process memory; this is not a separate security boundary.

The optional udev rule grants only the active local user HID access to the BTD 700
USB product identifier 3542:3001. The controller does not run as root.

Do not include secrets or identifying device data in public issues. For a
security-sensitive report, use the repository's private vulnerability reporting
feature when available; avoid publishing exploit details before a fix is ready.

## No warranty or guaranteed recovery

This experimental software is provided as is, at the user's risk. No warranty of
compatibility, reliability, hardware safety, or recovery is made. Authors and
contributors exclude liability, including for equipment damage, data loss and
downtime, to the maximum extent permitted by applicable law. See the project
license for the complete terms. Mandatory legal protections are not waived.
