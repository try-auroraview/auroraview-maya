"""Install the adapter wheel in a new task-local venv and exercise actual files."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import sysconfig
import venv
import zipfile
from pathlib import Path


def run(command, **kwargs):
    subprocess.run(command, check=True, timeout=180, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", required=True, type=Path)
    parser.add_argument("--inside", action="store_true")
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    (wheel,) = args.dist.resolve().glob("*.whl")
    if not args.inside:
        environment = root / (".install-env-py%d%d" % sys.version_info[:2])
        if not environment.exists():
            venv.EnvBuilder(with_pip=False).create(str(environment))
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        uv = [
            "vx",
            "--no-auto-install",
            "--cache-mode",
            "offline",
            "uv@0.12.7",
            "pip",
            "install",
            "--python",
            str(python),
            "--offline",
            "--no-deps",
            "--index-url",
            "https://pypi.org/simple",
        ]
        # This is Core's declared Python < 3.8 compatibility dependency.
        if sys.version_info < (3, 8):
            run(uv + ["typing_extensions==4.7.1"])
        run(uv + ["--no-index", "--reinstall", str(wheel)])
        run(
            [
                str(python),
                str(Path(__file__).resolve()),
                "--inside",
                "--dist",
                str(args.dist.resolve()),
                "--core",
                str(args.core),
            ]
        )
        return
    candidate_src = (root / "src").resolve()
    sys.path[:] = [entry for entry in sys.path if Path(entry or ".").resolve() != candidate_src]
    sys.path.insert(0, str(args.core.resolve() / "python"))
    import auroraview_maya

    installed = Path(auroraview_maya.__file__).resolve()
    site = Path(sysconfig.get_path("purelib"))
    assert installed == (site / "auroraview_maya/__init__.py").resolve()
    with zipfile.ZipFile(wheel) as archive:
        for path in installed.parent.glob("*.py"):
            assert path.read_bytes() == archive.read("auroraview_maya/" + path.name)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(args.core.resolve() / "python")
    run(
        [
            sys.executable,
            str(root / "scripts/run_tests.py"),
            "--installed",
            "--core",
            str(args.core.resolve()),
        ],
        env=env,
    )
    print("Installed wheel payload verified; pinned source Core; no runtime dependency acceptance")


if __name__ == "__main__":
    main()
