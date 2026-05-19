def render(payload: dict) -> tuple[str, str]:
    """
    payload:
      lead_id: int
      lead_name: str
      lead_email: str
      lead_phone: str | None
    """
    lead_id = payload["lead_id"]
    lead_name = payload["lead_name"]
    lead_email = payload["lead_email"]
    lead_phone = payload.get("lead_phone") or "-"

    subject = f"Você foi atribuído ao lead #{lead_id} - {lead_name}"
    html = (
        f"<p>Um novo lead foi atribuído a você.</p>"
        f"<ul>"
        f"<li><b>Nome:</b> {lead_name}</li>"
        f"<li><b>E-mail:</b> {lead_email}</li>"
        f"<li><b>Telefone:</b> {lead_phone}</li>"
        f"</ul>"
    )
    return subject, html
