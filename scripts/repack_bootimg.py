#!/usr/bin/env python3
"""Re-pack boot.img: replace kernel+dtb in stock boot.img while preserving header.

Usage:
  python3 repack_bootimg.py <stock_boot.img> <kernel> <dtb> <output>
"""
import json, subprocess, sys

stock_boot_img = sys.argv[1]
kernel_img = sys.argv[2]
dtb_img = sys.argv[3]
output_img = sys.argv[4]

# Unpack stock boot.img
subprocess.check_call([
    "python3", "mkbootimg-tools/unpack_bootimg.py",
    "--boot_img", stock_boot_img,
    "--out", "boot_extract"
])

# Replace kernel and dtb
subprocess.check_call(["cp", kernel_img, "boot_extract/kernel"])
if dtb_img != "none":
    subprocess.check_call(["cp", dtb_img, "boot_extract/dtb"])

# Read header params from JSON
cfg = json.load(open("boot_extract/boot.img.json"))

# Build mkbootimg args
args = ["python3", "mkbootimg-tools/mkbootimg.py"]
for key, flag in [
    ("header_version", "--header_version"),
    ("base", "--base"),
    ("kernel_offset", "--kernel_offset"),
    ("ramdisk_offset", "--ramdisk_offset"),
    ("tags_offset", "--tags_offset"),
    ("page_size", "--pagesize"),
    ("os_version", "--os_version"),
    ("os_patch_level", "--os_patch_level"),
    ("cmdline", "--cmdline"),
]:
    val = cfg.get(key)
    if val is not None:
        if key in ("base", "kernel_offset", "ramdisk_offset", "tags_offset"):
            args += [flag, f"0x{int(val):08x}"]
        else:
            args += [flag, str(val)]

args += ["--kernel", "boot_extract/kernel"]
args += ["--ramdisk", "boot_extract/ramdisk"]
args += ["--dtb", "boot_extract/dtb"]
args += ["-o", output_img]

print(" ".join(args))
subprocess.check_call(args)
