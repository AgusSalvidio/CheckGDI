class NotifiableEvent:
    def __init__(self, title, message, app_name, app_icon, timeout):
        self.title = title
        self.message = message
        self.app_name = app_name
        self.app_icon = app_icon
        self.timeout = timeout

    @classmethod
    def composedOf(cls, title, message, app_name, app_icon, timeout):
        return cls(title=title, message=message, app_name=app_name, app_icon=app_icon, timeout=timeout)
