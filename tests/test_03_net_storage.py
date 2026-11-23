import pytest
from harness.log_analyzer import find_kernel_errors


@pytest.mark.storage
def test_virtio_blk_data_integrity(dut):
    """
    מפרמט דיסק virtio-blk (/dev/sda), כותב קובץ בדיקה, מבצע sync,
    מנתק ומחבר מחדש ומוודא ש-sha256sum זהה לחלוטין.
    """
    assert dut.run_cmd("ls /dev/sda").exit_code == 0, "virtio-blk device /dev/sda not found"

    # פרמוט ועגינה
    assert dut.run_cmd("mkfs.ext2 -F /dev/sda").exit_code == 0
    assert dut.run_cmd("mkdir -p /mnt/testdisk && mount /dev/sda /mnt/testdisk").exit_code == 0

    # כתיבת 2MB של נתונים אקראיים וחישוב Hash לפני ניתוק
    assert dut.run_cmd("dd if=/dev/urandom of=/mnt/testdisk/payload.bin bs=1M count=2").exit_code == 0
    hash_before = dut.run_cmd("sha256sum /mnt/testdisk/payload.bin").stdout.split()[0]

    # סנכרון מלא, ניתוק ועגינה מחדש כדי לוודא שהנתונים אכן נשמרו על הדיסק ולא רק ב-RAM Cache
    assert dut.run_cmd("sync && umount /mnt/testdisk").exit_code == 0
    assert dut.run_cmd("mount /dev/sda /mnt/testdisk").exit_code == 0

    hash_after = dut.run_cmd("sha256sum /mnt/testdisk/payload.bin").stdout.split()[0]
    dut.run_cmd("umount /mnt/testdisk")

    assert hash_before == hash_after, f"Data corruption! {hash_before} != {hash_after}"
    assert not find_kernel_errors(dut.run_cmd("dmesg").stdout)


@pytest.mark.storage
def test_daemon_no_fd_leak(dut):
    """מפעיל את הדמון ברקע ובודק שמספר ה-File Descriptors ב-/proc/PID/fd נשאר קבוע."""
    dut.run_cmd("insmod /lib/modules/task_telemetry.ko 2>/dev/null || true")

    # הפעלת הדמון ברקע ושליפת ה-PID שלו
    res_pid = dut.run_cmd("monitor_cli --daemon > /tmp/daemon.log 2>&1 & echo $!")
    pid = res_pid.stdout.strip()
    assert pid.isdigit(), f"Failed to start daemon, got PID: {pid}"

    try:
        fd_start = int(dut.run_cmd(f"ls /proc/{pid}/fd | wc -l").stdout.strip())
        # המתנה למספר מחזורי דגימה של הדמון (כל מחזור = 2 שניות)
        dut.run_cmd("sleep 6")
        fd_end = int(dut.run_cmd(f"ls /proc/{pid}/fd | wc -l").stdout.strip())

        assert fd_end == fd_start, f"FD leak detected! Started with {fd_start}, ended with {fd_end}"
    finally:
        dut.run_cmd(f"kill -TERM {pid} 2>/dev/null || true")