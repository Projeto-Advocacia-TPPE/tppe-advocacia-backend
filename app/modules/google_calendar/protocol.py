from typing import Protocol


class GoogleCalendarClient(Protocol):
    """Operações sobre o Google Calendar de um usuário.

    `event` é o corpo de evento já no formato da Google Calendar API.
    As implementações recebem o `refresh_token` em texto puro (já
    descriptografado pelo service).
    """

    def create_event(self, refresh_token: str, event: dict) -> str:
        """Cria o evento e retorna o `google_event_id`."""
        ...

    def update_event(self, refresh_token: str, event_id: str, event: dict) -> None: ...

    def delete_event(self, refresh_token: str, event_id: str) -> None: ...
