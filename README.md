# AuroraView Maya

An independently maintained Maya host adapter and thread dispatcher, extracted
from the public AuroraView repository with relevant Git history preserved.
This first migration batch is a development candidate, not a published release.

## Dependency boundary

`auroraview` owns RFC0019 `HostAdapter`, `Registry`, `RenderBackend`, the Qt host,
WebView bridge and thread-dispatch contract. This package owns Maya discovery,
version metadata and `maya.utils` scheduling. It adds no runtime dependencies
except Core and never vendors Qt, a renderer or a native wheel.

The initial declared compatibility range is `auroraview>=0.5.11,<0.6.0`.
Source checks pin the migration base from `PROVENANCE.json`; released-wheel
compatibility is a separate acceptance gate. Version `0.0.0.dev0` reserves no
PyPI release and CI contains no publishing job.

## Explicit activation

```python
from auroraview_maya import MayaDispatcherBackend, MayaHostAdapter, register

register()
# Existing AuroraView factories and APIs remain unchanged.
from auroraview import create_webview
```

Importing `auroraview_maya` does not import `maya.utils`, construct Qt widgets,
register candidates or change global selection. `register()` initializes Core's
builtins, removes only the known bundled Maya dispatcher class/spec, then puts
this implementation into Core's existing Maya dispatcher and host slots.
Calling it again leaves one canonical and no bundled Maya registry entry.
Other DCC registrations remain intact. The bundled implementations and legacy
Core imports remain available during this first opt-in stage; canonical and
legacy classes are intentionally distinct before a later compatibility facade.

## Local checks

Use an existing interpreter containing `hatchling` and `ruff`. Supply the Core
checkout as `AURORAVIEW_CORE_SOURCE` and interpreter as `AURORAVIEW_TEST_PYTHON`.

```sh
vx just check
vx just package-check
```

Recipes are portable and contain no developer machine paths. Build and install
checks run without resolving runtime dependencies, then bind the pinned public
Core source explicitly. CI installs development dependencies into its temporary
runner environment and uses the same recipes.

## Acceptance matrix

| Gate | Coverage | Meaning |
| --- | --- | --- |
| Source/no SDK | Python 3.7+, fake `maya.utils`, both import orders, host metadata, registration replacement | Source contract and scheduling behavior |
| Package/no SDK | Wheel + sdist metadata/license/payload and isolated installed-wheel tests | Packaging and installed code, using pinned source Core |
| Released Core | Dependency range against the official Core wheel | Separate evidence required; source gates alone do not certify it |
| Real Maya | Maya versions, their Python/PySide versions, parent/dock ownership and owner thread | Required before release; not covered by mocks |
| Native bridge | Real Qt/WebView JS return, close/restart, deadlines and late admission | Must use the exact public Core build; prior private joint tests are not a whole-ecosystem release gate |
| Standalone | Same Core API outside Maya, including no-Qt shell | Core acceptance required; not exercised by this package |

No CI job uses a Maya license, modifies Maya startup files, changes user scenes,
or marks an absent native SDK as a passed host acceptance run.

## History and existing references

`migration/commit-map.txt` maps all original main commits to filtered history.
Zero hashes mark pruned commits with no remaining selected-path change. The
`filtered_head` in provenance records the retained state of the original main
tip, including when the tip commit itself has a zero mapping. The filter keeps the Maya dispatcher, its
pre-restructure shared dispatcher predecessor, shared host-adapter source and
MIT license. The initialization commit narrows the shared host source to Maya
and changes only dependency imports and dispatcher identity.

The Core repository's real organization transfer preserves its complete history,
tags, issues and pull requests. This new adapter repository has path-filtered
history with rewritten hashes; it does not inherit GitHub issue numbers or Core
release tags. Existing references remain at
[Core issues](https://github.com/try-auroraview/auroraview/issues) and
[Core releases](https://github.com/try-auroraview/auroraview/releases).
See `PROVENANCE.json` for the public source commit and selected path mapping.
