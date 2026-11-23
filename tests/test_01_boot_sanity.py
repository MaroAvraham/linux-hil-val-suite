from harness.log_analyzer import find_kernel_errors
import pytest

@pytest.mark.sanity

def test_boot_time_within_threshold(dut):
    """מוודא שהמערכת עלתה תוך פחות מ-10 שניות."""
    assert dut.boot_time_sec > 0
    assert dut.boot_time_sec < 10.0, f"Boot took too long: {dut.boot_time_sec}s"


def test_kernel_version(dut):
    """מוודא ש-uname -r מחזיר גרסת קרנל תקינה עם קוד יציאה 0."""
    res = dut.run_cmd("uname -r")
    assert res.exit_code == 0
    assert len(res.stdout) > 0
    # עדכן את הקידומת אם קימפלת גרסת קרנל אחרת (למשל "5.15" או "6.6")
    assert res.stdout.startswith(("5.", "6.")), f"Unexpected kernel version: {res.stdout}"


def test_virtual_filesystems_mounted(dut):
    """מוודא שסקריפט ה-/init ביצע mount ל-/proc, /sys ו-/dev."""
    for path in ("/proc", "/sys", "/dev"):
        res = dut.run_cmd(f"ls {path}")
        assert res.exit_code == 0, f"Failed to list {path}"
        assert len(res.stdout) > 0, f"{path} appears to be empty (not mounted)"


def test_dmesg_clean_of_critical_errors(dut):
    """מוודא שאין Kernel panic, Oops, BUG או Call Trace ב-dmesg."""
    res = dut.run_cmd("dmesg")
    assert res.exit_code == 0
    errors = find_kernel_errors(res.stdout)
    assert not errors, f"Critical kernel errors found in dmesg:\n" + "\n".join(errors)