from pathlib import Path
import pytest
from harness.qemu_controller import QemuController

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def dut():
    """
    Fixture ברמת Session: מרים את QEMU פעם אחת בתחילת הריצה,
    מעביר אותו לכל הטסטים, ומכבה אותו בצורה בטוחה בסיום.
    """
    controller = QemuController(
        kernel_path=str(PROJECT_ROOT / "build" / "bzImage"),
        initrd_path=str(PROJECT_ROOT / "build" / "initramfs.cpio.gz"),
        log_file=str(PROJECT_ROOT / "logs" / "serial.log"),
        boot_timeout=30,
    )
    with controller as target:
        yield target