"""Tests for the helper scripts (run: ``python -m pytest``)."""

from __future__ import annotations

import zipfile
from pathlib import Path

from tamper_hash import flip_first_hex, tamper
from typosquat_check import parse_names, suspicious
from wheelkit import build_wheel, normalize


def test_normalize() -> None:
    assert normalize("Acme_Internal..Utils") == "acme-internal-utils"


def test_build_wheel_has_record(tmp_path: Path) -> None:
    wheel = build_wheel("demo-pkg", "1.0", {"demo_pkg/__init__.py": "X = 1\n"}, tmp_path)
    with zipfile.ZipFile(wheel) as zf:
        names = set(zf.namelist())
    assert "demo_pkg-1.0.dist-info/RECORD" in names
    assert "demo_pkg-1.0.dist-info/METADATA" in names


def test_tamper_changes_every_hash() -> None:
    digest = "a" * 64
    text = f"idna==3.20 \\\n    --hash=sha256:{digest} \\\n    --hash=sha256:{'0' * 64}\n"
    new_text, count = tamper(text)
    assert count == 2
    assert digest not in new_text
    assert flip_first_hex("0" * 64).startswith("1")


def test_typosquat_detection() -> None:
    names = parse_names("reqeusts==2.0\nrequests>=2\n# comment\n-r other.txt\nnumpyy\n")
    assert names == ["reqeusts", "requests", "numpyy"]
    assert suspicious("reqeusts") == ["requests"]
    assert suspicious("requests") == []


def test_build_wheel_is_reproducible(tmp_path: Path) -> None:
    first = build_wheel("demo-pkg", "1.0", {"demo_pkg/__init__.py": "X = 1\n"}, tmp_path / "a")
    second = build_wheel("demo-pkg", "1.0", {"demo_pkg/__init__.py": "X = 1\n"}, tmp_path / "b")
    assert first.read_bytes() == second.read_bytes()
