"""Shared contract and opt-in registry checks; Maya SDK is mocked."""

from __future__ import annotations

import os
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

from auroraview.adapter import EmbedMode, Feature, ThreadModel, UiFramework, get_host_registry
from auroraview.adapter.hosts import MayaHostAdapter as BundledHost
from auroraview.utils.thread_dispatcher import registry
from auroraview.utils.thread_dispatcher.backends.maya import MayaDispatcherBackend as BundledMaya
from test_dispatcher import FakeMaya

from auroraview_maya import MayaDispatcherBackend, MayaHostAdapter, register


class HostTests(unittest.TestCase):
    def setUp(self):
        self.sdk = FakeMaya()
        self.cmds = types.ModuleType("maya.cmds")
        self.cmds.about = lambda **kwargs: "test-Maya-version"
        self.sdk.maya.cmds = self.cmds
        modules = patch.dict(
            sys.modules,
            {
                "maya": self.sdk.maya,
                "maya.utils": self.sdk.utils,
                "maya.cmds": self.cmds,
            },
        )
        modules.start()
        self.addCleanup(modules.stop)
        self.host = MayaHostAdapter()

    def test_metadata_matches_existing_core_contract(self):
        self.assertIsNot(MayaHostAdapter, BundledHost)
        self.assertEqual(self.host.id, "maya")
        self.assertEqual(self.host.display_name, "Autodesk Maya")
        self.assertEqual(self.host.ui_framework, UiFramework.QT)
        self.assertEqual(self.host.thread_model, ThreadModel.HOST_UI_THREAD)
        self.assertEqual(self.host.embed_mode, EmbedMode.NATIVE_CHILD)
        self.assertEqual(self.host.capabilities(), BundledHost().capabilities())
        self.assertTrue(self.host.probe(Feature.MAIN_THREAD_DISPATCH).is_supported)
        self.assertIsNone(self.host.parent_handle())

    def test_detection_and_dispatch_use_owned_backend(self):
        self.assertTrue(self.host.detect())
        self.assertIs(type(self.host._backend()), MayaDispatcherBackend)
        self.assertEqual(self.host.dispatcher_backend(), "MayaDispatcherBackend")
        events = []
        self.host.run_deferred(events.append, "deferred")
        self.assertEqual(events, [])
        self.sdk.pump()
        self.assertEqual(events, ["deferred"])

    def test_version_returns_sdk_value(self):
        self.assertEqual(self.host.version(), "test-Maya-version")

    def test_sdk_absence_is_not_a_detected_host(self):
        with patch.dict(sys.modules, {"maya": None, "maya.utils": None, "maya.cmds": None}):
            self.assertFalse(MayaHostAdapter().detect())
            self.assertIsNone(MayaHostAdapter().version())

    def test_version_probe_failure_is_contained(self):
        def fail(**kwargs):
            raise RuntimeError("SDK version probe failed")

        self.cmds.about = fail
        self.assertIsNone(self.host.version())


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.sdk = FakeMaya()
        modules = patch.dict(sys.modules, {"maya": self.sdk.maya, "maya.utils": self.sdk.utils})
        modules.start()
        self.addCleanup(modules.stop)
        environment = patch.dict(os.environ, {"AURORAVIEW_DISPATCHER": "", "AURORAVIEW_HOST": ""})
        environment.start()
        self.addCleanup(environment.stop)
        registry.clear_dispatcher_backends()
        get_host_registry().clear()
        self.addCleanup(registry.clear_dispatcher_backends)
        self.addCleanup(get_host_registry().clear)

    def assert_owned_slot(self):
        maya = [entry for entry in registry.list_dispatcher_backends() if entry[1] == "Maya"]
        self.assertEqual(len(maya), 1)
        self.assertIs(type(registry.get_dispatcher_backend()), MayaDispatcherBackend)
        hosts = get_host_registry()
        self.assertEqual(hosts.names().count("maya"), 1)
        self.assertIs(type(hosts.detect(env_override="maya").value), MayaHostAdapter)

    def test_register_before_discovery_initializes_and_replaces_builtins(self):
        register()
        self.assert_owned_slot()
        self.assertIn("Houdini", [entry[1] for entry in registry.list_dispatcher_backends()])
        self.assertIn("houdini", get_host_registry().names())

    def test_register_after_cached_legacy_selection_invalidates_cache(self):
        self.assertIs(type(registry.get_dispatcher_backend()), BundledMaya)
        self.assertIs(type(get_host_registry().detect(env_override="maya").value), BundledHost)
        register()
        self.assert_owned_slot()

    def test_repeated_registration_has_one_canonical_slot(self):
        register()
        register()
        self.assert_owned_slot()

    def test_string_and_class_legacy_entries_are_both_removed(self):
        registry.list_dispatcher_backends()
        registry.register_dispatcher_backend(
            "auroraview.utils.thread_dispatcher.backends.maya:MayaDispatcherBackend",
            priority=200,
            name="Maya",
        )
        registry.register_dispatcher_backend(
            "auroraview_maya.dispatcher:MayaDispatcherBackend",
            priority=200,
            name="Maya",
        )
        register()
        self.assert_owned_slot()

    def test_other_plugin_and_host_slots_are_preserved(self):
        class OtherBackend(MayaDispatcherBackend):
            pass

        registry.list_dispatcher_backends()
        registry.register_dispatcher_backend(OtherBackend, priority=10, name="OtherPlugin")
        hosts = get_host_registry()
        hosts.register(BundledHost, priority=10, name="other-plugin")
        register()
        self.assertIn("OtherPlugin", [entry[1] for entry in registry.list_dispatcher_backends()])
        self.assertIn("other-plugin", hosts.names())


class FreshProcessTests(unittest.TestCase):
    def fresh(self, script):
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_import_does_not_load_maya_sdk_or_register(self):
        self.fresh(
            "import sys\n"
            "from auroraview.adapter import get_host_registry\n"
            "from auroraview.utils.thread_dispatcher import registry\n"
            "hosts = get_host_registry().names()\n"
            "before = registry.list_dispatcher_backends()\n"
            "import auroraview_maya\n"
            "assert 'maya' not in sys.modules and 'maya.utils' not in sys.modules\n"
            "assert get_host_registry().names() == hosts\n"
            "assert registry.list_dispatcher_backends() == before\n"
        )

    def test_registration_without_sdk_keeps_maya_unavailable_and_falls_back(self):
        self.fresh(
            "import sys\n"
            "sys.modules.update({'maya': None, 'maya.utils': None})\n"
            "from auroraview_maya import register\n"
            "register()\n"
            "from auroraview.utils.thread_dispatcher import registry\n"
            "from auroraview.adapter import get_host_registry\n"
            "maya = [item for item in registry.list_dispatcher_backends() if item[1] == 'Maya']\n"
            "assert len(maya) == 1 and maya[0][2] is False\n"
            "selection = get_host_registry().detect(env_override='maya')\n"
            "assert selection.value.id == 'standalone' and selection.has_warnings\n"
        )

    def test_canonical_first_preserves_legacy_class_and_contract(self):
        self.fresh(
            "from auroraview_maya import MayaHostAdapter as New\n"
            "from auroraview.adapter.hosts import MayaHostAdapter as Old\n"
            "from auroraview.adapter import HostAdapter\n"
            "assert New is not Old and issubclass(New, HostAdapter)\n"
            "assert New.id == Old.id == 'maya'\n"
        )

    def test_legacy_first_preserves_legacy_class_and_contract(self):
        self.fresh(
            "from auroraview.adapter.hosts import MayaHostAdapter as Old\n"
            "from auroraview_maya import MayaHostAdapter as New\n"
            "from auroraview.adapter import HostAdapter\n"
            "assert New is not Old and issubclass(New, HostAdapter)\n"
            "assert New.id == Old.id == 'maya'\n"
        )
