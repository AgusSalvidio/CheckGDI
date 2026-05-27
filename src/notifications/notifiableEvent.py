class NotifiableEvent:
    def __init__(self, title: str, message: str, app_name: str, app_icon: str, timeout: int):
        self.title = title
        self.message = message
        self.app_name = app_name
        self.app_icon = app_icon
        self.timeout = timeout

    @classmethod
    def composedOf(cls, title: str, message: str, app_name: str, app_icon: str, timeout: int):
        return cls(title=title, message=message, app_name=app_name, app_icon=app_icon, timeout=timeout)
