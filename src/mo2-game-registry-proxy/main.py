"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import override

import mobase  # pyright: ignore[reportMissingModuleSource]
from PyQt6.QtGui import QIcon

from .proxy import Proxy


class GameRegistryProxy(mobase.IPluginTool):
    """
    Plugin for Mod Organizer 2.
    """

    NAME: str = "Game-Registry-Proxy"
    ENABLED_SETTING: str = "enableProxy"
    DISABLED_APPS_SETTING: str = "disabled_apps"

    __organizer: mobase.IOrganizer
    __icon_path: Path
    __proxy: Proxy

    def __init__(self) -> None:
        super().__init__()

    @override
    def init(self, organizer: mobase.IOrganizer) -> bool:
        self.__organizer = organizer
        self.__icon_path = (
            Path(
                self.__organizer.getPluginDataPath().replace(
                    "data", "mo2-game-registry-proxy"
                )
            )
            / "icons"
        )

        self.__proxy = Proxy(self.__organizer)
        self.__organizer.onAboutToRun(self.__proxy.on_about_to_run)
        self.__organizer.onFinishedRun(self.__proxy.on_finished_run)

        return True

    @override
    def name(self) -> str:
        return GameRegistryProxy.NAME

    @override
    def author(self) -> str:
        return "Cutleast"

    @override
    def displayName(self) -> str:
        return "Game Registry Proxy"

    @override
    def description(self) -> str:
        return (
            "Changes the registry key of the game folder to match the one used by "
            "this instance when an executable is started. The key is reverted when the "
            "executable is stopped."
        )

    @override
    def version(self) -> mobase.VersionInfo:
        return mobase.VersionInfo(1, 0, 0, mobase.ReleaseType.FINAL)

    def isActive(self) -> bool:
        return bool(
            self.__organizer.pluginSetting(
                self.name(), GameRegistryProxy.ENABLED_SETTING
            )
        )

    @override
    def settings(self) -> list[mobase.PluginSetting]:
        return [
            mobase.PluginSetting(
                GameRegistryProxy.ENABLED_SETTING, "Enable this plugin.", True
            ),
            mobase.PluginSetting(
                GameRegistryProxy.DISABLED_APPS_SETTING,
                "List of applications that should not be affected by this plugin.",
                "SkyrimSE.exe;skse64_loader.exe",
            ),
        ]

    @override
    def display(self) -> None:
        self.__organizer.setPluginSetting(
            self.name(), GameRegistryProxy.ENABLED_SETTING, not self.isActive()
        )

    @override
    def icon(self) -> QIcon:
        if self.isActive():
            return QIcon(str(self.__icon_path / "on.png"))
        else:
            return QIcon(str(self.__icon_path / "off.png"))

    @override
    def tooltip(self) -> str:
        return self.description()
