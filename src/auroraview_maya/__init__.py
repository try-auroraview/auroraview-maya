# -*- coding: utf-8 -*-
"""Opt-in Maya adapter. Importing this package never registers a backend."""

from __future__ import annotations

from .dispatcher import MayaDispatcherBackend
from .host import MayaHostAdapter

__all__ = ["MayaDispatcherBackend", "MayaHostAdapter", "register"]


def register() -> None:
    """Select this implementation in AuroraView's existing registries.

    The bundled implementation remains available through legacy imports.
    Initialize builtins before replacing their Maya entries; otherwise the
    first discovery call would restore the bundled backend over this one.
    Repeated calls are safe. Other DCC registrations remain intact.
    """
    from auroraview.adapter import AdapterPriority, get_host_registry
    from auroraview.utils.thread_dispatcher import registry
    from auroraview.utils.thread_dispatcher.backends.maya import (
        MayaDispatcherBackend as BundledMaya,
    )

    registry.list_dispatcher_backends()
    for spec in (
        BundledMaya,
        "auroraview.utils.thread_dispatcher.backends.maya:MayaDispatcherBackend",
        "auroraview_maya.dispatcher:MayaDispatcherBackend",
    ):
        while registry.unregister_dispatcher_backend(spec):
            pass
    registry.register_dispatcher_backend(
        MayaDispatcherBackend, priority=registry.DispatcherPriority.MAYA, name="Maya"
    )
    hosts = get_host_registry()
    hosts.register(MayaHostAdapter, priority=AdapterPriority.MAYA, name="maya")
