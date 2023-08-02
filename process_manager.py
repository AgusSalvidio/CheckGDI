import psutil
from ctypes import *
from process import *


class ProcessManager:
    def processNamed(self, aProcessName):
        for process in psutil.process_iter():
            try:
                if aProcessName.lower() in process.name().lower():
                    return Process.composedOf(aProcessName, process.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return None

    def gdiCountFor(self, aProcess):
        ph = windll.kernel32.OpenProcess(0x400, 0, aProcess.pid)
        gdi_count = windll.user32.GetGuiResources(ph, 0)
        windll.kernel32.CloseHandle(ph)
        return gdi_count
