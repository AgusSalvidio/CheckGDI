from plyer import notification


class Notifier:
    def publish(self, event) -> None:
        try:
            notification.notify(
                title=event.title,
                message=event.message,
                app_name=event.app_name,
                app_icon=event.app_icon,
                timeout=event.timeout,
            )
        except Exception:
            pass
