from src.core.processManager import ProcessManager
from src.config.configManager import ConfigManager
from src.notifications.notifier import Notifier
from src.notifications.notifiableEvent import NotifiableEvent
from src.core.process import Process


class ApplicationContext:
    def __init__(self):
        self._processManager = ProcessManager()
        self._configManager = ConfigManager()
        self._notifier = Notifier()

    # ── Processes ─────────────────────────────────────────────────────────────

    def loadedProcesses(self) -> list[Process]:
        return self._processManager.processesNamed(self._configManager.processNames())

    def gdiCountFor(self, process: Process) -> int | None:
        return self._processManager.gdiCountFor(process)

    # ── Thresholds ────────────────────────────────────────────────────────────

    def gdiWarnThreshold(self) -> int:
        return self._configManager.gdiWarnThreshold()

    def gdiCriticalThreshold(self) -> int:
        return self._configManager.gdiCriticalThreshold()

    def gdiMax(self) -> int:
        return self._configManager.gdiMax()

    # ── Polling ───────────────────────────────────────────────────────────────

    def pollInterval(self) -> int:
        return self._configManager.pollInterval()

    # ── Notifications ─────────────────────────────────────────────────────────

    def notificationEnabled(self) -> bool:
        return self._configManager.notificationEnabled()

    def notificationCooldown(self) -> int:
        return self._configManager.notificationCooldown()

    def publish(self, event: NotifiableEvent) -> None:
        self._notifier.publish(event)

    # ── Display ───────────────────────────────────────────────────────────────

    def showBar(self) -> bool:
        return self._configManager.showBar()

    def showPercentage(self) -> bool:
        return self._configManager.showPercentage()
