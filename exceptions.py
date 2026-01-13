class MissingKeysException(Exception):
    """Возникает при отсутствии необходимых ключей."""

    pass


class UnexpectedStatusException(Exception):
    """Возникает при получении неожиданного значения статуса."""

    pass


class UnsuccessfulResponseException(Exception):
    """Возникает при получении ответа, отличного от статус кода 200."""

    pass
