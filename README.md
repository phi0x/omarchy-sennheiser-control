# Sennheiser Control for Omarchy

An unofficial, experimental Omarchy top-bar widget for Sennheiser BTD 700 and HDB 630. Click the headphones icon
next to the audio widget. Uses Omarchy's popup, theme and focus handling.
Device control stays local. On-demand firmware checks contact Sennheiser’s official catalog.

> **NO WARRANTY — USE AT YOUR OWN RISK.** This experimental, unofficial software
> is provided “as is,” without warranties of any kind. To the maximum extent
> permitted by applicable law, its authors and contributors accept no liability
> for device or computer damage, data loss, downtime, lost profits, or other
> claims or losses arising from its use, modification, or distribution. No
> compatibility, reliability, or recovery outcome is guaranteed. The license
> contains the full disclaimer; mandatory legal rights are not excluded.

## Install or update

Requires Omarchy Quattro's Quickshell plugin system on Linux, Python 3.12+,
python-dbus, bluez, bluez-libs, bluez-utils, hidapi and gcc. Node is used only
for a development test. Install dependencies through Omarchy:

```
omarchy pkg add python python-dbus bluez bluez-libs bluez-utils hidapi gcc
```

Use Omarchy's standard plugin manager:

```
omarchy plugin add https://github.com/phi0x/omarchy-sennheiser-control.git --enable
```

The first direct headphone connection compiles the small SDP discovery helper
from the included C source into the user's cache. No prebuilt binary is bundled
and no root access is used for compilation or device control.

The dongle also needs a one-time device-access rule. In the installed plugin:

```
cd ~/.config/omarchy/plugins/phi0x.sennheiser
./install.sh --device-access
```

That command opens a system authentication dialog to install a udev rule scoped
to USB ID 3542:3001. Only the active desktop user receives HID access. Replug the
dongle if permissions do not change immediately. The controller runs unprivileged.

For development from a separate checkout, `./install.sh` builds the helper and
copies the plugin into user configuration, backing up shell.json before adding
the widget. It refuses to overwrite an unrelated plugin directory. Re-run to
deploy source edits; if the shell caches old QML, use `omarchy restart shell`.
Standard Git-managed installs update through `omarchy plugin update phi0x.sennheiser`.

## Using it

Dongle: live firmware, codec, stream state, bit depth and link sample rate;
audio mode, transport and codec selection from the reported supported mask.
Apply buttons make changes; polling does not alter settings.

Headphones: put HDB 630 in pairing mode, then choose Headphones → Search.
If pairing needs confirmation, complete it in Omarchy's Bluetooth panel and
retry Connect here. Controls use a separate Bluetooth Classic RFCOMM connection
through the computer's adapter. Dongle audio plus control uses both multipoint
slots. Disconnect controls frees that connection.

Headphone controls include battery, ANC, adaptive/comfort ANC, transparency,
crossfeed, on-head detection, smart pause, auto-answer and comfort call. Switches
apply immediately; transparency applies on slider release.

EQ: read five-band parametric EQ, edit frequency/gain/Q/filter and pre-gain,
then Save. Enable parametric EQ separately. Values are stored on the headphones.
Shelf Q must be 0.25–0.71; other Q values 0.25–8. Pre-gain is -12–0 dB.
All fields are validated before writing. A failed multi-band write can leave
some bands changed: read EQ again before continuing. Firmware flashing remains outside this app; use the official Sennheiser software
for firmware installation.

## Verification

```
python -m unittest discover -s tests -v
python backend/service.py --probe
omarchy-shell sennheiser-control status
```

Status reads verified on a real BTD 700, firmware 3.11.0. Headphone commands are based on the upstream HDB 630 implementation. Core controls
and new read paths have been checked on the connected headset; setting writes
also have encoding and validation tests.
The shared controller starts on first opening and polls every five seconds.
Each monitor attaches to it; it releases handles when all monitor widgets unload. Avoid concurrent controller instances when
probing. Run `python -B backend/service.py` for the line-delimited JSON worker;
stdin EOF shuts it down. Example request: `{"action":"refresh"}`.

## Remove

```
omarchy plugin remove phi0x.sennheiser
```

For a development copy, remove its bar.layout entry from shell.json and its
plugin folder, then rescan plugins. Optional cleanup: remove the udev file
`/etc/udev/rules.d/70-sennheiser-control.rules` using system administration tools
and reload udev. Local connection preferences and EQ presets are in
`~/.local/state/sennheiser-control/`; compiled helpers are in
`~/.cache/sennheiser-control/`. XDG directory overrides are respected.

See THIRD_PARTY.md for protocol sources and licenses.

## Setting explanations

Click a small **i** beside a setting to expand its explanation; click again to
collapse. Only one guide opens at a time. The transparency illustration follows
the slider, crossfeed shows how channels blend, and the EQ guide compares broad
and narrow bell filters. These are conceptual diagrams, not acoustic measurements.
The slider also labels both ends and explains when Adaptive ANC controls the balance.

Descriptions were checked against the [HDB 630 manual](https://cdn.sennheiser-hearing.com/product-documents/product-downloads/hdb-630/Instruction%20manual%20HDB%20630/Instruction_manual_HDB_630.pdf)
and [official FAQ](https://us.sennheiser-hearing.com/pages/hdb-630-faq/).
The experimental Comfort ANC flag is identified as undocumented, consistent with
the [protocol notes](https://github.com/hatemosphere/hdb630-control-macos/blob/main/docs/02-gaia-v3-commands.md).

The popup groups related controls into bordered sections. Its tabs and refresh
button remain visible while the settings scroll; each EQ band has its own card.
A dedicated scrollbar gutter keeps help icons clear of the scroll track.

Headphone controls remember the last explicitly selected paired headset in
`~/.local/state/sennheiser-control/connection.json` (or `$XDG_STATE_HOME`). After
power-off, suspend, or a connection reset, the worker reconnects with increasing
retry delays, capped at 30 seconds. Opening the widget after a shell restart
restores that target. It checks adapter power and pairing before discovery,
without resetting the adapter or changing audio routing. A shared session controller owns one hardware connection. All monitor widgets
attach to it and receive the same status; opening a second widget does not
create another headset connection. A lock still protects against unrelated
standalone diagnostic controllers.

Disconnect controls / Stop reconnecting clears the remembered target. Connection
recovery reads current settings; it never replays failed EQ or setting writes.
If the headset cannot accept a control connection because both multipoint slots
are occupied, disconnect another peer such as your phone and let the retry run.


## Additional controls

Headphones now includes wind-noise reduction (Off/Automatic/Maximum), call
transparency (Off/levels 1–4), pause-on-call-transparency, auto power-off, a
read-only paired-device list, and wireless resolution. Applying a changed
resolution preference restarts the headphones, then reconnects automatically.
No restart occurs if the chosen preference is already active.

EQ now includes processing-mode selection, bass boost and a graphic five-band
EQ with genre presets. Read graphic EQ, edit/select a preset, then Apply to write
the bands and enable Graphic EQ. Parametric EQ remains a separate mode.

Save a parametric draft locally under a name, load it as a draft, or delete it.
Loading and deleting local presets never change the headphone tuning. Saved
presets live in `~/.local/state/sennheiser-control/presets.json` (or XDG_STATE_HOME).
Save EQ to headphones is the separate hardware-write step. Existing names are
replaced when saved again. A failed multi-setting write may leave earlier values
applied; read settings again before retrying.

Dongle now includes Auracast broadcast settings. Read the current configuration,
choose a 1–32-byte UTF-8 name, visibility, quality and optional password, then
Save. Select Broadcast audio mode separately to transmit. Enabling encryption
requires a 1–16-byte UTF-8 password. Leave the password empty to retain an
existing encrypted broadcast password. Passwords are not read back, shown in
status broadcasts, or saved locally. Receivers must support Auracast; broadcast
reception was not tested without a compatible receiver.

## Active settings versus drafts

Graphic EQ and parametric EQ are mutually exclusive playback modes. Both editors
remain usable for preparing drafts; their captions show whether the mode is
active. Apply graphic EQ explicitly enables it. Saving parametric EQ keeps the
current processing mode, and its separate Enable button switches playback to PEQ.
Local preset operations remain usable regardless of playback mode.

Bass boost is disabled outside Graphic EQ. Bypassed parametric bands keep their
stored frequency/gain/Q values but disable those fields until another filter is
chosen. Already-active Enable / already-off Disable buttons are disabled.
Smart pause, automatic call answering and automatic power-off require on-head
detection. ANC-specific settings require noise cancellation. Each disabled
setting keeps its info button available and shows the reason.

Run `node tests/test_ui_rules.js` for the UI dependency and EQ-mode checks.


## Firmware checks

The Updates tab shows installed versions and checks the official catalog on
request. It records the check time and distinguishes current firmware, a newer
release, an unread device version and a failed check. It does not download images,
flash either device, or offer downgrades. Use the linked official updater to
install firmware: Dongle Control for BTD 700, Smart Control Plus for HDB 630.

See [firmware investigation](docs/firmware-research.md) for verified metadata,
transport findings and remaining work before native flashing can be supported.


## Future development

See the [roadmap](ROADMAP.md) for potential native firmware installation,
model-specific validation and recovery work, other possible improvements, and
how future releases can update the same public repository and marketplace
listing. These are plans to investigate, not current features or release promises.

## License

This project is [source-available under the Sennheiser Control license](LICENSE.md).
You may fork, modify and use it, including in a business. You may charge for
installation, integration, maintenance or support. You may include it as a free
component of a paid product if the app remains separately available without
charge and recipients keep their license rights.

You may not sell copies of the app or substantially derived/rebranded versions,
or charge for downloads, activation or access to the app itself. This custom
no-sale condition means the project is not OSI-approved open-source software.
The MIT and LGPL components identified in [THIRD_PARTY.md](THIRD_PARTY.md) retain
their own licenses and redistribution rights.

**No warranty; use at your own risk.** Authors and contributors exclude liability,
including for equipment damage, data loss and downtime, to the maximum extent
permitted by applicable law. See the license for the full terms and mandatory-law
exceptions.
