# Roadmap

These are potential future improvements, not shipped capabilities or promised
release dates. The current app controls the HDB 630 and BTD 700 and checks the
official firmware catalog. It does **not** download or install firmware.

## Native BTD 700 firmware installation

Status: investigation. A separate update-related HID interface has been observed,
but a complete BTD 700 update has not been implemented or validated.

- Confirm the BTD 700-specific update protocol, hardware/firmware variant matching,
  and official image format; do not assume a BTD 600 updater is interchangeable.
- Obtain images from verified official sources and validate their integrity,
  authenticity where supported, and compatibility before any device write.
- Implement and test acknowledgements, progress reporting, verification, reboot,
  resume and recovery for the complete transfer state machine.
- Validate a real supported version transition and read back the installed
  version afterward. Catalog checks and mocked transports do not establish that
  flashing works on hardware.

## Native HDB 630 firmware installation

Status: investigation. The official catalog exposes encrypted packages with
language-specific firmware and voice-prompt variants.

- Investigate the official model-specific OTA flow, encrypted package handling,
  language selection, transport framing and hardware compatibility checks.
- Establish the transfer, verification, restart/reconnect and recovery behavior.
- Validate updates on the HDB 630 itself. Other Sennheiser or GAIA devices may use
  different procedures and are not automatically supported.

The existing [firmware investigation](docs/firmware-research.md) records the
verified observations and remaining protocol questions.

## Update experience, once native flashing is validated

- Show the exact device, installed version, target release and update source
  before the user explicitly starts an installation.
- Check relevant battery, power, connection and device-compatibility requirements.
- Give the updater exclusive device access through the shared controller, so
  another monitor, status poll or control change cannot interfere with flashing.
- Report progress and recovery instructions. Offer cancellation only at stages
  where the verified protocol permits it.
- Keep firmware checks available independently of installation support; a failed
  check must never be presented as proof that firmware is current.

## Other possible follow-up work

- Additional hardware compatibility testing and clearer capability detection.
- Preset import/export and further UI/accessibility improvements based on feedback.

These are candidates for future work, not guarantees that they will be implemented.

## Releasing improvements after publication

Publishing the repository or obtaining a marketplace listing does not freeze
the project. Future improvements can be released from the same repository and
plugin ID (`phi0x.sennheiser`).

1. Develop experimental features on a separate branch. Keep unvalidated flashing
   experiments out of the default branch used by normal installations.
2. Add focused tests, complete relevant hardware validation, and document exactly
   what was tested and what remains unsupported.
3. Merge a ready feature, bump the version in `manifest.json`, update the README,
   and publish a stable GitHub Release tagged `vMAJOR.MINOR.PATCH`, with notes
   describing behavior changes and limitations. The in-app plugin checker uses
   published Releases; a Git push or bare tag alone does not advertise an update.
4. If the plugin is listed in the marketplace, use its [verification/update
   process](https://github.com/omacom/omarchy-plugin-marketplace/blob/main/VERIFICATION.md)
   to request review and publication of the exact new commit. An upstream push
   alone does not grant marketplace approval to that new commit.
5. Users with a standard Git-managed installation can update through Omarchy:

   ```bash
   omarchy plugin update phi0x.sennheiser
   ```

Omarchy's Git update and marketplace snapshot review are separate processes.
The standard update command obtains current upstream code; it should not be
represented as installation of a marketplace-pinned verified snapshot. A new
repository or listing is not needed for normal feature updates.

All existing license terms, third-party notices, no-warranty statements and
liability limitations continue to apply. No warranty of update success or device
recovery is implied by this roadmap.
