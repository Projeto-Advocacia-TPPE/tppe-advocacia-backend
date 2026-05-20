def render(payload: dict) -> tuple[str, str]:
    """
    payload:
      process_number: str
      deadline_type: str
      due_date: str  (ISO 8601)
      business_days_left: int
    """
    process_number = payload["process_number"]
    deadline_type = payload["deadline_type"]
    due_date = payload["due_date"]
    days_left = payload["business_days_left"]

    subject = f"Prazo se aproximando: {deadline_type} ({process_number})"
    html = (
        f"<p>O prazo <b>{deadline_type}</b> do processo "
        f"<b>{process_number}</b> vence em "
        f"<b>{days_left} dia(s) útil(eis)</b>.</p>"
        f"<p>Data-limite: <b>{due_date}</b>.</p>"
        f"<p>Providencie a peça ou medida necessária a tempo.</p>"
    )
    return subject, html
