import re
from typing import List

# רשימת דפוסי כשל קריטיים בקרנל לינוקס
CRITICAL_KERNEL_PATTERNS = [
    r"Kernel panic",
    r"Oops:",
    r"BUG:",
    r"Call Trace:",
    r"Out of memory",
    r"segfault at",
]

# אזהרות חומרה/BIOS ידועות של סימולטור QEMU שאינן תקלת קרנל אמיתית
BENIGN_PATTERNS = [
    r"MP-BIOS bug: 8254 timer not connected to IO-APIC",
]

def find_kernel_errors(log_text: str) -> List[str]:
    """
    סורק טקסט (פלט dmesg או לוג Serial) ומחזיר רשימה של כל השורות
    שבהן נמצא דפוס כשל קריטי של הקרנל.
    """
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in CRITICAL_KERNEL_PATTERNS]
    matches: List[str] = []

    for line in log_text.splitlines():
        if any(regex.search(line) for regex in compiled):
            matches.append(line.strip())

    return matches