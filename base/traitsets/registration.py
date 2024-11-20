class Registration:
    name: str
    enabled: bool

    def __init__(self, name: str, enabled: bool):
        self.name = name
        self.enabled = enabled

    def __str__(self) -> str:
        return self.name
