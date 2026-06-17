"""Entrypoint standalone para o scheduler (produção).

Roda como processo separado do Gunicorn para evitar disparo duplicado
de jobs em ambientes multi-worker. Configure SCHEDULER_ENABLED=false
no serviço da API e mantenha true aqui.

Uso:
    python scripts/run_scheduler.py
"""

import logging
import signal
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    from app.scheduler.scheduler import shutdown_scheduler, start_scheduler

    start_scheduler()
    logger.info("Scheduler process running")

    def handle_shutdown(sig: int, _frame: object) -> None:
        logger.info("Scheduler shutting down (signal %d)", sig)
        shutdown_scheduler()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
