import re

DATAJUD_ALIAS_REGEX = re.compile(r"^[a-z0-9-]+$")
DATAJUD_ALIAS_MIN_LENGTH = 2
DATAJUD_ALIAS_MAX_LENGTH = 30


def normalize_datajud_tribunal_alias(value: str | None) -> str | None:
    if value is None:
        return None

    alias = value.strip().lower()
    if (
        len(alias) < DATAJUD_ALIAS_MIN_LENGTH
        or len(alias) > DATAJUD_ALIAS_MAX_LENGTH
        or not DATAJUD_ALIAS_REGEX.match(alias)
    ):
        raise ValueError("Alias do tribunal inválido")
    return alias
