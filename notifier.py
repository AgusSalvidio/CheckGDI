from plyer import notification


class Notifier:
    def publish(self, aNotifiableEvent):
        notification.notify(
            title=aNotifiableEvent.title,
            message=aNotifiableEvent.message,
            app_name=aNotifiableEvent.app_name,
            app_icon=aNotifiableEvent.app_icon,
            timeout=aNotifiableEvent.timeout)
