from configparser import ConfigParser

class ConfigManager:
    def __init__(self):
        self.configParser = ConfigParser()
        self.process_name = None
        self.icon_path = None
        self.gdi_info_amount = None
        self.gdi_warning_amount = None
        self.check_every = 0

    def loadConfigFrom(self, aFileName):
        self.configParser.read(aFileName)
        self.process_name = self.configParser.get("CONFIG", "PROCESS_NAME")
        self.icon_path = (self.configParser.get("CONFIG", "ICON_PATH"))
        self.gdi_info_amount = int(self.configParser.get("CONFIG", "GDI_INFO_AMOUNT"))
        self.gdi_warning_amount = int(self.configParser.get(
            "CONFIG", "GDI_WARNING_AMOUNT"))
        self.check_every = int(self.configParser.get(
            "CONFIG", "CHECK_EVERY"))

    def processName(self):
        return self.process_name

    def gdiInfoAmount(self):
        return self.gdi_info_amount

    def gdiWarningAmount(self):
        return self.gdi_warning_amount

    def iconPath(self):
        return self.icon_path

    def checkEvery(self):
        return self.check_every
