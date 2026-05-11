from typing import Protocol


class EmailService(Protocol):
    def send(self, to: str, subject: str, html: str) -> None: ...
