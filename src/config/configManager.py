import os
from dotenv import load_dotenv


class ConfigManager:
    def __init__(self):
        load_dotenv()

    def processNames(self) -> list[str]:
        raw = os.getenv("PROCESS_NAMES", "abt")
        return [name.strip() for name in raw.split(",") if name.strip()]

    def pollInterval(self) -> int:
        return int(os.getenv("POLL_INTERVAL", "10"))

    def gdiWarnThreshold(self) -> int:
        return int(os.getenv("GDI_WARN_THRESHOLD", "100"))

    def gdiCriticalThreshold(self) -> int:
        return int(os.getenv("GDI_CRITICAL_THRESHOLD", "300"))

    def gdiMax(self) -> int:
        return int(os.getenv("GDI_MAX", "10000"))

    def notificationEnabled(self) -> bool:
        return os.getenv("NOTIFICATION_ENABLED", "true").lower() == "true"

    def notificationCooldown(self) -> int:
        return int(os.getenv("NOTIFICATION_COOLDOWN", "60"))

    def showBar(self) -> bool:
        return os.getenv("SHOW_BAR", "true").lower() == "true"

    def showPercentage(self) -> bool:
        return os.getenv("SHOW_PERCENTAGE", "true").lower() == "true"
