"""Verify package payload, license and metadata without importing host SDKs."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path


def check_metadata(data):
    metadata = BytesParser().parsebytes(data)
    assert metadata["Name"] == "auroraview-maya"
    assert metadata["Requires-Python"] == ">=3.7"
    dependencies = metadata.get_all("Requires-Dist", [])
    assert len(dependencies) == 1
    assert dependencies[0].replace(" ", "") in (
        "auroraview>=0.5.11,<0.6.0",
        "auroraview<0.6.0,>=0.5.11",
    )
    return {"version": metadata["Version"], "requires_dist": dependencies}


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=root / "dist")
    args = parser.parse_args()
    wheels = list(args.dist.glob("*.whl"))
    sdists = list(args.dist.glob("*.tar.gz"))
    assert len(wheels) == len(sdists) == 1
    source = {
        str(path.relative_to(root / "src")).replace("\\", "/"): path.read_bytes()
        for path in (root / "src").rglob("*.py")
    }
    with zipfile.ZipFile(wheels[0]) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        for name, expected in source.items():
            assert archive.read(name) == expected
        assert not any(name.startswith("auroraview/") for name in names)
        assert not any(name.lower().endswith((".pyd", ".dll", ".exe")) for name in names)
        licenses = [name for name in names if name.endswith("/LICENSE")]
        assert len(licenses) == 1
        assert archive.read(licenses[0]) == (root / "LICENSE").read_bytes()
        metadata = check_metadata(
            archive.read(next(name for name in names if name.endswith(".dist-info/METADATA")))
        )
    with tarfile.open(sdists[0], "r:gz") as archive:
        files = {
            member.name.split("/", 1)[1]: member
            for member in archive.getmembers()
            if member.isfile()
        }
        for required in ("LICENSE", "PROVENANCE.json", "migration/commit-map.txt"):
            assert required in files
        for name, member in files.items():
            if name != "PKG-INFO":
                assert archive.extractfile(member).read() == (root / name).read_bytes(), name
            assert not any(
                part in name.split("/")
                for part in (".git", "evidence", ".uv-cache", "dist", "__pycache__")
            )
        assert check_metadata(archive.extractfile(files["PKG-INFO"]).read()) == metadata
    print(
        json.dumps(
            {
                "accepted": True,
                "metadata": metadata,
                "artifacts": [
                    {
                        "file": path.name,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "bytes": path.stat().st_size,
                    }
                    for path in (wheels[0], sdists[0])
                ],
                "published": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
