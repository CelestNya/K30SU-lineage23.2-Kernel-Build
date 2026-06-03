#!/usr/bin/env python3
"""Fix MODULE_IMPORT_NS for 4.19 kernel compatibility.

MODULE_IMPORT_NS was introduced in kernel 5.x. On 4.19, we need to
wrap it with a version check so the build doesn't fail.
"""
import re

KSU_C = 'KernelSU/kernel/ksu.c'

with open(KSU_C, 'r') as f:
    content = f.read()

# Add version.h include if not present
if '#include <linux/version.h>' not in content:
    content = '#include <linux/version.h>\n' + content

# Wrap MODULE_IMPORT_NS with version check
pattern = r'MODULE_IMPORT_NS\(VFS_internal_I_am_really_a_filesystem_and_am_NOT_a_driver\);'
replacement = (
    '#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 0, 0)\n'
    + '\\g<0>\n'
    + '#endif'
)
content = re.sub(pattern, replacement, content)

with open(KSU_C, 'w') as f:
    f.write(content)

print('MODULE_IMPORT_NS fix applied')
