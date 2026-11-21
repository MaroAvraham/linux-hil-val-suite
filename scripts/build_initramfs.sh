#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ROOTFS_DIR="$PROJECT_ROOT/build/rootfs"
BUSYBOX_INSTALL="$PROJECT_ROOT/src/busybox/_install"

rm -rf "$ROOTFS_DIR"
mkdir -p "$ROOTFS_DIR"/{proc,sys,dev,etc,tmp}

cp -a "$BUSYBOX_INSTALL"/* "$ROOTFS_DIR"/
cp "$PROJECT_ROOT/target/initramfs/init" "$ROOTFS_DIR/init"
chmod +x "$ROOTFS_DIR/init"

cd "$ROOTFS_DIR"
find . -print0 | cpio --null -ov --format=newc | gzip -9 > "$PROJECT_ROOT/build/initramfs.cpio.gz"

echo "Done! Creates $PROJECT_ROOT/build/initramfs.cpio.gz"
