"""Minimal, dependency-free builder of valid ``py3-none-any`` wheels.

Used by the exercises to create *harmless, local-only* packages (a ``.pth`` demo and the
dependency-confusion simulation). Nothing here downloads or uploads anything.
"""

from __future__ import annotations

import base64
import hashlib
import zipfile
from pathlib import Path

FIXED_DATE = (2026, 1, 1, 0, 0, 0)


def _record_hash(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    return "sha256=" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def normalize(name: str) -> str:
    """PEP 503 name normalization: runs of ``-``, ``_``, ``.`` become a single ``-``, lower-cased."""
    out: list[str] = []
    prev_sep = False
    for ch in name.lower():
        if ch in "-_.":
            if not prev_sep:
                out.append("-")
            prev_sep = True
        else:
            out.append(ch)
            prev_sep = False
    return "".join(out)


def build_wheel(name: str, version: str, files: dict[str, str], out_dir: Path, summary: str = "demo") -> Path:
    """Build ``{name}-{version}-py3-none-any.whl`` containing ``files`` (archive path -> text content)."""
    dist = normalize(name).replace("-", "_")
    dist_info = f"{dist}-{version}.dist-info"
    metadata = f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\nSummary: {summary}\n"
    wheel_meta = "Wheel-Version: 1.0\nGenerator: wheelkit (demo)\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    entries: dict[str, bytes] = {path: text.encode("utf-8") for path, text in files.items()}
    entries[f"{dist_info}/METADATA"] = metadata.encode("utf-8")
    entries[f"{dist_info}/WHEEL"] = wheel_meta.encode("utf-8")
    record_lines = [f"{path},{_record_hash(data)},{len(data)}" for path, data in entries.items()]
    record_lines.append(f"{dist_info}/RECORD,,")
    entries[f"{dist_info}/RECORD"] = ("\n".join(record_lines) + "\n").encode("utf-8")

    out_dir.mkdir(parents=True, exist_ok=True)
    wheel_path = out_dir / f"{dist}-{version}-py3-none-any.whl"
    # Fixed timestamps + no compression => byte-identical wheel (and sha256) on every OS and every run.
    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_STORED) as zf:
        for path, data in entries.items():
            info = zipfile.ZipInfo(path, date_time=FIXED_DATE)
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)
    return wheel_path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
