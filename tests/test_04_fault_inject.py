import re
import pytest
from harness.log_analyzer import find_kernel_errors


@pytest.mark.fault
def test_daemon_sigkill_recovery_and_resource_release(dut):
    """
    הורג את הדמון בצורה אלימה (kill -9 / SIGKILL) בזמן שהוא מחזיק את ההתקן פתוח,
    ומוודא שהדרייבר משחרר את המשאב וניתן לגשת אליו ואף להסיר את המודול.
    """
    dut.run_cmd("insmod /lib/modules/task_telemetry.ko 2>/dev/null || true")

    pid = dut.run_cmd("monitor_cli --daemon < /dev/null > /tmp/daemon_kill.log 2>&1 & echo $!").stdout.strip()
    assert pid.isdigit()
    dut.run_cmd("sleep 1")

    # הזרקת תקלה + המתנה באותה פקודה כדי שה-SIGCHLD ייאסף בזמן ה-sleep ולא בזמן read()
    assert dut.run_cmd(f"kill -9 {pid}; sleep 1").exit_code == 0

    # אימות שהתהליך מת
    assert dut.run_cmd(f"kill -0 {pid} 2>/dev/null").exit_code != 0

    # אימות שההתקן לא נשאר נעול ושניתן להסיר את המודול בצורה נקייה
    assert dut.run_cmd("monitor_cli --stats").exit_code == 0
    assert dut.run_cmd("rmmod task_telemetry").exit_code == 0
    assert not find_kernel_errors(dut.run_cmd("dmesg").stdout)


@pytest.mark.fault
def test_driver_concurrent_mutex_stress(dut):
    """
    מריץ 10 תהליכי monitor_cli במקביל כדי לבחון את ה-mutex בדרייבר
    ולוודא שאין Race Condition או אובדן ספירת אירועים.
    """
    dut.run_cmd("insmod /lib/modules/task_telemetry.ko 2>/dev/null || true")
    assert dut.run_cmd("monitor_cli --reset").exit_code == 0

    # הפעלת 10 תהליכים בו-זמנית והמתנה לסיום כולם
    res = dut.run_cmd("for i in $(seq 1 10); do monitor_cli --stats >/dev/null & done; wait")
    assert res.exit_code == 0

    # קריאת הסטטיסטיקה הסופית (הפתיחה הזו עצמה היא אירוע מספר 11)
    final_out = dut.run_cmd("monitor_cli --stats").stdout
    match = re.search(r"events=(\d+)", final_out)
    assert match, f"Could not parse events from: {final_out}"

    events = int(match.group(1))
    assert events == 11, f"Race condition detected! Expected 11 events, got {events}"
    assert not find_kernel_errors(dut.run_cmd("dmesg").stdout)