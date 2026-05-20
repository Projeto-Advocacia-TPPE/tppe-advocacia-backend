def render(payload: dict) -> tuple[str, str]:
    """
    payload:
      process_number: str
      deadline_type: str
      due_date: str  (ISO 8601)
    """
    process_number = payload["process_number"]
    deadline_type = payload["deadline_type"]
    due_date = payload["due_date"]

    subject = f"Prazo VENCIDO: {deadline_type} ({process_number})"
    html = (
        f"<p><b>Atenção:</b> o prazo <b>{deadline_type}</b> do processo "
        f"<b>{process_number}</b> venceu em <b>{due_date}</b>.</p>"
        f"<p>Verifique imediatamente a situação processual.</p>"
    )
    return subject, html
