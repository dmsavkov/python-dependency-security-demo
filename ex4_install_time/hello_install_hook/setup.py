"""Exercise 4a: a HARMLESS legacy-style package whose setup.py runs code at BUILD/INSTALL time.

When pip installs this from source (a directory or an sdist .tar.gz), the build backend (setuptools)
executes this file. A malicious package could run anything here; we only write a proof file into the
system temp directory and print a message.
"""

from __future__ import annotations

import datetime
import getpass
import os
import sys
import tempfile
from pathlib import Path

from setuptools import setup

proof = Path(tempfile.gettempdir()) / "PROOF_setup_py_was_executed.txt"
proof.write_text(
    f"setup.py ran at {datetime.datetime.now().isoformat(timespec='seconds')}\n"
    f"user={getpass.getuser()} python={sys.executable}\n"
    f"argv={sys.argv}\n"
    f"setup.py location: {Path(__file__).resolve()}\n"
    f"it could also read: {len(os.environ)} environment variables (we only counted them)\n",
    encoding="utf-8",
)
print(f"[hello-install-hook] setup.py is running! proof written to {proof}", file=sys.stderr)

setup(
    name="hello-install-hook",
    version="0.1.0",
    description="Harmless demo: code execution at install time",
    py_modules=["hello_install_hook"],
)
