from pathlib import Path
import pytest
from harness.qemu_controller import QemuController

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

@pytest.fixture(scope="session")
def dut(tmp_path_factory):
    """מייצר דיסק virtio-blk זמני של 32MB ומרים את QEMU למשך כל ה-Session."""
    disk_dir = tmp_path_factory.mktemp("qemu_disk")
    disk_img = disk_dir / "disk.img"
    subprocess.run(
        ["qemu-img", "create", "-f", "raw", str(disk_img), "32M"],
        check=True,
        capture_output=True,
    )

    controller = QemuController(
        kernel_path=str(PROJECT_ROOT / "build" / "bzImage"),
        initrd_path=str(PROJECT_ROOT / "build" / "initramfs.cpio.gz"),
        log_file=str(PROJECT_ROOT / "logs" / "serial.log"),
        disk_path=str(disk_img),
        boot_timeout=30,
    )
    with controller as target:
        yield target


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook שמזהה כשל בטסט ומפעיל אוטומטית את איסוף ה-Triage."""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        dut_instance = item.funcargs.get("dut")
        if dut_instance is not None:
            triage_path = collect_triage(dut_instance, item.name, REPORTS_DIR)
            print(f"\n[AUTO-TRIAGE] Collected failure bundle at: {triage_path}")