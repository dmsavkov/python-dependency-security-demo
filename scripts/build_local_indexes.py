"""Exercise 5: build two LOCAL package indexes (PEP 503 "simple" layout) to simulate dependency confusion.

* ``indexes/internal`` - your "company" index with the real ``acme-internal-utils==1.0.0``
* ``indexes/public``   - an "attacker-controlled public" index with ``acme-internal-utils==99.0.0``

Both packages are harmless: importing them only prints which copy you got. Everything stays on disk.
"""

from __future__ import annotations

import html
from pathlib import Path

from wheelkit import build_wheel, normalize, sha256_file

PACKAGE = "acme-internal-utils"


def _module_source(origin: str, version: str) -> str:
    banner = 'print(f"[acme_internal_utils] imported {VERSION} from the {ORIGIN} index")'
    return f'ORIGIN = "{origin}"\nVERSION = "{version}"\n{banner}\n'


def _page(body: str) -> str:
    return f"<!DOCTYPE html>\n<html><body>\n{body}\n</body></html>\n"


def write_index(root: Path, project: str, wheel: Path) -> None:
    """Write ``root/simple/index.html`` and ``root/simple/<project>/index.html`` (with a sha256 fragment)."""
    simple = root / "simple"
    proj_dir = simple / normalize(project)
    proj_dir.mkdir(parents=True, exist_ok=True)
    target = proj_dir / wheel.name
    target.write_bytes(wheel.read_bytes())
    wheel.unlink()
    digest = sha256_file(target)
    link = f'<a href="{html.escape(target.name)}#sha256={digest}">{html.escape(target.name)}</a>'
    (proj_dir / "index.html").write_text(_page(link), encoding="utf-8")
    root_link = f'<a href="{normalize(project)}/">{normalize(project)}</a>'
    (simple / "index.html").write_text(_page(root_link), encoding="utf-8")


def main() -> None:
    base = Path(__file__).resolve().parent.parent / "ex5_confusion_typosquatting" / "indexes"
    for origin, version in (("internal", "1.0.0"), ("PUBLIC (impostor!)", "99.0.0")):
        folder = base / ("internal" if origin == "internal" else "public")
        wheel = build_wheel(
            name=PACKAGE,
            version=version,
            files={"acme_internal_utils/__init__.py": _module_source(origin, version)},
            out_dir=folder / "_build",
            summary=f"Harmless dependency-confusion demo ({origin})",
        )
        write_index(folder, PACKAGE, wheel)
        (folder / "_build").rmdir()
        print(f"{origin:>20}: {PACKAGE}=={version}  ->  {(folder / 'simple').as_uri()}")
    print("\nCopy the two file:// URLs above into the commands from README (exercise 5).")


if __name__ == "__main__":
    main()
