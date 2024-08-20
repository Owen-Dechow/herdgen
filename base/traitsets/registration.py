class Registration:
    def __init__(self, name: str, enabled: bool):
        self.name = name
        self.enabled = enabled

    def __str__(self) -> str:
        return self.name
