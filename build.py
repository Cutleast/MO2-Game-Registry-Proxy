"""
Copyright (c) Cutleast

Copies the content of the src folder to a dist folder and packs it into a zip file.
"""

import shutil
from pathlib import Path

PROJECT_FOLDER = Path("src") / "mo2-game-registry-proxy"
DIST_FOLDER = Path("dist") / PROJECT_FOLDER.name
OUTPUT_FOLDER: Path = DIST_FOLDER / PROJECT_FOLDER.name

if DIST_FOLDER.is_dir():
    shutil.rmtree(DIST_FOLDER)

if DIST_FOLDER.with_suffix(".zip").is_file():
    DIST_FOLDER.with_suffix(".zip").unlink()

shutil.copytree(PROJECT_FOLDER, OUTPUT_FOLDER, dirs_exist_ok=True)

shutil.make_archive(str(DIST_FOLDER), "zip", DIST_FOLDER)
