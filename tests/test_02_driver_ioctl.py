import re
import pytest
from harness.log_analyzer import find_kernel_errors

SYSFS_THRESHOLD = "/sys/class/telemetry_cls/task_telemetry/threshold"


def _get_mem_available_kb(dut) -> int:
    res = dut.run_cmd("grep -E 'MemFree:|MemAvailable:' /proc/meminfo | head -n 1")
    match = re.search(r"(\d+)", res.stdout)
    assert match, f"Could not parse meminfo: {res.stdout}"
    return int(match.group(1))


@pytest.mark.kernel
def test_lkm_lifecycle_stress(dut):
    """20 מחזורי טעינה והסרה של המודול + מעקב שאין דליפת זיכרון חריגה."""
    # וידוא מצב נקי לפני תחילת הלולאה
    dut.run_cmd("rmmod task_telemetry 2>/dev/null || true")
    mem_before = _get_mem_available_kb(dut)

    for cycle in range(1, 21):
        res_in = dut.run_cmd("insmod /lib/modules/task_telemetry.ko")
        assert res_in.exit_code == 0, f"insmod failed on cycle {cycle}: {res_in.stdout}"

        res_dev = dut.run_cmd("ls /dev/task_telemetry")
        assert res_dev.exit_code == 0, f"/dev/task_telemetry missing on cycle {cycle}"

        res_out = dut.run_cmd("rmmod task_telemetry")
        assert res_out.exit_code == 0, f"rmmod failed on cycle {cycle}: {res_out.stdout}"

    mem_after = _get_mem_available_kb(dut)
    mem_drop_kb = mem_before - mem_after
    # טעינה והסרה נקייה לא אמורה לאבד יותר מכמה MB בודדים של מטמון
    assert mem_drop_kb < 4096, f"Potential memory leak detected: dropped {mem_drop_kb} kB"

    dmesg = dut.run_cmd("dmesg").stdout
    assert not find_kernel_errors(dmesg), "Kernel errors found during LKM stress loop"


@pytest.mark.kernel
@pytest.mark.parametrize("bad_value", ["0", "99999", "-5", "not_a_number"])
def test_driver_negative_sysfs_inputs(dut, bad_value):
    """בדיקה שלילית: קלט לא חוקי ל-sysfs חייב להידחות בלי להפיל את הקרנל."""
    dut.run_cmd("insmod /lib/modules/task_telemetry.ko 2>/dev/null || true")

    res = dut.run_cmd(f"echo '{bad_value}' > {SYSFS_THRESHOLD}")
    assert res.exit_code != 0, f"Driver unexpectedly accepted invalid threshold: {bad_value}"

    # וידוא שהערך החוקי הקודם לא הושחת ושהקרנל נקי
    current = dut.run_cmd(f"cat {SYSFS_THRESHOLD}").stdout
    assert current.isdigit() and int(current) > 0
    assert not find_kernel_errors(dut.run_cmd("dmesg").stdout)


@pytest.mark.kernel
@pytest.mark.parametrize("bad_threshold", ["0", "10001", "999999"])
def test_driver_negative_ioctl_threshold(dut, bad_threshold):
    """בדיקה שלילית: ioctl עם ערך מחוץ לטווח חייב להחזיר EINVAL (קוד יציאה שונה מ-0)."""
    dut.run_cmd("insmod /lib/modules/task_telemetry.ko 2>/dev/null || true")

    res = dut.run_cmd(f"monitor_cli --threshold {bad_threshold}")
    assert res.exit_code != 0
    assert "Invalid argument" in res.stdout or res.exit_code == 1
    assert not find_kernel_errors(dut.run_cmd("dmesg").stdout)