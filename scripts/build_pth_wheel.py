"""Exercise 4b: build a HARMLESS wheel whose ``.pth`` file runs code at every interpreter start.

This mirrors the mechanism used by the malicious ``litellm==1.82.8`` release (March 2026), but the
payload here only prints one line to stderr. Install it ONLY into a throwaway venv.
"""

from __future__ import annotations

from pathlib import Path

from wheelkit import build_wheel

PTH_LINE = (
    "import sys; sys.stderr.write('[pth_demo] Hello from a .pth file: this line ran at interpreter START, "
    "you never imported anything\\n')\n"
)


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "ex4_install_time" / "dist"
    wheel = build_wheel(
        name="pth-demo",
        version="0.1.0",
        files={
            "pth_demo/__init__.py": '"""Harmless demo package."""\n',
            "pth_demo_hook.pth": PTH_LINE,
        },
        out_dir=out_dir,
        summary="Harmless .pth startup-hook demo",
    )
    print(f"Built {wheel}")


if __name__ == "__main__":
    main()
