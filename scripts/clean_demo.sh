#!/usr/bin/env bash
# Remove local artifacts produced by running the exercises.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "Cleaning demo artifacts under $ROOT"

for d in .venv-tools .venv-safety .venv-ex2 .venv-ex3 .venv-ex4 .venv-ex5 \
         ex3_hashes/dl ex4_install_time/dist ex5_confusion_typosquatting/indexes; do
  if [[ -e "$d" ]]; then
    rm -rf "$d"
    echo "  removed $d"
  fi
done

for f in ex1_known_vulns/req-fixme.txt ex1_known_vulns/report.json \
         ex1_known_vulns/.safety-project.ini ex3_hashes/requirements-tampered.txt; do
  if [[ -e "$f" ]]; then
    rm -f "$f"
    echo "  removed $f"
  fi
done

PROOF="${TMPDIR:-/tmp}/PROOF_setup_py_was_executed.txt"
if [[ -e "$PROOF" ]]; then
  rm -f "$PROOF"
  echo "  removed $PROOF"
fi

echo "Done. Re-create tool venvs with the README setup section when you need them again."
