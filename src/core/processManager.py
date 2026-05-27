import psutil
from ctypes import windll
from src.core.process import Process


class ProcessManager:
    def __init__(self):
        self._descriptionCache: dict[str, str | None] = {}

    def processesNamed(self, names: list[str]) -> list[Process]:
        """Return all running processes whose name matches any of the given names."""
        results = []
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                if any(n.lower() in proc.info["name"].lower() for n in names):
                    exe = proc.info.get("exe")
                    results.append(
                        Process.composedOf(
                            name=proc.info["name"],
                            pid=proc.info["pid"],
                            exe=exe,
                            description=self._fileDescriptionFor(exe),
                        )
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return results

    def gdiCountFor(self, process: Process) -> int | None:
        handle = windll.kernel32.OpenProcess(0x400, 0, process.pid)
        if not handle:
            return None
        count = windll.user32.GetGuiResources(handle, 0)
        windll.kernel32.CloseHandle(handle)
        return count or None

    def _fileDescriptionFor(self, exePath: str | None) -> str | None:
        if not exePath:
            return None
        if exePath not in self._descriptionCache:
            self._descriptionCache[exePath] = self._readFileDescription(exePath)
        return self._descriptionCache[exePath]

    @staticmethod
    def _readFileDescription(exePath: str) -> str | None:
        try:
            import win32api
            pairs = win32api.GetFileVersionInfo(exePath, r"\VarFileInfo\Translation")
            lang, cp = pairs[0]
            key = f"\\StringFileInfo\\{lang:04x}{cp:04x}\\FileDescription"
            desc = win32api.GetFileVersionInfo(exePath, key)
            return desc.strip() or None
        except Exception:
            return None
