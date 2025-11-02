"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import ctypes
import winreg
from pathlib import Path
from typing import Optional, cast

import mobase  # pyright: ignore[reportMissingModuleSource]
from PyQt6.QtCore import QDir, qCritical, qDebug


class Proxy:
    """
    Proxy managing the registry key for the game folder.
    """

    GAME_REGISTRY_KEYS: dict[str, tuple[int, str, str]] = {
        "Enderal": (
            winreg.HKEY_LOCAL_MACHINE,
            "Software\\WOW6432Node\\SureAI\\Enderal",
            "Install_Path",
        ),
        "Fallout3": (
            winreg.HKEY_LOCAL_MACHINE,
            "Software\\WOW6432Node\\Bethesda Softworks\\Fallout3",
            "Installed Path",
        ),
        "Fallout4": (
            winreg.HKEY_LOCAL_MACHINE,
            "Software\\WOW6432Node\\Bethesda Softworks\\Fallout4",
            "Installed Path",
        ),
        "Fallout4VR": (
            winreg.HKEY_LOCAL_MACHINE,
            "Software\\WOW6432Node\\Bethesda Softworks\\Fallout 4 VR",
            "Installed Path",
        ),
        "FalloutNV": (
            winreg.HKEY_LOCAL_MACHINE,
            "Software\\WOW6432Node\\Bethesda Softworks\\FalloutNV",
            "Installed Path",
        ),
        "Morrowind": (
            winreg.HKEY_LOCAL_MACHINE,
            "Software\\WOW6432Node\\Bethesda Softworks\\Morrowind",
            "Installed Path",
        ),
        "Oblivion": (
            winreg.HKEY_LOCAL_MACHINE,
            "Software\\WOW6432Node\\Bethesda Softworks\\Oblivion",
            "Installed Path",
        ),
        "Skyrim": (
            winreg.HKEY_LOCAL_MACHINE,
            "Software\\WOW6432Node\\Bethesda Softworks\\Skyrim",
            "Installed Path",
        ),
        "SkyrimSE": (
            winreg.HKEY_LOCAL_MACHINE,
            "Software\\WOW6432Node\\Bethesda Softworks\\Skyrim Special Edition",
            "Installed Path",
        ),
        "SkyrimVR": (
            winreg.HKEY_LOCAL_MACHINE,
            "Software\\WOW6432Node\\Bethesda Softworks\\Skyrim VR",
            "Installed Path",
        ),
        "TTW": (
            winreg.HKEY_LOCAL_MACHINE,
            "Software\\WOW6432Node\\Bethesda Softworks\\FalloutNV",
            "Installed Path",
        ),
    }
    """Dictionary mapping game names to registry keys."""

    __organizer: mobase.IOrganizer

    __original_reg_value: Optional[Path] = None

    def __init__(self, organizer: mobase.IOrganizer) -> None:
        self.__organizer = organizer

    def on_about_to_run(self, app_name: str) -> bool:
        """
        Callback handler that's called when the user is about to run an application from
        MO2.

        Args:
            app_name (str): Absolute path to the application.

        Returns:
            bool: Whether the application should be run.
        """

        if (
            not self.__is_active()
            or Path(app_name).name.lower() in self.__get_disabled_apps()
        ):
            return True

        game_folder: Path = self.get_game_folder()
        reg_value: Optional[Path] = self.get_reg_value()
        qDebug(f"Game folder: {game_folder}")
        qDebug(f"Registry value: {reg_value}")
        if reg_value != game_folder:
            self.__original_reg_value = reg_value
            self.set_reg_value(str(game_folder))

        return True

    def on_finished_run(self, app_name: str, return_code: int) -> None:
        """
        Callback handler that's called when an application is finished.

        Args:
            app_name (str): Absolute path to the application.
            return_code (int): Return code of the application.
        """

        if not self.__is_active() or self.__original_reg_value is None:
            return

        self.set_reg_value(str(self.__original_reg_value))
        self.__original_reg_value = None

    def __get_game_reg_key(self) -> Optional[tuple[int, str, str]]:
        """
        Returns:
            Optional[tuple[int, str, str]]:
                Registry key for the current game or None if not supported.
        """

        game_name: str = self.__organizer.managedGame().gameShortName()
        if game_name not in Proxy.GAME_REGISTRY_KEYS:
            return

        return Proxy.GAME_REGISTRY_KEYS[game_name]

    def set_reg_value(self, value: str) -> None:
        """
        Sets the current registry value for the game folder using elevated rights.

        Args:
            value (str): The new value for the registry key.
        """

        reg_key: Optional[tuple[int, str, str]] = self.__get_game_reg_key()
        if reg_key is None:
            qCritical("No registry key defined for this game.")
            return

        key, sub_key, value_name = reg_key

        if key != winreg.HKEY_LOCAL_MACHINE:
            qCritical("Only HKLM writes are supported for elevation.")
            return

        full_path = f"HKLM\\{sub_key}"
        # Escape quotes for safety
        safe_value = value.replace('"', '\\"')

        # Build reg.exe argument string
        args = f'add "{full_path}" /v "{value_name}" /d "{safe_value}" /f /reg:32'

        try:
            qDebug(f"Requesting elevated registry write: reg {args}")

            # Use ShellExecuteW to start reg.exe with "runas" (Admin rights)
            ShellExecuteW = ctypes.windll.shell32.ShellExecuteW
            ret = int(ShellExecuteW(None, "runas", "reg.exe", args, None, 1))

            if ret <= 32:
                qCritical(f"Failed to start reg.exe (ShellExecute returned {ret}).")
            else:
                qDebug("Successfully requested elevation for registry update.")

        except Exception as ex:
            qCritical(f"Error launching elevated registry write: {ex}")

    def get_reg_value(self) -> Optional[Path]:
        """
        Reads the current registry value for the game folder.

        Returns:
            Optional[Path]: The path to the game folder.
        """

        reg_key: Optional[tuple[int, str, str]] = self.__get_game_reg_key()
        if reg_key is None:
            return

        key, sub_key, value_name = reg_key

        install_path: Optional[Path] = None
        try:
            with winreg.OpenKey(
                key, sub_key, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY
            ) as hKey:
                try:
                    value: str = winreg.QueryValueEx(hKey, value_name)[0]
                    if value.strip():
                        install_path = Path(QDir(value).canonicalPath())
                    else:
                        install_path = None

                except FileNotFoundError:
                    install_path = None

        except FileNotFoundError:
            install_path = None

        return install_path

    def get_game_folder(self) -> Path:
        """
        Returns:
            Path: The path to the game folder.
        """

        return Path(self.__organizer.managedGame().gameDirectory().canonicalPath())

    def __is_active(self) -> bool:
        from .main import GameRegistryProxy

        return bool(
            self.__organizer.pluginSetting(
                GameRegistryProxy.NAME, GameRegistryProxy.ENABLED_SETTING
            )
        )

    def __get_disabled_apps(self) -> list[str]:
        from .main import GameRegistryProxy

        return list(
            map(
                lambda x: x.lower(),
                cast(
                    str,
                    self.__organizer.pluginSetting(
                        GameRegistryProxy.NAME, GameRegistryProxy.DISABLED_APPS_SETTING
                    ),
                ).split(";"),
            )
        )
