# Agent guide

## Start here

This is Sennheiser Control, an unofficial Omarchy Quattro top-bar plugin for
HDB 630 headphones and the BTD 700 dongle. The public repository is
`phi0x/omarchy-sennheiser-control`; the permanent public plugin ID is
`phi0x.sennheiser`.

Before changing code:

- Check `git status`, the current branch, and recent commits. Preserve unrelated
  user changes.
- Read `README.md` and `CONTRIBUTING.md`. Consult `ROADMAP.md` and
  `docs/firmware-research.md` for firmware work, and `SECURITY.md` and
  `THIRD_PARTY.md` when changing access, networking, or borrowed code.
- Inspect current files and live configuration as needed. This file records
  durable guidance, not the current device state, marketplace approval, or a
  substitute for checking what is installed.

## Architecture

- `Widget.qml`: bar icon, native Omarchy `KeyboardPanel`, tabs, settings and EQ
  draft editors. Uses `qs.Ui`, `qs.Commons`, and the current desktop theme.
- `Section.qml`, `HelpCard.qml`, `HelpData.js`: grouped settings, expandable
  explanations and conceptual diagrams.
- `UiRules.js`: setting dependencies and active/inactive EQ descriptions.
- `backend/client.py`: per-widget JSON-lines proxy to the shared controller.
- `backend/shared.py`: private Unix-socket broker with one hardware worker shared
  across monitors. All widgets receive the same status.
- `backend/service.py`: serialized requests, polling, reads and explicit writes.
- `backend/dongle.py`: BTD 700 HID protocol. `backend/headphones.py`: HDB 630
  GAIA/RFCOMM protocol. Direct headphone control uses the computer's Bluetooth
  adapter separately from dongle audio and occupies another multipoint slot.
- `backend/reconnect.py`: remembered connection target and bounded retry delays.
- `backend/presets.py`: local parametric EQ drafts.
- `backend/firmware.py`: on-demand official HTTPS catalog checks only.
- `backend/plugin_updates.py`: on-demand public GitHub Release checks using the
  local manifest version. No credentials, automatic checks or installation.
- `backend/build_helper.py`, `native/sdp-channel.c`: compile and cache the SDP
  discovery helper locally. Do not commit the generated executable.
- `tests/`: mock protocol, validation, controller, reconnect and UI-rule checks.

## Behavior to preserve

- Keep one shared hardware controller, including on multiple monitors. Do not
  start independent hardware workers for each popup or monitor. Avoid launching
  standalone hardware probes while the shared controller owns the devices.
- Idle maintenance uses host-side USB enumeration and passive socket checks,
  without bulk HID/GAIA status requests. Repeated status queries caused playback
  crackles in a listening comparison. Read settings on open, explicit refresh,
  control changes, or a new connection; keep local preset operations free of
  device queries. Never replay failed writes during reconnection. Keep hardware
  commands serialized through the controller.
- Validate an entire setting request before writing. Multi-command writes can
  still partially succeed; report that possibility and invalidate affected data
  so the user can read it again.
- Draft edits survive status polls. Loading a local preset does not apply it to
  the headphones. Explicit apply/save controls govern hardware writes.
- Graphic and parametric EQ are separate playback modes. Keep draft editors
  usable while inactive and explain their status. Preserve dependencies in
  `UiRules.js`; disabled settings retain accessible help.
- Transparency applies on slider release. Routine setting changes must not
  insert/remove busy or status rows and make the panel jump or flash.
- Keep tabs and the footer fixed while settings scroll. Preserve the dedicated
  right-hand scrollbar gutter: the bar is visible when content overflows,
  supports dragging and track clicks, and has a usable minimum thumb size.
  It must never cover help icons or settings.
- Tab shading identifies selection. Draw button focus rings for keyboard
  navigation (`visualFocus`), rather than automatic focus on panel opening.
- Firmware installation is not implemented. Never describe catalog checks or
  mocked transfers as successful flashing. Keep unvalidated flashing experiments
  out of the default branch; follow the roadmap's model-specific validation and
  recovery requirements before offering installation.

## Verification

Run checks appropriate to the change. Backend or protocol changes normally need:

```sh
python -m unittest discover -s tests -v
node tests/test_ui_rules.js
bash -n install.sh install-device-access.sh
```

Shared-controller tests need local Unix sockets. Helper build tests need GCC and
Bluetooth development headers. Report environment limitations accurately.

For QML changes, use a matching installed Omarchy shell:

```sh
/usr/lib/qt6/bin/qmllint -I /usr/share/omarchy/shell Widget.qml HelpCard.qml
omarchy plugin validate .
```

Inspect the live popup for layout, focus, scrolling and draft preservation when
relevant. Use mock transports for write-path tests. Do not change the user's
audio settings merely to test visuals or capture media. Distinguish mock tests,
hardware reads, and hardware writes in reports. Documentation-only changes need
link/content review and `git diff --check`, not hardware access.

## Local deployment

Source edits do not necessarily update the installed plugin. Before deploying,
inspect `~/.config/omarchy/shell.json` and installed plugin manifests. A development
machine may still use an older plugin ID; do not assume its installed directory
matches the public ID, create a second active copy, or rewrite its bar layout
incidentally. Preserve the installed identity unless migration is requested.

Follow the current session's authorization for deployment. Standard installs use
Omarchy's plugin commands; development installs use `install.sh` as documented.
The installer refuses to overwrite an unrelated plugin. Inspect any differences
before replacing installed files. Back up local configuration when changing it.
Never modify packaged files under `/usr/share/omarchy/`.

Plugin code normally hot-reloads. If the shell still serves cached QML after
`omarchy-shell shell rescanPlugins`, `omarchy restart shell` may be necessary.
Do not use configuration-reset commands as a routine reload.

The optional `./install.sh --device-access` uses `pkexec` for a product-scoped udev
rule granting the active desktop user access. Keep the controller unprivileged;
do not replace this with broad permissions or passwordless privilege rules.

## Public repository and captures

- Treat tracked documentation, including this file, as public. Exclude private
  keys, tokens, personal email addresses, real Bluetooth addresses, serials, broadcast
  passwords, raw status dumps, personal paths and private desktop content.
- User state belongs in XDG state/cache/runtime locations, outside the checkout.
  Do not commit connection targets, local presets, logs, packet captures, vendor
  firmware packages, or built helpers. Use synthetic addresses in fixtures.
- Check the repository's Git author configuration before publishing commits;
  preserve the maintainer's GitHub privacy email rather than introducing a
  personal address.
- `docs/media/` contains cropped real popup captures and an animated WebP;
  root `preview.png` is the marketplace preview. Refresh relevant media when
  changing visible behavior. Inspect every published view for private content
  and accidental desktop exposure, especially when the popup changes height.
  Strip image metadata. Keep raw captures and temporary recording tools outside
  the repository. Help diagrams are illustrations, not acoustic measurements.

## License and publication

Preserve the custom source-available `LICENSE.md`: forks, modification, commercial
use and genuine paid services are allowed; sale or paywalling of the application
itself is restricted. Do not call it OSI-approved open source or replace it with
a different license incidentally. Preserve the no-warranty and liability notices.
`backend/headphones.py` remains MIT; `backend/dongle.py` remains LGPL-2.1-only.
Retain their notices and applicable third-party terms.

The initial marketplace submission is
<https://github.com/omacom/omarchy-plugin-marketplace/issues/13437>.
Check its current state before updating it. For a pending initial submission,
update the existing issue rather than opening a duplicate. For an already-listed
plugin, follow the marketplace's current verification/update process. Repository
pushes, automated validation and maintainer approval are distinct; do not claim a
commit is listed or verified without checking. Keep the public plugin ID stable
and follow `ROADMAP.md` for release versioning and review.
