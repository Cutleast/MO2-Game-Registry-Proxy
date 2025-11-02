"""
Copyright (c) Cutleast
"""

import mobase  # pyright: ignore[reportMissingModuleSource]

from .main import GameRegistryProxy


def createPlugin() -> mobase.IPlugin:
    return GameRegistryProxy()
