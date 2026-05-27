class Process:
    def __init__(self, name: str, pid: int, exe: str | None = None, description: str | None = None):
        self.name = name
        self.pid = pid
        self.exe = exe
        self.description = description

    @classmethod
    def composedOf(cls, name: str, pid: int, exe: str | None = None, description: str | None = None):
        return cls(name=name, pid=pid, exe=exe, description=description)

    def displayName(self) -> str:
        return self.description or self.name
