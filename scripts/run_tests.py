"""Run no-SDK contract checks against pinned public Core source."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path


def bind_core(core):
    root = Path(__file__).resolve().parents[1]
    provenance = json.loads((root / "PROVENANCE.json").read_text(encoding="utf-8"))
    for name, expected in provenance["source_files"].items():
        data = (core / name).read_bytes()
        if name == "LICENSE":
            data = data.replace(b"\r\n", b"\n")
        assert hashlib.sha256(data).hexdigest() == expected, name
    original = (core / "python/auroraview/utils/thread_dispatcher/backends/maya.py").read_text(
        encoding="utf-8"
    )
    expected = original.replace(
        "from ..base import ThreadDispatcherBackend",
        "from auroraview.utils.thread_dispatcher.base import ThreadDispatcherBackend",
    )
    assert (root / "src/auroraview_maya/dispatcher.py").read_text(encoding="utf-8") == expected
    sys.path.insert(0, str(core / "python"))
    return root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", required=True, type=Path)
    parser.add_argument("--installed", action="store_true")
    args = parser.parse_args()
    root = bind_core(args.core.resolve())
    for directory in ("src", "tests", "scripts"):
        for path in sorted((root / directory).rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            if sys.version_info >= (3, 8):
                ast.parse(source, filename=path.name, feature_version=7)
            else:
                ast.parse(source, filename=path.name)
    paths = [str(args.core.resolve() / "python")]
    if not args.installed:
        sys.path.insert(0, str(root / "src"))
        paths.insert(0, str(root / "src"))
    os.environ["PYTHONPATH"] = os.pathsep.join(paths)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    print("Gate: pinned public Core source + mocked Maya scheduling; no native host acceptance")
    print("Python runtime: " + sys.version.split()[0])
    suite = unittest.defaultTestLoader.discover(str(root / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "accepted": result.wasSuccessful(),
        "python": sys.version.split()[0],
        "tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skips": len(result.skipped),
        "installed_adapter": args.installed,
        "source_core": json.loads((root / "PROVENANCE.json").read_text())["source_commit"],
        "real_maya": False,
        "native_webview": False,
        "published_core_dependency": False,
    }
    print("RESULT_JSON=" + json.dumps(report, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
