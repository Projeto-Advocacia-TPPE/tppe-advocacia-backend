from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def unit_of_work(db: Session) -> Generator[None, None, None]:
    """Orquestra uma transação SQLAlchemy: commit no sucesso, rollback no erro.

    Convenção do projeto: Repositories nunca comitam — apenas `add`/`flush`.
    O Service envolve uma sequência de chamadas de repository neste bloco
    para garantir atomicidade. Efeitos colaterais (notificações, e-mails)
    devem ocorrer FORA do `with`, para só dispararem após o commit confirmado.
    """
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise
