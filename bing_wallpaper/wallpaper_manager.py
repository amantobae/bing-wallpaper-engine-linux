import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

logger = logging.getLogger(__name__)

class KdeWallpaperManager:
    """Manages KDE Plasma desktop wallpaper settings on Fedora."""

    def __init__(self):
        self.plasma_tool = shutil.which("plasma-apply-wallpaperimage")
        self.qdbus_tool = shutil.which("qdbus-qt6") or shutil.which("qdbus")

    def set_wallpaper(self, image_path: str, fill_mode: str = "preserveAspectCrop") -> bool:
        """
        Sets the specified image as the desktop wallpaper in KDE Plasma.
        Returns True if successful, False otherwise.
        """
        path = Path(image_path).expanduser().resolve()
        if not path.is_file():
            logger.error("Image file does not exist: %s", path)
            return False

        abs_str = str(path)

        # 1. Primary method: plasma-apply-wallpaperimage
        if self.plasma_tool:
            try:
                cmd = [self.plasma_tool, "--fill-mode", fill_mode, abs_str]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if res.returncode == 0:
                    logger.info("Wallpaper applied successfully via plasma-apply-wallpaperimage: %s", abs_str)
                    return True
                else:
                    logger.warning("plasma-apply-wallpaperimage failed (code %d): %s", res.returncode, res.stderr)
            except Exception as e:
                logger.warning("Error running plasma-apply-wallpaperimage: %s", e)

        # 2. Fallback method: D-Bus evaluateScript via qdbus-qt6 / qdbus
        if self.qdbus_tool:
            try:
                js_script = (
                    f'var allDesktops = desktops();\n'
                    f'for (var i = 0; i < allDesktops.length; i++) {{\n'
                    f'    var d = allDesktops[i];\n'
                    f'    d.wallpaperPlugin = "org.kde.image";\n'
                    f'    d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");\n'
                    f'    d.writeConfig("Image", "file://{abs_str}");\n'
                    f'}}\n'
                )
                cmd = [
                    self.qdbus_tool,
                    "org.kde.plasmashell",
                    "/PlasmaShell",
                    "org.kde.PlasmaShell.evaluateScript",
                    js_script
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if res.returncode == 0:
                    logger.info("Wallpaper applied successfully via qdbus evaluateScript")
                    return True
                else:
                    logger.error("qdbus evaluateScript failed (code %d): %s", res.returncode, res.stderr)
            except Exception as e:
                logger.error("Error executing qdbus script: %s", e)

        return False

    def get_current_wallpaper(self) -> Optional[str]:
        """
        Reads KDE Plasma config to find the current desktop wallpaper image path.
        """
        config_file = Path.home() / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
        if not config_file.is_file():
            return None

        try:
            with open(config_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("Image="):
                        raw_val = line[len("Image="):].strip()
                        if raw_val.startswith("file://"):
                            parsed = urlparse(raw_val)
                            path_str = unquote(parsed.path)
                        else:
                            path_str = raw_val
                        
                        path = Path(path_str)
                        if path.is_file():
                            return str(path)
        except Exception as e:
            logger.warning("Could not read current wallpaper from config: %s", e)

        return None
