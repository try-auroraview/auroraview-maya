# -*- coding: utf-8 -*-
"""Maya host metadata, using the shared AuroraView host contract."""

from __future__ import annotations

from typing import Optional

from auroraview.adapter.hosts import DispatcherBackedHostAdapter, QtHostAdapterMixin


class MayaHostAdapter(QtHostAdapterMixin, DispatcherBackedHostAdapter):
    """Autodesk Maya (Qt host). SDK imports remain lazy."""

    dispatcher_spec = "auroraview_maya.dispatcher:MayaDispatcherBackend"
    id = "maya"
    display_name = "Autodesk Maya"

    def version(self) -> Optional[str]:
        """Maya version, via ``maya.cmds.about``."""
        try:
            from maya import cmds

            return str(cmds.about(version=True))
        except Exception:
            return None
