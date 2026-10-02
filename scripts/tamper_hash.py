"""Exercise 3: copy a hash-pinned requirements file and corrupt ONE hex digit of every ``--hash``.

This simulates "the artifact on the index is not the one you locked" (a swapped/tampered file).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HASH_RE = re.compile(r"(--hash=sha256:)([0-9a-f]{64})")


def flip_first_hex(digest: str) -> str:
    first = digest[0]
    replacement = "0" if first != "0" else "1"
    return replacement + digest[1:]


def tamper(text: str) -> tuple[str, int]:
    """Return (new_text, number_of_hashes_changed)."""
    return HASH_RE.subn(lambda m: m.group(1) + flip_first_hex(m.group(2)), text)


def main(argv: list[str]) -> int:
    src = Path(argv[1]) if len(argv) > 1 else Path("requirements.txt")
    dst = src.with_name("requirements-tampered.txt")
    new_text, count = tamper(src.read_text(encoding="utf-8"))
    if count == 0:
        print(f"No sha256 hashes found in {src}", file=sys.stderr)
        return 1
    dst.write_text(new_text, encoding="utf-8")
    print(f"Wrote {dst} ({count} hashes corrupted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
