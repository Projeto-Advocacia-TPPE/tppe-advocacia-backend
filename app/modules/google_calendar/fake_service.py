class FakeGoogleCalendarClient:
    """Implementação fake de `GoogleCalendarClient` para testes.

    Guarda os eventos em memória. Defina `fail = True` para simular
    indisponibilidade do Google.
    """

    def __init__(self) -> None:
        self.events: dict[str, dict] = {}
        self.fail: bool = False
        self._counter: int = 0

    def _maybe_fail(self) -> None:
        if self.fail:
            raise RuntimeError("Google Calendar unavailable (fake)")

    def create_event(self, refresh_token: str, event: dict) -> str:
        self._maybe_fail()
        self._counter += 1
        event_id = f"fake-event-{self._counter}"
        self.events[event_id] = event
        return event_id

    def update_event(self, refresh_token: str, event_id: str, event: dict) -> None:
        self._maybe_fail()
        self.events[event_id] = event

    def delete_event(self, refresh_token: str, event_id: str) -> None:
        self._maybe_fail()
        self.events.pop(event_id, None)
