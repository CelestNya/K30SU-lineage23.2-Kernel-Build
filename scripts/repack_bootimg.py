#!/usr/bin/env python3
"""Re-pack boot.img: replace kernel+dtb in stock boot.img while preserving header.

Usage:
  python3 repack_bootimg.py <stock_boot.img> <kernel> <dtb> <output>
"""
import subprocess, sys, os, shlex

stock_boot_img = sys.argv[1]
kernel_img = sys.argv[2]
dtb_img = sys.argv[3]
output_img = sys.argv[4]

# Unpack and get mkbootimg args in one call
result = subprocess.run(
    ["python3", "mkbootimg-tools/unpack_bootimg.py",
     "--boot_img", stock_boot_img,
     "--out", "boot_extract",
     "--format", "mkbootimg"],
    capture_output=True, text=True, check=True)

# Replace kernel and dtb in the extracted files
subprocess.check_call(["cp", kernel_img, "boot_extract/kernel"])
if os.path.isfile(dtb_img):
    subprocess.check_call(["cp", dtb_img, "boot_extract/dtb"])

# Parse mkbootimg args from output, then update kernel/ramdisk/dtb paths
# They already point to boot_extract/ so we keep them as-is
mkbootimg_args = shlex.split(result.stdout.strip())
args = ["python3", "mkbootimg-tools/mkbootimg.py"] + mkbootimg_args + ["-o", output_img]

print("Running:", " ".join(args))
sys.stdout.flush()
subprocess.check_call(args)
