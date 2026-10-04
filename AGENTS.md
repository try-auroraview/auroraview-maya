# AuroraView Maya

Keep source compatible with Python 3.7. All tools use `vx`; task orchestration
uses `vx just <recipe>`. Set `AURORAVIEW_TEST_PYTHON` to an existing interpreter
and `AURORAVIEW_CORE_SOURCE` to the public Core checkout for source tests.

`vx just check` runs source tests, grammar checks and lint. `vx just package-check`
builds wheel/sdist and verifies an isolated wheel install. These gates use mocked
Maya scheduling and source Core; they do not certify real Maya or native WebView.

The host contract, Qt integration, renderer and registries belong to Core.
Never introduce an adapter registry, render backend or Maya setup script here.
Imports must not load the Maya SDK or register candidates. `register()` explicitly
replaces only known bundled Maya dispatcher entries in existing registries.
Keep unrelated DCC slots and legacy Core import paths intact.

Do not commit binaries, raw machine logs, local paths, credentials or build caches.
Do not publish a package until the real-host acceptance matrix is complete.
