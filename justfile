set windows-shell := ["powershell.exe", "-NoLogo", "-NonInteractive", "-Command"]

python := env_var_or_default("AURORAVIEW_TEST_PYTHON", "python")
core := env_var("AURORAVIEW_CORE_SOURCE")
dist := env_var_or_default("AURORAVIEW_DIST", "dist")

# Existing runtimes only. CI prepares development dependencies beforehand.
test:
    vx --no-auto-install --cache-mode offline uv@0.12.7 run --no-project --python "{{python}}" scripts/run_tests.py --core "{{core}}"

lint:
    vx --no-auto-install --cache-mode offline uv@0.12.7 run --no-project --python "{{python}}" -m ruff check src tests scripts

format-check:
    vx --no-auto-install --cache-mode offline uv@0.12.7 run --no-project --python "{{python}}" -m ruff format --check src tests scripts

check: lint format-check test

build:
    vx --no-auto-install --cache-mode offline uv@0.12.7 build --no-build-isolation --python "{{python}}" --sdist --wheel --out-dir "{{dist}}"

artifact-check:
    vx --no-auto-install --cache-mode offline uv@0.12.7 run --no-project --python "{{python}}" scripts/verify_artifacts.py --dist "{{dist}}"

install-smoke:
    vx --no-auto-install --cache-mode offline uv@0.12.7 run --no-project --python "{{python}}" scripts/installed_smoke.py --core "{{core}}" --dist "{{dist}}"

package-check: build artifact-check install-smoke

format:
    vx --no-auto-install --cache-mode offline uv@0.12.7 run --no-project --python "{{python}}" -m ruff format src tests scripts
    vx --no-auto-install --cache-mode offline uv@0.12.7 run --no-project --python "{{python}}" -m ruff check --fix src tests scripts
