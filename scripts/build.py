"""Build a standalone offline-store IPS for USA Minecraft update v9408."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CODE_SHA256 = "7e58f876a531428b484a4a71bdca364413ce86c6bb63250ca375605e41f260f0"


def seams():
    text = (ROOT / "native/seams.h").read_text()
    return {name: int(value, 16) for name, value in re.findall(
        r"^#define\s+(SEAM_\w+)\s+(0x[0-9a-fA-F]+)u", text, re.M)}


def branch(source, target):
    displacement = target - source - 8
    if displacement % 4 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError("ARM branch target is out of range or unaligned")
    return 0xEA000000 | ((displacement >> 2) & 0xFFFFFF)


def ips(original, patched):
    out = bytearray(b"PATCH")
    index = 0
    while index < len(original):
        if original[index] == patched[index]:
            index += 1
            continue
        start = index
        while index < len(original) and original[index] != patched[index] and index - start < 65535:
            index += 1
        out.extend(start.to_bytes(3, "big"))
        out.extend((index - start).to_bytes(2, "big"))
        out.extend(patched[start:index])
    out.extend(b"EOF")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", required=True, type=Path, help="Decompressed USA update v9408 code.bin")
    parser.add_argument("--devkitarm", type=Path, default=os.environ.get("DEVKITARM"),
                        help="devkitARM directory containing bin/arm-none-eabi-gcc")
    args = parser.parse_args()
    original = args.code.read_bytes()
    if hashlib.sha256(original).hexdigest() != CODE_SHA256:
        raise SystemExit("Unsupported code.bin: expected the unmodified USA 1.9.19 update (v9408).")
    registry = seams()
    build = ROOT / "build"
    build.mkdir(exist_ok=True)

    def tool(name):
        executable = "arm-none-eabi-" + name + (".exe" if os.name == "nt" else "")
        location = args.devkitarm / "bin" / executable if args.devkitarm else shutil.which(executable)
        if not location or not Path(location).is_file():
            raise SystemExit("Install devkitARM or pass --devkitarm.")
        return str(location)

    elf = build / "store-demo.elf"
    subprocess.run([tool("gcc"), "-mcpu=mpcore", "-marm", "-mfloat-abi=soft",
                    "-Os", "-std=c11", "-ffreestanding", "-fno-builtin", "-fno-stack-protector",
                    "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-ffunction-sections",
                    "-nostdlib", "-Wl,--build-id=none", "-Wl,-T," + str(ROOT / "native/payload.ld"),
                    "-Wall", "-Wextra", "-Werror", str(ROOT / "native/catalog.c"),
                    "-o", str(elf)], check=True)
    payload_file = build / "catalog.bin"
    subprocess.run([tool("objcopy"), "-O", "binary", str(elf), str(payload_file)], check=True)
    symbols = subprocess.check_output([tool("nm"), "-n", str(elf)], text=True)
    addresses = {line.split()[2]: int(line.split()[0], 16) for line in symbols.splitlines()
                 if len(line.split()) == 3}
    payload = payload_file.read_bytes()
    base = registry["SEAM_CatalogPayload"]
    if addresses["demo_fill_catalog"] != base or len(payload) > registry["SEAM_CatalogPayloadEnd"] - base:
        raise SystemExit("Payload entry/size does not fit the replaced catalog function.")
    patched = bytearray(original)
    patches = []

    def write(name, content):
        address = registry[name]
        offset = address - registry["SEAM_ImageBase"]
        if offset < 0 or offset + len(content) > len(original):
            raise ValueError("Patch lies outside code.bin")
        for previous in patches:
            if address < previous["address"] + previous["size"] and previous["address"] < address + len(content):
                raise ValueError("Overlapping patches")
        patched[offset:offset + len(content)] = content
        patches.append({"name": name, "address": address, "size": len(content)})

    def word(name, instruction):
        write(name, struct.pack("<I", instruction))

    write("SEAM_CatalogPayload", payload)
    word("SEAM_StoreBrowser_tick", branch(registry["SEAM_StoreBrowser_tick"], addresses["demo_tick"]))
    word("SEAM_StoreBrowser_loadCatalog", branch(registry["SEAM_StoreBrowser_loadCatalog"],
                                               registry["SEAM_StoreBrowser_rebuild"]))
    for name in ("SEAM_Store_setupCommerce", "SEAM_Store_setupConnection",
                 "SEAM_Store_finishConnection", "SEAM_Store_finishCommerce"):
        word(name, 0xE1A00000)  # nop: store-scoped service setup/teardown
    word("SEAM_Store_restorePurchasesAction", 0xE12FFF1E)  # bx lr after native epilogue
    word("SEAM_StoreItem_purchaseAction", 0xE12FFF1E)  # common touch/controller purchase entry
    word("SEAM_StoreItem_purchaseEnableBranch", 0xE1A00000)  # always disable purchase button
    word("SEAM_StoreBrowser_rowZeroRegister", 0xE3A04000)  # r4 = native row's zero argument
    word("SEAM_StoreBrowser_rowServiceBranch", branch(registry["SEAM_StoreBrowser_rowServiceBranch"],
                                                    registry["SEAM_StoreBrowser_rowCreate"]))
    target = build / "luma/titles/00040000001B8700"
    target.mkdir(parents=True, exist_ok=True)
    (target / "code.ips").write_bytes(ips(original, patched))
    (build / "patched-code.bin").write_bytes(patched)
    (build / "patch-manifest.json").write_text(json.dumps({
        "input_sha256": CODE_SHA256, "payload_bytes": len(payload),
        "patches": patches, "symbols": addresses,
    }, indent=2) + "\n")
    archive = build / "MC3DS-Store-Demo-USA-v9408.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
        package.write(target / "code.ips", "luma/titles/00040000001B8700/code.ips")
        package.write(ROOT / "README.md", "README.md")
    print(f"Built standalone store demo: {len(payload)} payload bytes, {len(patches)} patch regions")
    print(archive)


if __name__ == "__main__":
    main()
