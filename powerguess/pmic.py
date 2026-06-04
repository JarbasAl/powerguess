"""Raspberry Pi PMIC board power via ``vcgencmd`` (Pi 5).

The Pi 5 PMIC reports per-rail voltage and current through
``vcgencmd pmic_read_adc``; summing ``V × I`` over the rails gives real
whole-board power — a measured *total* power source, which is why it lives in
the power library. Returns ``None`` on Pi 3/4 (no ADC telemetry) and non-Pi
hosts. Other Pi telemetry (throttling, clocks) belongs in the bridge, not here.
"""

from __future__ import annotations

import re
import subprocess
from shutil import which
from typing import Optional

# "<NAME>_A current(0)=0.0434A"  or  "<NAME>_V volt(24)=5.0985V"
_ADC_RE = re.compile(r"^\s*(\w+?)_(A|V)\s+\w+\(\d+\)=([\d.]+)\w*\s*$")


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
    """Sum board power (W) from ``pmic_read_adc`` output by pairing rail V and I."""
    rails: dict = {}
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


def pmic_available() -> bool:
    """True only where ``pmic_read_adc`` yields power — i.e. a Pi 5."""
    return pmic_power() is not None
