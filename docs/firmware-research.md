# Firmware update investigation

Investigated 2026-10-30. No firmware image was flashed or update-mode command sent.

## Verified catalog and installed versions

Official metadata endpoints, fetched with normal TLS verification:

- `https://api.s-consumer-cloud.com/firmware/api/v2/availableSystemReleases/700434?os_type=android`
  returned `success: true`, releases `["3.11.0"]` for BTD 700.
- `https://api.s-consumer-cloud.com/firmware/api/v2/availableSystemReleases/700445?os_type=android`
  returned `success: true`, releases `["3.33.3"]` for HDB 630.

Live USB and Bluetooth status reported those same installed versions.
The checker uses a fixed product allowlist, numeric version comparison, bounded
JSON responses and verified HTTPS. It does not infer "up to date" from errors,
empty lists, unknown installed versions or malformed version strings. It makes
no automatic network checks and sends no serial number or Bluetooth address.

Release details use `/systemRelease/<product>/<version>?os_type=android`:

- BTD 700 3.11.0: one FW_FULL package, identifier `0x0000`, 2,090,744 bytes,
  `MX248_dfu_image_With_Key_V_3_11_00.bin` on firmware.s-consumer-cloud.com.
- HDB 630 3.33.3: language-specific VP and FW_FULL packages, each ending in
  `.bin.zip.enc`. Languages include de, en, es, fr, ja, ko, ru, zh.
  The English full package is 2,071,863 bytes. No images were downloaded.

These are metadata observations, not verified image compatibility/signature checks.
A release version alone does not establish a safe flashing procedure.

## Update transport findings

Read-only HID enumeration of the connected BTD 700 (3542:3001):

- USB interface 0 includes the current control collection FFA2:0001.
- USB interface 1 includes FF00:0001 and FF00:0003 collections.

The independent [btd600-fw](https://github.com/hhh2210/btd600-fw) project targets
BTD 600 (3542:3000), FF00:0001, Qualcomm hid_upgrade reports 03/05/06 and a
VM Upgrade state machine. Its PID and pinned images differ from BTD 700.
The matching usage page is a lead, not evidence that its updater is safe for BTD 700.
No version/variant queries or DFU connect commands were sent on that interface.

For HDB 630, the existing protocol notes identify an Airoha chipset with GAIA v3
control. General GAIA upgrade documentation from another model does not prove
which OTA framing, encryption, package choice and reboot/recovery sequence this
model needs. Native flashing therefore remains unimplemented.

## Official software

- [Dongle Control](https://eu.sennheiser-hearing.com/en-de/pages/sennheiser-dongle-control)
  provides Windows/macOS downloads.
- [HDB 630 product page](https://us.sennheiser-hearing.com/products/hdb-630)
  links Smart Control Plus for headphone updates.

The graphassets download host linked by the official Dongle Control page failed
normal TLS validation with an expired-certificate error in this environment.
TLS validation was not disabled, and that executable was not downloaded or run.
The official metadata API worked with normal TLS validation.

## Remaining native-flashing work

1. Verify the BTD 700 update transport and firmware variant without entering an
   upgrade or disrupting audio; inspect exact official image structure/signature.
2. Establish full transfer, acknowledgement, verification, restart/resume and
   recovery behavior for the BTD 700, distinct from BTD 600 assumptions.
3. Trace the HDB 630 official updater, its encrypted package handling, language
   selection and OTA state machine; verify the target hardware/firmware variants.
4. Isolate the updater from normal controller traffic for the complete update.
5. Validate a real supported version transition and post-update recovery.

The Updates tab intentionally offers checking and official updater links, rather
than an unverified native Install button. It neither downloads nor flashes images.
