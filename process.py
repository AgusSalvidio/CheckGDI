class Process:
    def __init__(self, name, pid):
        self.name = name
        self.pid = pid

    @classmethod
    def composedOf(cls, name, pid):
        return cls(name=name, pid=pid)
