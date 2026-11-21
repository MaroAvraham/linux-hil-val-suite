#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

qemu-system-x86_64 \
 -kernel "$PROJECT_ROOT/build/bzImage" \
 -initrd "$PROJECT_ROOT/build/initramfs.cpio.gz" \
 -m 512M \
 -nographic \
 -append "console=ttyS0 nokaslr quiet"
