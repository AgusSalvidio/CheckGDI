import copy

from src.core.processManager import ProcessManager
from src.config.configManager import ConfigManager, NEEDLE_THICKNESS_MIN, NEEDLE_THICKNESS_MAX
from src.config.settingsStore import SettingsStore
from src.notifications.notifier import Notifier
from src.notifications.notifiableEvent import NotifiableEvent
from src.core.process import Process

# Every one of these fields lives inside a profile and is swapped in/out when the user
# switches profiles. `viewStyle` is intentionally excluded — it's global, not per-profile.
PROFILE_FIELDS = (
    "gaugeStyle", "needleStyle", "needleColor", "zoneMode",
    "accentColor", "numberColor", "dialColor", "needleThickness",
)


class ApplicationContext:
    def __init__(self):
        self._processManager = ProcessManager()
        self._configManager = ConfigManager()
        self._notifier = Notifier()
        self._settingsStore = SettingsStore()
        # Runtime-overridable display settings, seeded from .env for the "Default" profile, then
        # overridden by whatever profiles/selection were last persisted from the UI (if any)
        saved = self._settingsStore.load()
        self._viewStyle = saved.get("viewStyle", self._configManager.viewStyle())

        defaultProfile = {field: getattr(self._configManager, field)() for field in PROFILE_FIELDS}

        self._profiles: dict = saved.get("profiles") or {}
        if not self._profiles:
            # Migrate a pre-profiles flat settings file (last-selected values) into "Default"
            self._profiles["Default"] = {
                field: saved.get(field, defaultProfile[field]) for field in PROFILE_FIELDS
            }

        self._activeProfile = saved.get("activeProfile", next(iter(self._profiles)))
        if self._activeProfile not in self._profiles:
            self._activeProfile = next(iter(self._profiles))

        self._values: dict = {}
        self._applyProfileValues(self._profiles[self._activeProfile])

        # While an edit session is open (settings dialog), changes are previewed live but
        # only written to disk once the session is committed — see beginEditSession() below.
        self._persistenceSuspended = False
        self._sessionSnapshot: dict | None = None

    def _applyProfileValues(self, values: dict) -> None:
        self._values = {field: values[field] for field in PROFILE_FIELDS}
        self._values["needleThickness"] = float(self._values["needleThickness"])

    def _currentProfileValues(self) -> dict:
        return dict(self._values)

    def _field(self, name: str):
        return self._values[name]

    def _setField(self, name: str, value) -> None:
        self._values[name] = value
        self._persistSettings()

    def _persistSettings(self) -> None:
        self._profiles[self._activeProfile] = self._currentProfileValues()
        if self._persistenceSuspended:
            return
        self._settingsStore.save({
            "viewStyle": self._viewStyle,
            "activeProfile": self._activeProfile,
            "profiles": self._profiles,
        })

    # ── Edit session (save/cancel workflow for the settings dialog) ─────────────

    def beginEditSession(self) -> None:
        """Snapshots the current state and stops writes to disk until commit/cancel,
        so the user can experiment (switch profiles, tweak colors) without touching
        the persisted file unless they explicitly choose to keep the changes."""
        if self._persistenceSuspended:
            return
        self._sessionSnapshot = {
            "viewStyle": self._viewStyle,
            "activeProfile": self._activeProfile,
            "profiles": copy.deepcopy(self._profiles),
        }
        self._persistenceSuspended = True

    def commitEditSession(self) -> None:
        """Keeps whatever is currently applied and writes it to disk."""
        self._persistenceSuspended = False
        self._sessionSnapshot = None
        self._persistSettings()

    def cancelEditSession(self) -> None:
        """Throws away every change made since beginEditSession() and restores the
        pre-session state (disk was never touched, so nothing needs to be re-saved)."""
        self._persistenceSuspended = False
        if self._sessionSnapshot is None:
            return
        self._viewStyle = self._sessionSnapshot["viewStyle"]
        self._profiles = self._sessionSnapshot["profiles"]
        self._activeProfile = self._sessionSnapshot["activeProfile"]
        self._applyProfileValues(self._profiles[self._activeProfile])
        self._sessionSnapshot = None

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

    def viewStyle(self) -> str:
        return self._viewStyle

    def setViewStyle(self, viewStyle: str) -> None:
        self._viewStyle = viewStyle
        self._persistSettings()

    def gaugeStyle(self) -> str:
        return self._field("gaugeStyle")

    def setGaugeStyle(self, gaugeStyle: str) -> None:
        self._setField("gaugeStyle", gaugeStyle)

    def needleStyle(self) -> str:
        return self._field("needleStyle")

    def setNeedleStyle(self, needleStyle: str) -> None:
        self._setField("needleStyle", needleStyle)

    def needleColor(self) -> str:
        return self._field("needleColor")

    def setNeedleColor(self, needleColor: str) -> None:
        self._setField("needleColor", needleColor)

    def zoneMode(self) -> str:
        return self._field("zoneMode")

    def setZoneMode(self, zoneMode: str) -> None:
        self._setField("zoneMode", zoneMode)

    def accentColor(self) -> str:
        return self._field("accentColor")

    def setAccentColor(self, accentColor: str) -> None:
        self._setField("accentColor", accentColor)

    def numberColor(self) -> str:
        return self._field("numberColor")

    def setNumberColor(self, numberColor: str) -> None:
        self._setField("numberColor", numberColor)

    def dialColor(self) -> str:
        return self._field("dialColor")

    def setDialColor(self, dialColor: str) -> None:
        self._setField("dialColor", dialColor)

    def needleThickness(self) -> float:
        return self._field("needleThickness")

    def setNeedleThickness(self, needleThickness: float) -> None:
        clamped = max(NEEDLE_THICKNESS_MIN, min(float(needleThickness), NEEDLE_THICKNESS_MAX))
        self._setField("needleThickness", clamped)

    # ── Profiles ──────────────────────────────────────────────────────────────

    def profileNames(self) -> list[str]:
        return list(self._profiles.keys())

    def activeProfile(self) -> str:
        return self._activeProfile

    def setActiveProfile(self, name: str) -> None:
        if name not in self._profiles or name == self._activeProfile:
            return
        self._activeProfile = name
        self._applyProfileValues(self._profiles[name])
        self._persistSettings()

    def createProfile(self, name: str) -> None:
        name = name.strip()
        if not name or name in self._profiles:
            return
        self._profiles[name] = self._currentProfileValues()
        self._activeProfile = name
        self._persistSettings()

    def deleteProfile(self, name: str) -> None:
        if name not in self._profiles or len(self._profiles) <= 1:
            return
        del self._profiles[name]
        if self._activeProfile == name:
            self._activeProfile = next(iter(self._profiles))
            self._applyProfileValues(self._profiles[self._activeProfile])
        self._persistSettings()
