from html import escape


def render(payload: dict) -> tuple[str, str]:
    """
    payload:
      provider: str
      operation: str
      http_status: int | None
      error_code: str | None
      error_message: str | None
      request_identifier: str | None
      tribunal_alias: str | None
    """
    provider = escape(payload["provider"])
    operation = escape(payload["operation"])
    http_status = escape(str(payload.get("http_status") or "-"))
    error_code = escape(payload.get("error_code") or "-")
    error_message = escape(payload.get("error_message") or "Sem mensagem de erro")
    request_identifier = escape(payload.get("request_identifier") or "-")
    tribunal_alias = escape(payload.get("tribunal_alias") or "-")

    subject = f"Falha em integração externa: {provider}"
    html = (
        "<p>Uma chamada a API externa falhou.</p>"
        "<ul>"
        f"<li><b>Provider:</b> {provider}</li>"
        f"<li><b>Operação:</b> {operation}</li>"
        f"<li><b>Status HTTP:</b> {http_status}</li>"
        f"<li><b>Código:</b> {error_code}</li>"
        f"<li><b>Processo/identificador:</b> {request_identifier}</li>"
        f"<li><b>Tribunal:</b> {tribunal_alias}</li>"
        f"<li><b>Erro:</b> {error_message}</li>"
        "</ul>"
    )
    return subject, html
