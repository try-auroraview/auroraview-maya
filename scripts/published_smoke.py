"""Check installed adapter APIs against a checksum-verified public Core wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import sysconfig
import unittest
import zipfile
from email.parser import Parser
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-wheel", required=True, type=Path)
    parser.add_argument("--core-sha256", required=True)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    (adapter_wheel,) = args.dist.resolve().glob("*.whl")
    assert hashlib.sha256(args.core_wheel.read_bytes()).hexdigest() == args.core_sha256
    assert sys.flags.isolated, "Use an isolated interpreter so source paths cannot mask wheels"
    os.environ.pop("PYTHONPATH", None)
    os.environ["AURORAVIEW_DISABLE_WARMUP"] = "1"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True

    import auroraview
    import auroraview._core as native

    import auroraview_maya

    site = Path(sysconfig.get_path("purelib")).resolve()
    core_path = Path(auroraview.__file__).resolve()
    adapter_path = Path(auroraview_maya.__file__).resolve()
    native_path = Path(native.__file__).resolve()
    assert core_path == site / "auroraview/__init__.py"
    assert adapter_path == site / "auroraview_maya/__init__.py"
    assert native_path.parent == core_path.parent and native_path.suffix == ".pyd"
    assert "maya" not in sys.modules and "maya.utils" not in sys.modules
    with zipfile.ZipFile(args.core_wheel) as archive:
        (metadata,) = (name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        version = Parser().parsestr(archive.read(metadata).decode("utf-8"))["Version"]
        assert auroraview.__version__ == version
        for path in (core_path, native_path):
            assert path.read_bytes() == archive.read("auroraview/" + path.name)
    with zipfile.ZipFile(adapter_wheel) as archive:
        for name in archive.namelist():
            if name.startswith("auroraview_maya/") and name.endswith(".py"):
                assert (site / name).read_bytes() == archive.read(name)

    suite = unittest.defaultTestLoader.discover(str(root / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    accepted = result.testsRun > 0 and result.wasSuccessful() and not result.skipped
    print(
        "RESULT_JSON="
        + json.dumps(
            {
                "accepted": accepted,
                "python": sys.version.split()[0],
                "core_version": version,
                "core_wheel_sha256": args.core_sha256,
                "adapter_wheel_sha256": hashlib.sha256(adapter_wheel.read_bytes()).hexdigest(),
                "native_sha256": hashlib.sha256(native_path.read_bytes()).hexdigest(),
                "tests": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "skips": len(result.skipped),
                "source_core_injection": False,
                "real_maya": False,
                "native_bridge_acceptance": False,
            },
            sort_keys=True,
        )
    )
    return 0 if accepted else 1


if __name__ == "__main__":
    sys.exit(main())
