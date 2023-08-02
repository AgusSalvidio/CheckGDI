from process_manager import ProcessManager
from config_manager import ConfigManager

from notifier import Notifier


class ApplicationContext:
    def __init__(self):
        self.process_manager = ProcessManager()
        self.config_manager = ConfigManager()
        self.notifier = Notifier()
        self.fileName = "checkGDI-settings.ini"

    def loadConfigFromFile(self):
        self.config_manager.loadConfigFrom(self.fileName)

    def loadedProcess(self):
        self.loadConfigFromFile()
        process_name = self.config_manager.processName()
        return self.process_manager.processNamed(process_name)

    def gdiCountFor(self, aProcess):
        return self.process_manager.gdiCountFor(aProcess)

    def gdiInfoAmount(self):
        return self.config_manager.gdiInfoAmount()

    def gdiWarningAmount(self):
        return self.config_manager.gdiWarningAmount()

    def checkEvery(self):
        return self.config_manager.checkEvery()

    def iconPath(self):
        return self.config_manager.iconPath()

    def publish(self, aNotifiableEvent):
        self.notifier.publish(aNotifiableEvent)
