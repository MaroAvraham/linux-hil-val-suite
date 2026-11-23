import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import pexpect


@dataclass
class CommandResult:
    """אובייקט תוצאה מובנה לכל פקודה שרצה על ה-Target."""
    command: str
    stdout: str
    exit_code: int


class QemuController:
    """
    מנהל את מחזור החיים של מכונת QEMU דרך Serial Console (ttyS0).
    תומך ב-Context Manager (with) להבטחת ניקוי תהליכים.
    """
    INITIAL_PROMPT = r"[/~a-zA-Z0-9_-]* # "
    CUSTOM_PROMPT = "HIL_TARGET# "

    def __init__(
        self,
        kernel_path: str,
        initrd_path: str,
        log_file: str = "logs/serial.log",
        memory: str = "512M",
        boot_timeout: int = 30,
    ):
        self.kernel_path = Path(kernel_path)
        self.initrd_path = Path(initrd_path)
        self.log_file_path = Path(log_file)
        self.memory = memory
        self.boot_timeout = boot_timeout

        self.process: Optional[pexpect.spawn] = None
        self._log_handle = None
        self.boot_time_sec: float = 0.0

    def start(self) -> float:
        """מרים את QEMU, ממתין ל-Shell ומודד את זמן ה-Boot בשניות."""
        if not self.kernel_path.exists():
            raise FileNotFoundError(f"Kernel not found: {self.kernel_path}")
        if not self.initrd_path.exists():
            raise FileNotFoundError(f"Initrd not found: {self.initrd_path}")

        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_handle = open(self.log_file_path, "w", encoding="utf-8", errors="replace")

        args = [
            "-kernel", str(self.kernel_path),
            "-initrd", str(self.initrd_path),
            "-m", self.memory,
            "-nographic",
            "-append", "console=ttyS0 nokaslr quiet",
        ]

        start_time = time.monotonic()
        self.process = pexpect.spawn(
            "qemu-system-x86_64",
            args=args,
            encoding="utf-8",
            codec_errors="replace",
            timeout=self.boot_timeout,
            logfile=self._log_handle,
        )

        # 1. המתנה לבאנר מה-initramfs לוודא שהעלייה הושלמה
        self.process.expect("Linux HIL Validation Target Ready!", timeout=self.boot_timeout)
        self.boot_time_sec = round(time.monotonic() - start_time, 2)

        # 2. המתנה ל-Prompt הראשוני של BusyBox
        self.process.expect(r"# ", timeout=5)

        # 3. קביעת Prompt ייחודי (עם שרשור מחרוזות למניעת התאמה מוקדמת ב-echo)
        self.process.sendline('export PS1="HIL_TARGET""# "')
        self.process.expect(self.CUSTOM_PROMPT, timeout=5)

        return self.boot_time_sec

    def run_cmd(self, command: str, timeout: int = 10) -> CommandResult:
        """שולח פקודה ל-Target ומחזיר stdout נקי + קוד יציאה (exit_code)."""
        if not self.process or not self.process.isalive():
            raise RuntimeError("QEMU process is not running")

        marker = "__CMD_RC__="
        self.process.sendline(f"{command}; echo {marker}$?")
        self.process.expect(self.CUSTOM_PROMPT, timeout=timeout)

        raw_output = self.process.before or ""
        lines = [line.rstrip("\r") for line in raw_output.splitlines()]

        # הסרת השורה הראשונה (הפקודה עצמה שחוזרת ב-echo מהטרמינל)
        if lines and command in lines[0]:
            lines = lines[1:]

        # בתוך run_cmd(), החלף את הלולאה כך:
        exit_code = -1
        clean_lines = []
        for line in lines:
            if marker in line and "$?" in line:
                continue  # דילוג על שורת ה-echo של הפקודה עצמה
            match = re.search(rf"{marker}(\d+)", line)
            if match:
                exit_code = int(match.group(1))
            else:
                clean_lines.append(line)

        return CommandResult(
            command=command,
            stdout="\n".join(clean_lines).strip(),
            exit_code=exit_code,
        )

    def close(self) -> None:
        """סוגר את QEMU בצורה נקייה ומוודא שלא נשארים תהליכים יתומים."""
        if self.process is not None:
            try:
                if self.process.isalive():
                    # שליחת Ctrl+A ואז x ליציאה נקייה מ-QEMU
                    self.process.send("\x01x")
                    self.process.expect(pexpect.EOF, timeout=3)
            except (pexpect.TIMEOUT, pexpect.EOF, OSError):
                pass
            finally:
                if self.process.isalive():
                    self.process.terminate(force=True)
                self.process.close(force=True)
                self.process = None

        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None

    def __enter__(self) -> "QemuController":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()