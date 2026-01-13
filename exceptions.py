class InvalidJSONException(Exception):
    """Возникает при получении ответа не в формате JSON."""

    pass


class InvalidResponseException(TypeError):
    """Возникает при получении некорректного ответа от API."""

    pass


class MissingKeysException(Exception):
    """Возникает при отсутствии необходимых ключей."""

    pass


class UnexpectedStatusException(Exception):
    """Возникает при получении неожиданного значения статуса."""

    pass


class UnsuccessfulResponseException(Exception):
    """Возникает при получении ответа, отличного от статус кода 200."""

    pass
