def render(payload: dict) -> tuple[str, str]:
    """
    payload:
      process_number: str
      title: str
      description: str | None
      occurred_at: str  (ISO 8601)
    """
    process_number = payload["process_number"]
    title = payload["title"]
    description = payload.get("description") or ""
    occurred_at = payload["occurred_at"]

    subject = f"Nova movimentação no processo {process_number}"
    html = (
        f"<p>Uma nova movimentação foi registrada no processo "
        f"<b>{process_number}</b>.</p>"
        f"<p><b>{title}</b></p>"
        f"<p>{description}</p>"
        f"<p><small>Ocorrida em: {occurred_at}</small></p>"
    )
    return subject, html
