def render(payload: dict) -> tuple[str, str]:
    """
    payload:
      task_id: int
      task_title: str
      due_date: str | None  (ISO 8601)
    """
    task_id = payload["task_id"]
    task_title = payload["task_title"]
    due_date = payload.get("due_date")

    subject = f"Nova tarefa atribuída: {task_title}"
    body = (
        f"<p>Uma nova tarefa foi atribuída a você.</p>"
        f"<p><b>#{task_id} - {task_title}</b></p>"
    )
    if due_date:
        body += f"<p><b>Prazo:</b> {due_date}</p>"
    return subject, body
