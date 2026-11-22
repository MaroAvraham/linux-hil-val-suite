#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ROOTFS_DIR="$PROJECT_ROOT/build/rootfs"
BUSYBOX_INSTALL="$PROJECT_ROOT/src/busybox/_install"
KDIR="${KDIR:-$PROJECT_ROOT/src/linux}"

echo "[1/4] Running static analysis (cppcheck)..."
cppcheck --error-exitcode=1 --enable=warning,performance,portability \
  "$PROJECT_ROOT/dut/userspace_daemon/monitor_cli.c"

echo "[2/4] Building Kernel Module (task_telemetry.ko)..."
make -C "$PROJECT_ROOT/dut/kernel_module" KDIR="$KDIR" clean all

echo "[3/4] Building static Userspace Daemon (monitor_cli)..."
gcc -static -Wall -Werror -O2 \
  -I"$PROJECT_ROOT/dut/include" \
  "$PROJECT_ROOT/dut/userspace_daemon/monitor_cli.c" \
  -o "$PROJECT_ROOT/dut/userspace_daemon/monitor_cli"

echo "[4/4] Assembling and packing initramfs.cpio.gz..."
rm -rf "$ROOTFS_DIR"
mkdir -p "$ROOTFS_DIR"/{proc,sys,dev,etc,tmp,lib/modules,usr/bin}

# העתקת BusyBox וסקריפט ה-init משלב 1
cp -a "$BUSYBOX_INSTALL"/* "$ROOTFS_DIR"/
cp "$PROJECT_ROOT/target/initramfs/init" "$ROOTFS_DIR/init"
chmod +x "$ROOTFS_DIR/init"

# העתקת המודול והדמון החדשים לתוך מערכת הקבצים של ה-Target
cp "$PROJECT_ROOT/dut/kernel_module/task_telemetry.ko" "$ROOTFS_DIR/lib/modules/"
cp "$PROJECT_ROOT/dut/userspace_daemon/monitor_cli" "$ROOTFS_DIR/usr/bin/"

cd "$ROOTFS_DIR"
find . -print0 | cpio --null -ov --format=newc | gzip -9 > "$PROJECT_ROOT/build/initramfs.cpio.gz"

echo "Build complete! Updated $PROJECT_ROOT/build/initramfs.cpio.gz"