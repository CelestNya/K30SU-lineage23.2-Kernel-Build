#!/usr/bin/env python3
"""Generate release body markdown for stock kernel CI releases."""
import subprocess, sys
from datetime import datetime, timezone

# Find previous stock-kernel tag
tags = subprocess.run(
    ["git", "tag", "--list", "stock-kernel-*", "--sort=-v:refname"],
    capture_output=True, text=True, check=True
).stdout.strip().split("\n")

prev_tag = tags[1] if len(tags) > 1 else None

if prev_tag:
    log = subprocess.run(
        ["git", "log", "--oneline", "--no-decorate", f"{prev_tag}..HEAD"],
        capture_output=True, text=True, check=True
    ).stdout.strip()
    count = subprocess.run(
        ["git", "rev-list", "--count", f"{prev_tag}..HEAD"],
        capture_output=True, text=True, check=True
    ).stdout.strip()
    log_title = f"自上次发布以来共 {count} 个提交"
else:
    log = subprocess.run(
        ["git", "log", "--oneline", "--no-decorate", "-20"],
        capture_output=True, text=True, check=True
    ).stdout.strip()
    total = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        capture_output=True, text=True, check=True
    ).stdout.strip()
    log_title = f"首次发布（共 {total} 个提交）"

# Build body
lines = []
lines.append("## 📋 变更日志")
lines.append("")
lines.append(f"{log_title}：")
lines.append("")
if log:
    for line in log.split("\n"):
        lines.append(f"- {line}")
else:
    lines.append("（无新增变更）")

lines.append("")
lines.append("## 🔧 构建信息")
lines.append("")
lines.append(f"- **构建日期**: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
lines.append("- **内核来源**: LineageOS/android_kernel_xiaomi_sm8250 @ lineage-23.2")
lines.append("- **工具链**: AOSP Clang r383902 (Clang 14) + GCC 4.9")
lines.append("- **配置文件**: vendor/kona-perf + debugfs + sm8250-common + apollo")
lines.append("- **打包方式**: AnyKernel3（TWRP 刷入）+ boot.img（`fastboot boot` 验证）")
lines.append("")
lines.append("---")
lines.append("")
lines.append("*由 CI 自动构建*")

body = "\n".join(lines)
print(body)

# Write to file if path provided
if len(sys.argv) > 1:
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        f.write(body)
    print(f"\n(written to {sys.argv[1]})")
