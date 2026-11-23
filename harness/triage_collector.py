import shutil
from pathlib import Path
from harness.qemu_controller import QemuController


def collect_triage(dut: QemuController, test_name: str, reports_dir: Path) -> Path:
    """
    אוסף ראיות מערכת מה-Target ברגע שטסט נכשל ושומר אותן
    תחת reports/triage/<test_name>/.
    """
    safe_name = test_name.replace("/", "_").replace("[", "_").replace("]", "")
    triage_dir = reports_dir / "triage" / safe_name
    triage_dir.mkdir(parents=True, exist_ok=True)

    commands = {
        "dmesg.log": "dmesg",
        "meminfo.txt": "cat /proc/meminfo",
        "modules.txt": "cat /proc/modules",
        "ps.txt": "ps",
    }

    for filename, cmd in commands.items():
        try:
            res = dut.run_cmd(cmd, timeout=5)
            content = res.stdout if res.exit_code == 0 else f"[cmd failed rc={res.exit_code}]\n{res.stdout}"
        except Exception as exc:
            content = f"[triage collection error: {exc}]"
        (triage_dir / filename).write_text(content + "\n", encoding="utf-8")

    # העתקת לוג ה-Serial המלא עד לנקודת הכשל
    if dut.log_file_path.exists():
        shutil.copy2(dut.log_file_path, triage_dir / "serial.log")

    return triage_dir