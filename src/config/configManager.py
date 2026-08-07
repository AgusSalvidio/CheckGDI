import os
from dotenv import load_dotenv

NEEDLE_THICKNESS_MIN = 0.5
NEEDLE_THICKNESS_MAX = 3.0


class ConfigManager:
    def __init__(self):
        load_dotenv()

    # ── Generic env-parsing helpers ─────────────────────────────────────────────

    def _str(self, key: str, default: str) -> str:
        return os.getenv(key, default).strip().lower()

    def _int(self, key: str, default: int) -> int:
        return int(os.getenv(key, str(default)))

    def _bool(self, key: str, default: bool) -> bool:
        return os.getenv(key, str(default)).strip().lower() == "true"

    def _float(self, key: str, default: float, lo: float, hi: float) -> float:
        try:
            value = float(os.getenv(key, str(default)).strip())
        except ValueError:
            value = default
        return max(lo, min(value, hi))

    # ── Processes ─────────────────────────────────────────────────────────────

    def processNames(self) -> list[str]:
        raw = os.getenv("PROCESS_NAMES", "abt")
        return [name.strip() for name in raw.split(",") if name.strip()]

    # ── Polling / thresholds ─────────────────────────────────────────────────

    def pollInterval(self) -> int:
        return self._int("POLL_INTERVAL", 10)

    def gdiWarnThreshold(self) -> int:
        return self._int("GDI_WARN_THRESHOLD", 100)

    def gdiCriticalThreshold(self) -> int:
        return self._int("GDI_CRITICAL_THRESHOLD", 300)

    def gdiMax(self) -> int:
        return self._int("GDI_MAX", 10000)

    # ── Notifications ────────────────────────────────────────────────────────

    def notificationEnabled(self) -> bool:
        return self._bool("NOTIFICATION_ENABLED", True)

    def notificationCooldown(self) -> int:
        return self._int("NOTIFICATION_COOLDOWN", 60)

    # ── Display ───────────────────────────────────────────────────────────────

    def showBar(self) -> bool:
        return self._bool("SHOW_BAR", True)

    def showPercentage(self) -> bool:
        return self._bool("SHOW_PERCENTAGE", True)

    def viewStyle(self) -> str:
        return self._str("VIEW_STYLE", "bars")

    def gaugeStyle(self) -> str:
        return self._str("GAUGE_STYLE", "classic")

    def needleStyle(self) -> str:
        return self._str("NEEDLE_STYLE", "classic")

    def needleColor(self) -> str:
        return self._str("NEEDLE_COLOR", "auto")

    def zoneMode(self) -> str:
        return self._str("GAUGE_ZONE_MODE", "multicolor")

    def accentColor(self) -> str:
        return self._str("GAUGE_ACCENT_COLOR", "auto")

    def numberColor(self) -> str:
        return self._str("GAUGE_NUMBER_COLOR", "auto")

    def dialColor(self) -> str:
        return self._str("GAUGE_DIAL_COLOR", "auto")

    def fontFamily(self) -> str:
        return self._str("GAUGE_FONT_FAMILY", "auto")

    def needleThickness(self) -> float:
        return self._float("NEEDLE_THICKNESS", 1.0, NEEDLE_THICKNESS_MIN, NEEDLE_THICKNESS_MAX)
