import json
from pathlib import Path
from typing import Optional
from updatymeow.models import InstalledItem, Status, UpdateRecord

DEFAULT_SETTINGS = {
    "autostart": False,
    "minimize_to_tray": True,
    "check_interval": "6h",
    "notify_new_updates": True,
    "notify_updates_finished": True,
}

class Store:
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or (Path.home() / ".config" / "updatymeow")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.pinned_file = self.config_dir / "pinned.json"
        self.favorites_file = self.config_dir / "favorites.json"
        self.history_file = self.config_dir / "history.json"
        self.settings_file = self.config_dir / "settings.json"
        self.tools_file = self.config_dir / "tools.json"
        self.autostart_dir = Path.home() / ".config" / "autostart"

    def _read_json(self, path: Path, default):
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def _write_json(self, path: Path, data):
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def is_pinned(self, item_id: str) -> bool:
        return item_id in self._read_json(self.pinned_file, [])

    def pin(self, item_id: str):
        pinned = set(self._read_json(self.pinned_file, []))
        pinned.add(item_id)
        self._write_json(self.pinned_file, sorted(list(pinned)))

    def unpin(self, item_id: str):
        pinned = set(self._read_json(self.pinned_file, []))
        pinned.discard(item_id)
        self._write_json(self.pinned_file, sorted(list(pinned)))

    def is_favorite(self, item_id: str) -> bool:
        return item_id in self._read_json(self.favorites_file, [])

    def favorite(self, item_id: str):
        favs = set(self._read_json(self.favorites_file, []))
        favs.add(item_id)
        self._write_json(self.favorites_file, sorted(list(favs)))

    def unfavorite(self, item_id: str):
        favs = set(self._read_json(self.favorites_file, []))
        favs.discard(item_id)
        self._write_json(self.favorites_file, sorted(list(favs)))

    def add_history(self, record: UpdateRecord):
        history = self._read_json(self.history_file, [])
        history.insert(0, record.to_dict())
        self._write_json(self.history_file, history[:100])

    def get_history(self) -> list[UpdateRecord]:
        raw = self._read_json(self.history_file, [])
        return [UpdateRecord.from_dict(d) for d in raw]

    def get_settings(self) -> dict:
        saved = self._read_json(self.settings_file, {})
        settings = dict(DEFAULT_SETTINGS)
        settings.update(saved)
        return settings

    def save_settings(self, settings: dict):
        self._write_json(self.settings_file, settings)

    def is_autostart_enabled(self) -> bool:
        autostart_file = self.autostart_dir / "updatymeow.desktop"
        return autostart_file.exists()

    def set_autostart(self, enabled: bool):
        self.autostart_dir.mkdir(parents=True, exist_ok=True)
        autostart_file = self.autostart_dir / "updatymeow.desktop"
        if enabled:
            content = """[Desktop Entry]
Name=UpdatyMeow
Comment=One window solution for Linux software updates
Exec=updatymeow --minimized
Icon=system-software-update
Terminal=false
Type=Application
Categories=System;Settings;PackageManager;
"""
            autostart_file.write_text(content, encoding="utf-8")
        else:
            if autostart_file.exists():
                autostart_file.unlink()

    def apply_preferences(self, items: list[InstalledItem]):
        pinned_ids = set(self._read_json(self.pinned_file, []))
        fav_ids = set(self._read_json(self.favorites_file, []))
        for item in items:
            if item.id in pinned_ids:
                item.is_pinned = True
                item.status = Status.PINNED
            if item.id in fav_ids:
                item.is_favorite = True

