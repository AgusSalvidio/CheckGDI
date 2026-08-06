import json
import os

# Stored next to the project root so it survives across runs without touching .env
_DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".gdi_monitor_settings.json",
)


class SettingsStore:
    """Persists the UI display settings (view style, color/style profiles, active profile) across runs."""

    def __init__(self, path: str = _DEFAULT_PATH):
        self._path = path

    def load(self) -> dict:
        if not os.path.exists(self._path):
            return {}
        try:
            with open(self._path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, ValueError):
            return {}

    def save(self, values: dict) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as file:
                json.dump(values, file, indent=2)
        except OSError:
            pass
