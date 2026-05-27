import time
from src.notifications.notifiableEvent import NotifiableEvent
from src.core.process import Process


class ProcessChecker:
    def __init__(self, workingContext):
        self._context = workingContext
        self._lastNotified: dict[int, float] = {}

    @classmethod
    def workingWith(cls, workingContext):
        return cls(workingContext=workingContext)

    def checkAll(self) -> list[tuple[Process, int]]:
        """Query all monitored processes and return (process, gdi_count) pairs.
        Also fires desktop notifications when the critical threshold is exceeded."""
        results = []
        for process in self._context.loadedProcesses():
            count = self._context.gdiCountFor(process)
            if count is not None:
                results.append((process, count))
                self._notifyIfNeeded(process, count)
        return results

    def _notifyIfNeeded(self, process: Process, count: int) -> None:
        if not self._context.notificationEnabled():
            return
        if count < self._context.gdiCriticalThreshold():
            return
        now = time.time()
        if now - self._lastNotified.get(process.pid, 0) >= self._context.notificationCooldown():
            self._lastNotified[process.pid] = now
            self._context.publish(
                NotifiableEvent.composedOf(
                    title="GDI Alert",
                    message=f"{process.displayName()} (PID {process.pid}): GDI count is {count}",
                    app_name="CheckGDI",
                    app_icon="",
                    timeout=3,
                )
            )
