"""Raspberry Pi specifics via ``vcgencmd``.

Two SBC-only capabilities the generic paths can't provide:

- **PMIC board power** — the Pi 5 PMIC reports per-rail voltage *and* current
  through ``vcgencmd pmic_read_adc``; summing ``V × I`` over the rails gives real
  whole-board power with no extra hardware (the ARM analogue to x86 RAPL).
- **Throttling / undervoltage** — ``vcgencmd get_throttled`` flags under-voltage
  and thermal/frequency throttling, which on a Pi is both power-relevant and a
  data-integrity warning.

Everything no-ops cleanly when ``vcgencmd`` isn't present (i.e. not a Pi).
"""

from __future__ import annotations

import re
import subprocess
from shutil import which
from typing import Dict, Optional

# "<NAME>_A current(0)=0.0434A"  or  "<NAME>_V volt(24)=5.0985V"
_ADC_RE = re.compile(r"^\s*(\w+?)_(A|V)\s+\w+\(\d+\)=([\d.]+)\w*\s*$")


def available() -> bool:
    return bool(which("vcgencmd"))


def _vcgencmd(*args: str) -> Optional[str]:
    if not which("vcgencmd"):
        return None
    try:
        out = subprocess.run(["vcgencmd", *args], capture_output=True, text=True,
                             timeout=5)
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def parse_pmic_adc(text: str) -> Optional[float]:
    """Sum board power (W) from ``pmic_read_adc`` output by pairing each rail's
    current and voltage."""
    rails: Dict[str, Dict[str, float]] = {}
    for line in text.splitlines():
        m = _ADC_RE.match(line)
        if not m:
            continue
        name, kind, value = m.group(1), m.group(2), float(m.group(3))
        rails.setdefault(name, {})[kind] = value
    total = sum(r["A"] * r["V"] for r in rails.values() if "A" in r and "V" in r)
    return round(total, 3) if total > 0 else None


def pmic_power() -> Optional[float]:
    """Whole-board power in watts from the Pi PMIC, or None (not a Pi 5 / no PMIC)."""
    out = _vcgencmd("pmic_read_adc")
    return parse_pmic_adc(out) if out else None


def parse_throttled(text: str) -> Dict[str, bool]:
    """Decode a ``throttled=0x…`` value into named flags."""
    try:
        value = int(text.split("=")[-1].strip(), 16)
    except (ValueError, IndexError):
        return {}
    return {
        "undervoltage": bool(value & 0x1),
        "freq_capped": bool(value & 0x2),
        "throttled": bool(value & 0x4),
        "soft_temp_limit": bool(value & 0x8),
        "undervoltage_occurred": bool(value & 0x10000),
        "throttled_occurred": bool(value & 0x40000),
    }


def get_throttled() -> Dict[str, bool]:
    """Current throttling / undervoltage flags, or empty when unavailable."""
    out = _vcgencmd("get_throttled")
    return parse_throttled(out) if out else {}
