# Python dependency security — hands-on demo

Six short exercises for a class talk / self-study: from “pip-audit found a CVE” to “why `pip install` runs other people’s code”.

Everything runs **locally**. No packages are published. The “dangerous” packages in exercises 4–5 are homemade and harmless (print a line / write a text file under `%TEMP%` / `/tmp`).

**Primary tools:** [pip-audit](https://pypi.org/project/pip-audit/), [Safety](https://docs.safetycli.com/), [Dependabot](https://docs.github.com/en/code-security/dependabot) (+ Dependency Review + a pip-audit CI gate).

**Secondary:** pipdeptree, pip-tools hashes, install-time / `.pth` demos, dependency-confusion simulation.

| | |
|---|---|
| Python | ≥ 3.11 (checked on 3.13.5) |
| OS | Windows (PowerShell) primary; macOS/Linux notes inline |
| Network | PyPI + vulnerability DB APIs |
| Time | ~10 minutes per exercise |

Advisory databases change daily. Exact IDs/counts may differ from the sample outputs — that is expected.

---

## Quick start (Windows PowerShell)

All commands below assume you are in the **repository root** of this demo (the folder that contains `ex1_known_vulns/`).

```powershell
# Prefer `python` from PATH (need >= 3.11). Check: python --version
# If bare `py` is broken on your machine, pin for this session:  $env:PY_PYTHON = "3.13"

python -m venv .venv-tools
.\.venv-tools\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pip-audit pipdeptree pip-tools
```

**macOS / Linux:**

```bash
python3 -m venv .venv-tools
source .venv-tools/bin/activate
python -m pip install --upgrade pip
python -m pip install pip-audit pipdeptree pip-tools
```

On Windows, venv binaries are under `.\.venv-X\Scripts\` (not `bin/`). After `Activate.ps1`, you can call tools by name (`pip-audit`, `safety`, …).

Clean local artifacts anytime:

```powershell
.\scripts\clean_demo.ps1
# macOS/Linux: bash scripts/clean_demo.sh
```

---

## Layout

```
.
├── README.md
├── .github/                          ← Dependabot + CI (active when this repo is on GitHub)
├── scripts/                          ← helpers + clean_demo
├── ex1_known_vulns/                  ← pip-audit / Safety / Bandit
├── ex2_transitive/                   ← transitive vulns, pipdeptree, re-lock
├── ex3_hashes/                       ← --require-hashes
├── ex4_install_time/                 ← setup.py at install; .pth at interpreter start
├── ex5_confusion_typosquatting/      ← dependency confusion + typosquat check
└── ex6_dependabot/                   ← pointer to root .github/
```

---

## Exercise 1 — Known vulnerabilities (pip-audit, Safety)

**Goal:** old pins → scanner reports advisories → upgrade → clean.

`ex1_known_vulns/requirements.txt` (vulnerable on purpose):

```
requests==2.31.0
jinja2==3.1.2
```

The file is named `requirements.txt` so **Safety** and **Dependabot** discover it. (`safety scan` ignores names like `requirements-vulnerable.txt`.)

### 1a. pip-audit (no account)

```powershell
cd ex1_known_vulns
pip-audit -r requirements.txt                 # expect findings, exit code 1
pip-audit -r requirements.txt --desc          # + short descriptions
pip-audit -r requirements.txt -s osv          # OSV instead of PyPI JSON API
pip-audit -r requirements-fixed.txt           # expect: No known vulnerabilities found, exit 0
```

Sample shape (IDs/counts drift over time):

```
Found 16 known vulnerabilities in 2 packages
Name     Version ID              Fix Versions
requests 2.31.0  PYSEC-...       2.32.0
jinja2   3.1.2   PYSEC-...       3.1.3
...
```

**What to notice**

- Exit code **1** when findings exist → usable as a CI gate.
- Duplicate rows are often the same issue under GHSA + PYSEC aliases. Count unique CVE/GHSA groups, not raw lines.
- `-r` **resolves** deps in a temporary venv (can run build code for sdists). For a fully pinned lock, prefer `--no-deps --disable-pip` (see exercise 2).

Autofix (writes the file):

```powershell
copy requirements.txt req-fixme.txt
pip-audit -r req-fixme.txt --fix
# bumps to the *minimum* versions that close known advisories, not necessarily latest
```

### 1b. Safety (account required for `scan`)

```powershell
# separate venv (from demo root)
python -m venv .venv-safety
.\.venv-safety\Scripts\python.exe -m pip install --upgrade pip
.\.venv-safety\Scripts\python.exe -m pip install safety

# one-time auth (opens browser)
.\.venv-safety\Scripts\safety.exe auth register    # or: auth login
.\.venv-safety\Scripts\safety.exe auth status
```

Scan the exercise folder. The file **must** be named `requirements.txt` (Safety ignores other `requirements-*.txt` names).

```powershell
cd ex1_known_vulns
..\.venv-safety\Scripts\safety.exe scan
```

The first scan may ask to link a Safety Platform codebase — answer `y`. After that, a local `.safety-project.ini` appears (gitignored).

Expected when authenticated: findings on `requests` and `jinja2` (~8 issues), exit code 64.

Without an account, `safety scan` asks you to log in. The legacy command still works against the open-source DB (deprecated):

```powershell
..\.venv-safety\Scripts\safety.exe check -r requirements.txt
# expect ~8 vulnerabilities, exit code 64
```

### 1c. Bandit (your code, not dependencies)

```powershell
..\.venv-safety\Scripts\python.exe -m pip install bandit
..\.venv-safety\Scripts\bandit.exe -q app.py
```

Bandit flags `shell=True` in `app.py`. It knows nothing about CVE pins; pip-audit/Safety know nothing about `shell=True`. Different jobs.

---

## Exercise 2 — Transitive dependencies

**Goal:** a “clean” direct pin can still pull vulnerable transitive packages via an old lock.

```powershell
cd ex2_transitive
pip-audit -r requirements-lock-2024.txt --no-deps --disable-pip   # audit lock as-is

python -m venv ..\.venv-ex2
..\.venv-ex2\Scripts\python.exe -m pip install -r requirements-lock-2024.txt
pipdeptree --python ..\.venv-ex2\Scripts\python.exe
pipdeptree --python ..\.venv-ex2\Scripts\python.exe -r -p urllib3,idna

pip-compile --upgrade --strip-extras requirements.in -o requirements-lock-fresh.txt
pip-audit -r requirements-lock-fresh.txt --no-deps --disable-pip   # expect clean
```

You never typed `urllib3` / `idna` / `certifi` yourself — `requests` declared version *ranges*. Your lock chose the concrete versions, so the lock owns transitive risk.

---

## Exercise 3 — Hashes

**Goal:** hashes stop *artifact substitution* after lock; they do not prove the locked version was safe.

```powershell
cd ex3_hashes
pip-compile --generate-hashes --strip-extras requirements.in -o requirements.txt

python -m venv ..\.venv-ex3
..\.venv-ex3\Scripts\python.exe -m pip install --require-hashes -r requirements.txt   # OK

python ..\scripts\tamper_hash.py requirements.txt
python -m venv --clear ..\.venv-ex3
..\.venv-ex3\Scripts\python.exe -m pip install --no-cache-dir --require-hashes -r requirements-tampered.txt
# expect: THESE PACKAGES DO NOT MATCH THE HASHES...
```

---

## Exercise 4 — Install-time code execution

**Goal:** (a) installing an **sdist** runs `setup.py` / the build backend; (b) a **wheel** can drop a `.pth` that runs on every Python start—no `import` needed.

```powershell
# from demo root
python -m venv .venv-ex4
.\.venv-ex4\Scripts\python.exe -m pip install build
.\.venv-ex4\Scripts\python.exe -m build --sdist ex4_install_time\hello_install_hook --outdir ex4_install_time\dist

# wheels only → cannot install (no wheel present)
.\.venv-ex4\Scripts\python.exe -m pip install --only-binary :all: --no-index --find-links ex4_install_time\dist hello-install-hook

# sdist → setup.py runs (proof file under %TEMP%)
.\.venv-ex4\Scripts\python.exe -m pip install -v ex4_install_time\dist\hello_install_hook-0.1.0.tar.gz
python -c "import tempfile,pathlib; print((pathlib.Path(tempfile.gettempdir())/'PROOF_setup_py_was_executed.txt').read_text())"

# .pth hook
python scripts\build_pth_wheel.py
.\.venv-ex4\Scripts\python.exe -m pip install ex4_install_time\dist\pth_demo-0.1.0-py3-none-any.whl
.\.venv-ex4\Scripts\python.exe -c "print('2+2 =', 2+2)"
# expect a [pth_demo] line before 2+2 (may print twice; site can visit site-packages twice)
.\.venv-ex4\Scripts\python.exe -m pip uninstall -y pth-demo
```

---

## Exercise 5 — Dependency confusion & typosquatting (local simulation)

**Goal:** with `--extra-index-url`, pip picks the **best version across all indexes** (no private-index priority). Pin + hash (or uv first-index) blocks the impostor.

```powershell
python scripts\build_local_indexes.py
# prints two file:///... URLs — copy them into the commands below

python -m venv .venv-ex5
$internal = "file:///D:/path/from/script/indexes/internal/simple"
$public   = "file:///D:/path/from/script/indexes/public/simple"

# confusion: installs 99.0.0 from "public" even if --index-url is internal
.\.venv-ex5\Scripts\python.exe -m pip install --index-url $internal --extra-index-url $public acme-internal-utils
.\.venv-ex5\Scripts\python.exe -c "import acme_internal_utils"

# defense: pin + hash
.\.venv-ex5\Scripts\python.exe -m pip uninstall -y acme-internal-utils
.\.venv-ex5\Scripts\python.exe -m pip install --index-url $internal --extra-index-url $public -r ex5_confusion_typosquatting\requirements-pinned.txt
.\.venv-ex5\Scripts\python.exe -c "import acme_internal_utils"   # → 1.0.0 internal

# typosquat names
python scripts\typosquat_check.py ex5_confusion_typosquatting\requirements-typos.txt
```

Optional with [uv](https://docs.astral.sh/uv/): default index strategy is first-index (safer); `--index-strategy unsafe-best-match` reproduces pip’s behavior.

---

## Dependabot, Dependency Review, and CI

These are **three different layers**. Confusing them is the usual gap.

| Mechanism | When it runs | What it does |
|---|---|---|
| **Dependabot alerts** | After the dependency graph updates, or when a new GitHub Advisory appears | Opens an alert in the Security tab |
| **Dependabot security updates** | After an alert (if enabled) | Opens a PR that bumps to a fixed version |
| **Dependabot version updates** | On the schedule in `.github/dependabot.yml` | Opens PRs for newer versions (with cooldown) |
| **Dependency Review** | On each **pull request** | Diffs dependency changes in that PR and can **block merge** if new vulns appear |
| **pip-audit CI** (`.github/workflows/dependency-audit.yml`) | PR / push / weekly cron | Fails the job when known vulns are in `ex1_known_vulns/requirements.txt` |

This repository already contains:

- `.github/dependabot.yml` — watches `ex1_known_vulns/`
- `.github/workflows/dependency-audit.yml` — pip-audit gate (will **fail** while the demo file stays vulnerable — that is intentional)
- `.github/workflows/dependency-review.yml` — PR dependency review

After the repo is on GitHub, enable under **Settings → Code security**:

1. Dependency graph  
2. Dependabot alerts  
3. Dependabot security updates  

Alerts for `requests` / `jinja2` in `ex1_known_vulns/requirements.txt` should appear once the graph is built (often within minutes on the default branch).

---

## After the exercises

```powershell
.\scripts\clean_demo.ps1
```

Removes `.venv-*`, generated indexes, tampered hash files, Safety project ini, and the temp proof file. Nothing was installed globally.

---

## License

MIT — see `LICENSE`.
