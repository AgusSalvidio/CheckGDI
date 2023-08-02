from notifiable_event import NotifiableEvent
import time


class ProcessChecker:
    def __init__(self, workingContext):
        self.workingContext = workingContext

    @classmethod
    def workingWith(cls, workingContext):
        return cls(workingContext=workingContext)

    def startChecking(self, aProcess):
        gdi_info_amount = self.workingContext.gdiInfoAmount()
        gdi_warning_amount = self.workingContext.gdiWarningAmount()

        while True:
            current_gdi_amount = self.workingContext.gdiCountFor(aProcess)
            print(f"GDIs actuales del proceso {aProcess.name}: {current_gdi_amount}")
            if current_gdi_amount >= gdi_warning_amount:
                print(f"Guarda que los GDIs subieron a: {current_gdi_amount}")
                self.workingContext.publish(NotifiableEvent.composedOf("Alerta de exceso de GDIs",
                                                                       f"Guarda que los GDIs subieron a: {current_gdi_amount}",
                                                                       "CheckGDI", self.iconPath(),
                                                                       5))
            self.delayInSeconds(self.defaultDelay())

    def iconPath(self):
        return self.workingContext.iconPath()

    def defaultDelay(self):
        return self.workingContext.checkEvery()

    def delayInSeconds(self, seconds):
        time.sleep(seconds)
