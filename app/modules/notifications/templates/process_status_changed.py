def render(payload: dict) -> tuple[str, str]:
    """
    payload:
      process_number: str
      previous_status: str
      new_status: str
      reason: str | None
    """
    process_number = payload["process_number"]
    previous_status = payload["previous_status"]
    new_status = payload["new_status"]
    reason = payload.get("reason")

    subject = f"Status do processo {process_number} alterado"
    body = (
        f"<p>O status do processo <b>{process_number}</b> mudou de "
        f"<b>{previous_status}</b> para <b>{new_status}</b>.</p>"
    )
    if reason:
        body += f"<p><b>Motivo:</b> {reason}</p>"
    return subject, body
