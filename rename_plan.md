# Package Rename Plan: `reconsadfc` → `reconformal`

**Prepared:** 2026-05-27  
**Scope:** Rename the Python package, PyPI distribution, ReadTheDocs project, and GitHub repository from `reconsadfc` to `reconformal`.  
**Current version:** 0.1.0 (tag `v0.1.0` on PyPI and GitHub)  
**Principle:** No code changes are made speculatively. Every step below must be executed in order; later steps depend on earlier ones.

---

## 1. Pre-Rename Audit

### 1.1 Files that contain the string `reconsadfc`

| File | Occurrences | Nature of change required |
|---|---|---|
| `pyproject.toml` | 6 | Package name, CLI entry-point, package discovery, URLs |
| `README.md` | ~18 | Title, badges, install instructions, import examples, CLI usage, project structure table |
| `reconsadfc/__init__.py` | 2 | Docstring, relative import of `reconsadfc.py` |
| `reconsadfc/__main__.py` | 2 | Docstring, relative import of `reconsadfc.py` |
| `reconsadfc/reconsadfc.py` | 0 | No self-references — file rename only |
| `tests/test_plaso_to_footprint.py` | 1 | Absolute import `from reconsadfc.reconsadfc import ...` |
| `tests/test_correlation_calculator.py` | 1 | Absolute import `from reconsadfc.reconsadfc import ...` |
| `tests/test_entity_extractor.py` | 1 | Absolute import `from reconsadfc.reconsadfc import ...` |
| `tests/test_relationship_manager.py` | 1 | Absolute import `from reconsadfc.reconsadfc import ...` |
| `tests/test_data_processor.py` | 3 | Absolute imports + `mocker.patch` target path strings |
| `docs/source/conf.py` | 1 | `project = 'reconsadfc'` |
| `docs/source/index.rst` | 7 | Title, badges, description text |
| `docs/source/installation.rst` | 4 | Install commands, clone URL, descriptive text |
| `docs/source/quickstart.rst` | 6 | Import examples, CLI commands, descriptive text |
| `docs/source/api.rst` | 1 | `automodule:: reconsadfc.reconsadfc` directive |
| `.github/workflows/publish.yml` | 1 | PyPI project URL in environment block |
| `.gitignore` | 2 | Paths referencing `reconsadfc/reconformal_outputs` |
| `.readthedocs.yaml` | 0 | No name references — no change required |
| `docs/Makefile` | 0 | No name references — no change required |
| `docs/make.bat` | 0 | No name references — no change required |

### 1.2 Filesystem paths that carry the old name

| Current path | New path |
|---|---|
| `D:\kp\reconsadfc\reconsadfc\` (package directory) | `D:\kp\reconsadfc\reconformal\` |
| `D:\kp\reconsadfc\reconsadfc\reconsadfc.py` (core module) | `D:\kp\reconsadfc\reconformal\reconformal.py` |
| `D:\kp\reconsadfc\reconsadfc\__init__.py` | `D:\kp\reconsadfc\reconformal\__init__.py` |
| `D:\kp\reconsadfc\reconsadfc\__main__.py` | `D:\kp\reconsadfc\reconformal\__main__.py` |
| Repository root directory (`D:\kp\reconsadfc\`) | Optionally rename to `D:\kp\reconformal\` after all changes are committed (see §5) |

### 1.3 Notable observations from the audit

- **`reconsadfc.py` is clean:** The core source file contains zero self-references to the package name. Only its filename and directory placement require changing.
- **`__pycache__` entries:** `reconsadfc\__pycache__\reconformal.cpython-314.pyc` already exists, suggesting the module was previously imported under that name in a local experiment. All `__pycache__` directories must be deleted before the rename; they are regenerated automatically by Python.
- **`.gitignore` inconsistency:** Lines 5–6 are identical (`/reconsadfc/reconformal_outputs`), both referencing `reconformal_outputs` inside the old package directory. After the package directory is renamed, these paths will need updating to `/reconformal/reconformal_outputs`. The duplicate line should also be removed.
- **`reconformal_outputs/` data directory:** This subdirectory inside `reconsadfc/reconsadfc/` contains generated CSV artifacts. It will be physically moved with the parent directory rename. It is already gitignored, so it poses no versioning issue.
- **`docs/source/installation.rst` anomaly:** Line 23 reads `cd temp-reconformal` — an apparent leftover from a prior local experiment. Update it to `cd reconformal`.
- **`docs/source/conf.py` uses `html_theme = 'alabaster'`** while `docs/requirements.txt` pins `sphinx-rtd-theme`. The theme inconsistency is pre-existing and out of scope, but worth noting.
- **GitHub repository name:** Currently `forensic-timeline/reconsadfc` — must be renamed to `forensic-timeline/reconformal` via GitHub Settings to keep URLs consistent. All git remote references will need updating afterward.
- **ReadTheDocs project slug:** Must be changed from `reconsadfc` to `reconformal` in the RTD dashboard. The existing build URL (`https://reconsadfc.readthedocs.io`) should be set to redirect to the new slug.

---

## 2. Local File Changes

Execute steps in the order shown. Do not skip steps; some depend on the previous state.

### Step 2.1 — Delete all `__pycache__` directories

Stale bytecode will cause import confusion after the directory rename.

```powershell
# From the repo root D:\kp\reconsadfc
Get-ChildItem -Recurse -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
Get-ChildItem -Recurse -Filter "*.pyo" | Remove-Item -Force
```

### Step 2.2 — Rename the package directory and core module file

```powershell
# Rename the package directory
Rename-Item -Path "D:\kp\reconsadfc\reconsadfc" -NewName "reconformal"

# Rename the core module file inside it
Rename-Item -Path "D:\kp\reconsadfc\reconformal\reconsadfc.py" -NewName "reconformal.py"
```

### Step 2.3 — Update `reconformal/__init__.py`

**File:** `reconformal/__init__.py`

Replace:
```python
"""Public package exports for reconsadfc."""

from .reconsadfc import (
```
With:
```python
"""Public package exports for reconformal."""

from .reconformal import (
```

No other changes needed in this file; `__all__` exports class/function names that are not being renamed.

### Step 2.4 — Update `reconformal/__main__.py`

**File:** `reconformal/__main__.py`

Replace:
```python
"""Module execution entry point for python -m reconsadfc."""

from .reconsadfc import main
```
With:
```python
"""Module execution entry point for python -m reconformal."""

from .reconformal import main
```

### Step 2.5 — Update `pyproject.toml`

Apply the following changes (every occurrence of `reconsadfc` in the file):

| Line | Old value | New value |
|---|---|---|
| `name =` | `"reconsadfc"` | `"reconformal"` |
| `Homepage =` | `"https://github.com/forensic-timeline/reconsadfc"` | `"https://github.com/forensic-timeline/reconformal"` |
| `Repository =` | `"https://github.com/forensic-timeline/reconsadfc"` | `"https://github.com/forensic-timeline/reconformal"` |
| `Issues =` | `"https://github.com/forensic-timeline/reconsadfc/issues"` | `"https://github.com/forensic-timeline/reconformal/issues"` |
| `[project.scripts]` entry | `reconsadfc = "reconsadfc.reconsadfc:main"` | `reconformal = "reconformal.reconformal:main"` |
| `include =` | `["reconsadfc*"]` | `["reconformal*"]` |

**Result:**
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "reconformal"
version = "0.2.0"
description = "Forensic event reconstruction and timeline correlation for SADFC-style data"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [
  { name = "Muhammad Nur Yasir Utomo, Hudan Studiawan, Arkananta Masarief, Kemal Tangguh Aji Rajasa" }
]
keywords = ["forensics", "timeline", "incident-response", "sadfc", "pandas"]
classifiers = [
  "Development Status :: 3 - Alpha",
  "Intended Audience :: Developers",
  "Intended Audience :: Information Technology",
  "License :: OSI Approved :: MIT License",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3 :: Only",
  "Programming Language :: Python :: 3.9",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Topic :: Security",
  "Topic :: Scientific/Engineering :: Information Analysis",
]
dependencies = [
  "pandas>=1.5",
  "matplotlib>=3.6",
]

[project.optional-dependencies]
test = [
    "pytest",
    "pytest-mock",
]
docs = [
    "sphinx",
    "sphinx-rtd-theme",
]

[project.urls]
Homepage = "https://github.com/forensic-timeline/reconformal"
Repository = "https://github.com/forensic-timeline/reconformal"
Issues = "https://github.com/forensic-timeline/reconformal/issues"

[project.scripts]
reconformal = "reconformal.reconformal:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["reconformal*"]

[tool.pytest.ini_options]
pythonpath = [
  "."
]
```

> **Version bump note:** Bump the version to `0.2.0` at this point. This is the release that introduces the rename. Using a new version number ensures users who run `pip install --upgrade reconformal` receive the latest build and clearly distinguishes it from the deprecated stub (see §3).

### Step 2.6 — Update all test files

All five test files import from `reconsadfc.reconsadfc`. Replace every import and `mocker.patch` target path:

**Pattern to replace (all test files):**
```
reconsadfc.reconsadfc.
```
**Replace with:**
```
reconformal.reconformal.
```

**Pattern to replace (import statements only):**
```
from reconsadfc.reconsadfc import
```
**Replace with:**
```
from reconformal.reconformal import
```

Specific files and exact strings:

- `tests/test_plaso_to_footprint.py` line 3: `from reconsadfc.reconsadfc import PlasoToFootprint`
- `tests/test_correlation_calculator.py` line 3: `from reconsadfc.reconsadfc import Correlation_Calculator`
- `tests/test_entity_extractor.py` line 3: `from reconsadfc.reconsadfc import EntityExtractor, KnowledgeRepresentation`
- `tests/test_relationship_manager.py` line 3: `from reconsadfc.reconsadfc import RelationshipManager`
- `tests/test_data_processor.py` line 5: `from reconsadfc.reconsadfc import DataProcessor`
- `tests/test_data_processor.py` line 14: `mocker.patch("reconsadfc.reconsadfc.PlasoToFootprint.process_csv", ...)`
- `tests/test_data_processor.py` line 47: `mocker.patch("reconsadfc.reconsadfc.PlasoToFootprint.process_csv", ...)`

### Step 2.7 — Update `docs/source/conf.py`

Replace:
```python
project = 'reconsadfc'
```
With:
```python
project = 'reconformal'
```

### Step 2.8 — Update `docs/source/api.rst`

Replace:
```rst
.. automodule:: reconsadfc.reconsadfc
```
With:
```rst
.. automodule:: reconformal.reconformal
```

### Step 2.9 — Update `docs/source/index.rst`

All seven occurrences of `reconsadfc` must change:

- Line 1: `.. reconsadfc documentation master file` → `.. reconformal documentation master file`
- Line 3: `Welcome to reconsadfc's documentation!` → `Welcome to reconformal's documentation!`
  - Also update the RST header underline (`=` characters) to match the new title length (35 characters vs 40 — adjust the `=` row accordingly)
- Lines 6–9: Replace all four PyPI badge URLs: `reconsadfc` → `reconformal`
- Line 15: Replace `reconsadfc` (2 occurrences in the prose paragraph) → `reconformal`

### Step 2.10 — Update `docs/source/installation.rst`

- Line 4 (prose): `reconsadfc` → `reconformal`
- Line 13 (code block): `pip install reconsadfc` → `pip install reconformal`
- Line 22 (code block): `git clone https://github.com/forensic-timeline/reconsadfc.git` → `git clone https://github.com/forensic-timeline/reconformal.git`
- Line 23 (code block): `cd temp-reconformal` → `cd reconformal` (fixes the pre-existing stale path)

### Step 2.11 — Update `docs/source/quickstart.rst`

- Line 4 (prose): `` `reconsadfc` `` → `` `reconformal` ``
- Lines 13–18 (code block): `from reconsadfc import (` → `from reconformal import (`
- Line 54 (prose): `` `reconsadfc` `` → `` `reconformal` ``
- Line 59 (code block): `reconsadfc --input-dir ...` → `reconformal --input-dir ...`
- Line 65 (code block): `python -m reconsadfc ...` → `python -m reconformal ...`

### Step 2.12 — Update `README.md`

All ~18 occurrences must be replaced. Key substitutions:

- Title `# reconsadfc` → `# reconformal`
- All three PyPI badge URLs: replace `reconsadfc` with `reconformal`
- `pip install reconsadfc` → `pip install reconformal`
- `git clone https://github.com/forensic-timeline/reconsadfc` → `git clone https://github.com/forensic-timeline/reconformal`
- `cd reconsadfc` → `cd reconformal`
- All `from reconsadfc import` → `from reconformal import`
- `from reconsadfc.reconsadfc import` → `from reconformal.reconformal import`
- CLI examples: `reconsadfc --input-dir ...` → `reconformal --input-dir ...`
- `python -m reconsadfc ...` → `python -m reconformal ...`
- Project structure table: `reconsadfc/reconsadfc.py`, `reconsadfc/__main__.py`, `reconsadfc/__init__.py` → `reconformal/reconformal.py`, `reconformal/__main__.py`, `reconformal/__init__.py`

### Step 2.13 — Update `.gitignore`

Current lines 5–6 are identical duplicates. Replace both with a single corrected line:

Old content (lines 5–6):
```
/reconsadfc/reconformal_outputs
/reconsadfc/reconformal_outputs
```
New content:
```
/reconformal/reconformal_outputs
```

### Step 2.14 — Update `.github/workflows/publish.yml`

Line 40: Replace the PyPI environment URL:
```yaml
      url: https://pypi.org/p/reconsadfc
```
With:
```yaml
      url: https://pypi.org/p/reconformal
```

### Step 2.15 — Verify no remaining occurrences

After completing all edits above, run a final check to confirm no tracked files still contain `reconsadfc` (excluding `.git/` internals and the rename plan itself):

```powershell
# From repo root
git grep -r "reconsadfc" -- ":(exclude).git" ":(exclude)rename_plan.md"
```

The only expected match at this point is inside `rename_plan.md` (this document). If any other file appears, resolve it before proceeding.

---

## 3. PyPI Considerations

### Step 3.1 — Publish `reconformal` as a new package

1. Build the distribution from the updated `pyproject.toml`:
   ```powershell
   python -m pip install --upgrade build twine
   python -m build
   ```
2. Verify the built wheel and sdist in `dist/`:
   - Wheel name should be `reconformal-0.2.0-py3-none-any.whl`
   - Source tarball should be `reconformal-0.2.0.tar.gz`
3. Upload to PyPI:
   ```powershell
   python -m twine upload dist/reconformal-0.2.0*
   ```
   Or use the GitHub Actions `publish.yml` workflow by pushing a `v0.2.0` tag after committing all changes.

### Step 3.2 — Create a deprecation stub for `reconsadfc`

Users who still have `pip install reconsadfc` in their scripts must be guided to the new name. Publish a final `reconsadfc` release that installs `reconformal` as a dependency and prints a deprecation warning at import time.

**Create a minimal stub `pyproject.toml` in a separate directory (e.g., `reconsadfc-stub/`):**

```toml
[project]
name = "reconsadfc"
version = "0.2.0"
description = "Deprecated: this package has been renamed to reconformal. Install reconformal instead."
dependencies = ["reconformal>=0.2.0"]
```

**Create `reconsadfc-stub/reconsadfc/__init__.py`:**
```python
import warnings
warnings.warn(
    "The package 'reconsadfc' has been renamed to 'reconformal'. "
    "Please update your dependency: pip install reconformal. "
    "This stub will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)
from reconformal import *  # noqa: F401, F403
from reconformal import __all__  # noqa: F401
```

Build and publish the stub to PyPI:
```powershell
cd reconsadfc-stub
python -m build
python -m twine upload dist/reconsadfc-0.2.0*
```

> **Important:** You must be the owner of the `reconsadfc` PyPI project to upload this. This stub approach is preferable to yanking because it actively redirects users rather than breaking their installs silently.

### Step 3.3 — Consider yanking old `reconsadfc` releases (optional)

PyPI's yank mechanism marks a specific release as not to be installed by default (unless explicitly pinned). Use it to discourage installation of `reconsadfc` versions prior to the stub:

```powershell
# Requires pypi-yank or manual action via the PyPI web interface
# Navigate to: https://pypi.org/manage/project/reconsadfc/releases/
# Yank version 0.1.0 with message: "Package renamed to reconformal"
```

Yanking `0.1.0` means `pip install reconsadfc` will only resolve to the `0.2.0` stub (which then installs `reconformal`). Users with `reconsadfc==0.1.0` pinned will see a warning but still get the old version.

### Step 3.4 — Update PyPI project description for `reconsadfc`

Through the PyPI web interface, add a prominent deprecation notice in the `reconsadfc` project description pointing users to `reconformal`.

---

## 4. ReadTheDocs Considerations

### Step 4.1 — Rename the ReadTheDocs project

1. Log in to [readthedocs.org](https://readthedocs.org).
2. Navigate to the `reconsadfc` project dashboard.
3. Go to **Admin → Settings**.
4. Change the **Name** field from `reconsadfc` to `reconformal`.
5. The **slug** (URL identifier) will change from `reconsadfc` to `reconformal`.
   - Old URL: `https://reconsadfc.readthedocs.io`
   - New URL: `https://reconformal.readthedocs.io`

> **Note:** ReadTheDocs does not automatically set up redirects when you rename a project slug. You must configure redirects manually (see Step 4.2).

### Step 4.2 — Configure redirects on ReadTheDocs

In the RTD project settings for the renamed `reconformal` project:

1. Go to **Admin → Redirects**.
2. Add a **Domain Redirect** (or **Page Redirect**) from the old domain:
   - **From:** `https://reconsadfc.readthedocs.io/`
   - **To:** `https://reconformal.readthedocs.io/`
   - Type: **Domain Redirect** (redirects the entire old domain)

If RTD's built-in redirect feature is insufficient, consider requesting the rename through RTD support — they can retain the old slug as an alias for a period.

### Step 4.3 — Update `.readthedocs.yaml` if needed

The current `.readthedocs.yaml` does not reference the project name directly, so **no change is needed** to this file. Verify that the `sphinx.configuration` path (`docs/conf.py`) remains valid after any file moves — it currently points to `docs/conf.py` but the actual file is at `docs/source/conf.py`. This is a **pre-existing misconfiguration** that should be corrected:

```yaml
# Current (incorrect path):
sphinx:
  configuration: docs/conf.py

# Correct path:
sphinx:
  configuration: docs/source/conf.py
```

Fix this while making the other changes. This is a bug fix, not part of the rename itself, but the rename is a natural opportunity to correct it.

### Step 4.4 — Connect RTD to the renamed GitHub repository

After renaming the GitHub repository (Step 5.3), the RTD webhook integration will break. Reconnect it:

1. In the RTD project's **Admin → Integrations**, delete the old GitHub webhook.
2. Add a new GitHub webhook pointing to `forensic-timeline/reconformal`.
3. Alternatively, RTD may auto-detect the new repo URL if the GitHub OAuth connection is active.

### Step 4.5 — Trigger a fresh RTD build

After reconnecting the webhook and merging the rename commit:

1. Manually trigger a build from the RTD dashboard for the `reconformal` project.
2. Verify the build succeeds and all docs render correctly.
3. Confirm the `automodule:: reconformal.reconformal` directive resolves properly.

---

## 5. Git and Version Control Steps

### Step 5.1 — Stage all changed and renamed files

```powershell
# From D:\kp\reconsadfc
git add -A
```

> Using `-A` is appropriate here because the rename constitutes the bulk of all changes. Review `git status` output before committing to ensure no unintended files are staged.

### Step 5.2 — Commit the rename

```powershell
git commit -m "feat: rename package from reconsadfc to reconformal

- Rename reconsadfc/ package directory to reconformal/
- Rename reconsadfc.py core module to reconformal.py
- Update all imports, entry points, and references throughout codebase
- Update pyproject.toml: package name, scripts, discovery, URLs
- Update all test files to import from reconformal.reconformal
- Update Sphinx conf.py, RST docs, and README
- Update GitHub Actions publish workflow URL
- Fix .gitignore duplicate entry and update path
- Fix .readthedocs.yaml sphinx configuration path (docs/source/conf.py)
- Bump version to 0.2.0

Closes: [issue number if applicable]"
```

### Step 5.3 — Rename the GitHub repository

1. Navigate to `https://github.com/forensic-timeline/reconsadfc`.
2. Go to **Settings → General**.
3. Under **Repository name**, change `reconsadfc` to `reconformal`.
4. Click **Rename**.

GitHub will automatically create redirects from the old URL to the new one for all HTTP traffic (web browsing and `git clone`). However, existing local clones will have a stale remote URL.

### Step 5.4 — Update the local git remote URL

```powershell
git remote set-url origin https://github.com/forensic-timeline/reconformal.git
```

Verify:
```powershell
git remote -v
# Should show: origin  https://github.com/forensic-timeline/reconformal.git
```

### Step 5.5 — Push to GitHub

```powershell
git push origin main
```

### Step 5.6 — Create and push the version tag

```powershell
git tag v0.2.0
git push origin v0.2.0
```

Pushing the `v0.2.0` tag will trigger the `publish.yml` GitHub Actions workflow, which will build and publish `reconformal-0.2.0` to PyPI automatically.

### Step 5.7 — Rename root directory (optional, last step)

The local checkout directory is still named `reconsadfc`. This does not affect functionality, but for hygiene you may rename it:

```powershell
# Exit the directory first, then rename
Rename-Item -Path "D:\kp\reconsadfc" -NewName "reconformal"
```

This is purely cosmetic and should be done last, after all git operations and verification are complete.

---

## 6. Post-Rename Verification Checklist

Work through this checklist top-to-bottom. Each item should be verified before marking as complete.

### 6.1 Local environment verification

- [ ] **Fresh install test:** In a clean virtual environment, run `pip install -e .` from the renamed repo root. Confirm it installs without errors.
- [ ] **CLI entry point:** Run `reconformal --help`. Confirm the command exists and displays usage.
- [ ] **Module invocation:** Run `python -m reconformal --help`. Confirm it works.
- [ ] **Import test:** Run `python -c "import reconformal; print(reconformal.__all__)"`. Confirm all expected symbols appear.
- [ ] **No old name importable:** Run `python -c "import reconsadfc"`. Confirm `ModuleNotFoundError` is raised (not the reconformal content — unless the stub is installed).
- [ ] **Test suite passes:** Run `pytest tests/ -v`. All tests should pass with zero collection errors.
- [ ] **Docs build locally:** Run `sphinx-build -b html docs/source docs/build/html`. Confirm no errors, especially that the `automodule:: reconformal.reconformal` directive resolves all members.

### 6.2 PyPI verification

- [ ] **`reconformal` package appears on PyPI:** Visit `https://pypi.org/project/reconformal/`. Confirm version 0.2.0 is listed.
- [ ] **PyPI install works:** In a fresh virtual environment, run `pip install reconformal`. Confirm it installs cleanly.
- [ ] **`reconsadfc` stub on PyPI:** Visit `https://pypi.org/project/reconsadfc/`. Confirm version 0.2.0 stub is listed.
- [ ] **Stub install redirects correctly:** Run `pip install reconsadfc`. Confirm `reconformal` is pulled in as a dependency. Confirm the deprecation warning fires when `import reconsadfc` is executed.
- [ ] **Old `0.1.0` release yanked:** On the PyPI `reconsadfc` project page, confirm `0.1.0` shows a yank warning.

### 6.3 GitHub verification

- [ ] **Repository renamed:** Visit `https://github.com/forensic-timeline/reconformal`. Confirm the repository loads.
- [ ] **Old URL redirects:** Visit `https://github.com/forensic-timeline/reconsadfc`. Confirm GitHub redirects to the new URL.
- [ ] **GitHub Actions triggered:** In the `reconformal` repo, go to **Actions**. Confirm the `publish.yml` workflow ran successfully on `v0.2.0` tag push.
- [ ] **Test workflow runs cleanly:** Confirm the `test.yml` workflow passes on the `main` branch.

### 6.4 ReadTheDocs verification

- [ ] **RTD build succeeds:** Visit the `reconformal` project on RTD and confirm the latest build is passing.
- [ ] **Docs render correctly:** Visit `https://reconformal.readthedocs.io`. Confirm all pages load, including the API reference.
- [ ] **Old URL redirects:** Visit `https://reconsadfc.readthedocs.io`. Confirm redirect to `https://reconformal.readthedocs.io`.

### 6.5 No stale references remain

- [ ] **grep check on repo:** Run `git grep reconsadfc` from the repo root. The only permitted match is this `rename_plan.md` file. Any other hit indicates a missed substitution.
- [ ] **PyPI badge URLs in README work:** Click the README badges in GitHub's rendered view. Confirm they resolve to the `reconformal` PyPI project.
- [ ] **Sphinx conf.py path correct:** Confirm `.readthedocs.yaml` `sphinx.configuration` points to `docs/source/conf.py` (not `docs/conf.py`).

---

## Appendix A: Full File-by-File Change Summary

| File | Action | Details |
|---|---|---|
| `reconsadfc/` (directory) | Rename | → `reconformal/` |
| `reconformal/reconsadfc.py` | Rename | → `reconformal/reconformal.py` |
| `reconformal/__init__.py` | Edit | Docstring + relative import |
| `reconformal/__main__.py` | Edit | Docstring + relative import |
| `pyproject.toml` | Edit | 6 substitutions + version bump to 0.2.0 |
| `README.md` | Edit | ~18 substitutions |
| `tests/test_plaso_to_footprint.py` | Edit | 1 import |
| `tests/test_correlation_calculator.py` | Edit | 1 import |
| `tests/test_entity_extractor.py` | Edit | 1 import |
| `tests/test_relationship_manager.py` | Edit | 1 import |
| `tests/test_data_processor.py` | Edit | 3 substitutions (1 import + 2 mock patches) |
| `docs/source/conf.py` | Edit | 1 substitution (`project` variable) |
| `docs/source/api.rst` | Edit | 1 substitution (`automodule` directive) |
| `docs/source/index.rst` | Edit | 7 substitutions + RST header underline adjustment |
| `docs/source/installation.rst` | Edit | 4 substitutions + fix `cd temp-reconformal` |
| `docs/source/quickstart.rst` | Edit | 6 substitutions |
| `.github/workflows/publish.yml` | Edit | 1 substitution (PyPI URL) |
| `.gitignore` | Edit | Fix duplicate + update path |
| `.readthedocs.yaml` | Edit | Fix `sphinx.configuration` path (bug fix) |
| `reconsadfc-stub/` | Create (new dir) | Deprecation stub package |
