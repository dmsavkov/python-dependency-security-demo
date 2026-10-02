"""Exercise 5b: naive OFFLINE typosquatting detector for a requirements file.

Compares every requirement name with a small list of very popular PyPI projects and warns when a name is
suspiciously close (but not equal) to one of them. Real tools use download stats, publish dates and
malware feeds; this is only to make the idea tangible.
"""

from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

from wheelkit import normalize

POPULAR: tuple[str, ...] = (
    "requests", "urllib3", "numpy", "pandas", "django", "flask", "fastapi", "pydantic", "boto3", "setuptools",
    "pyyaml", "jinja2", "cryptography", "pillow", "matplotlib", "scipy", "torch", "tensorflow", "colorama",
    "python-dateutil", "beautifulsoup4", "selenium", "openai", "langchain", "litellm", "httpx", "pytest",
)  # fmt: skip

NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def parse_names(text: str) -> list[str]:
    names: list[str] = []
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped or stripped.startswith("-"):
            continue
        match = NAME_RE.match(stripped)
        if match:
            names.append(normalize(match.group(1)))
    return names


def suspicious(name: str, cutoff: float = 0.8) -> list[str]:
    """Popular names that ``name`` resembles without being identical to."""
    popular = [normalize(p) for p in POPULAR]
    if name in popular:
        return []
    return difflib.get_close_matches(name, popular, n=3, cutoff=cutoff)


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else Path("requirements-typos.txt")
    findings = 0
    for name in parse_names(path.read_text(encoding="utf-8")):
        close = suspicious(name)
        if close:
            findings += 1
            print(f"WARNING: '{name}' looks like {close} - typo or typosquat?")
        else:
            print(f"ok:      '{name}'")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
