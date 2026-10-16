# Minecraft 3DS Store Demo

A standalone, offline, browse-only demonstration of the original Minecraft: New Nintendo 3DS Edition store. Targets the **USA 1.9.19 update (v9408)**.

The game's native store screens, category buttons, scrolling lists, skin previews, pack artwork, descriptions and preview navigation are retained. The remote catalog lookup is replaced with the game's own local catalog mappings. Live prices are left blank. Listing order follows the local item-code map; this is not a recording of the historical server catalog.

Purchase buttons are disabled. The common purchase handler used by touch and controller input returns without doing anything. Restore Purchases is inactive. This mod does not grant licenses, change ownership flags, install packs or contact Nintendo's commerce service through the store.

## Install

1. Install the USA game and its v9408 update.
2. Enable **game patching** in Luma3DS.
3. Copy the ZIP's `luma` folder to the SD card root.
4. Open Minecraft and select **Store**.

This is a separate mod, not an add-on to NuMC3DS. Both use the same title's `code.ips`, so install one at a time. Preserve your existing title mod folder before replacing it. No ROMFS replacements, external exheader, plugin or extra permissions are required.

For Azahar, place the generated `code.ips` in the USA game's mod directory with other code patches disabled. The game/update supply all artwork and localization.

## Build

Requirements: Python 3 and devkitARM. Supply your own decompressed, unmodified update `code.bin`; game binaries and SDK files are not included.

```powershell
python scripts/build.py --code C:/path/to/update/code.bin --devkitarm C:/devkitPro/devkitARM
```

The builder verifies the exact executable SHA-256 and generates `build/MC3DS-Store-Demo-USA-v9408.zip`. Only the patch and this README are packaged. The ignored build directory also contains the linked payload, patched executable and patch manifest for local inspection.

## Implementation

- `native/seams.h`: exact executable addresses.
- `native/native_types.h`: verified catalog and store-record prefixes.
- `native/catalog.c`: feeds the original browser from its existing local metadata maps.
- `native/payload.ld`: links inside the replaced remote catalog function; no bootstrap or permission changes.
- `scripts/build.py`: compiles the payload and emits the standalone IPS.

The main NuMC3DS source and build are not modified by this project.
