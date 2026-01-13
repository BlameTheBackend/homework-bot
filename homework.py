import logging
import os
import requests
import sys
import time
from http import HTTPStatus

from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import (
    MissingKeysException,
    UnexpectedStatusException,
    UnsuccessfulResponseException,
)


load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(
    logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
)

logger.addHandler(stream_handler)

PRACTICUM_TOKEN: str | None = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: str | None = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: str | None = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD: int = 600
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict[str, str] = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS: dict[str, str] = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


def check_tokens() -> None:
    """Проверка на наличие переменных окружения.

    При отсутствии одной или нескольких переменных - логирует и отправляет
    сообщение пользователю о критической ошибке.
    """
    variables: dict[str, str | None] = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    missing: tuple[str, ...] = tuple(
        var for var, val in variables.items() if not val)
    if missing:
        raise MissingKeysException(
            f'Отсутствуют переменные окружения: {missing}'
        )


def send_message(bot: TeleBot, message: str) -> None:
    """Отправка сообщения от телеграм-бота.

    Логирование сообщений с уровнем debug;
    Логирование ошибок с уровнем error и отправление отчета пользователю.

    Args:
        bot: Клиент телеграм-бота.
        message: Сообщение для отправки.
    """
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Бот отправил сообщение: "{message}".')
    except Exception as e:
        logger.error(f'При отправке сообщения произошла ошибка: {e}')


def get_api_answer(timestamp: int) -> dict:
    """Получение ответа от эндпоинта.

    Логирует ошибки с уровнем error

    Args:
        timestamp: Точка отсчета в виде даты,
            представленной в Unix time формате.

    Returns:
        json объект, содержащий ответ эндпоинта.

    Raises:
        Exception: Сторонняя ошибка, связанная с эндпоинтом.
    """
    try:
        request = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except requests.RequestException:
        logger.error('Ошибка соединения с эндпоинтом.')
    if request.status_code != HTTPStatus.OK:
        raise UnsuccessfulResponseException('Неуспешный ответ от API.')
    return request.json()


def check_response(response: dict) -> None:
    """Проверяет ответ API на наличие ожидаемых ключей.

    Args:
        response: Ответ API в виде словаря.
    """
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем.')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('Ключ "homeworks" не является списком.')


def parse_status(homework: dict) -> str:
    """Возвращает строку при изменении статуса работы.

    Args:
        homework: Словарь с информацией о домашней работе.

    Returns:
        Строку с информацией о статусе работы.

    Raises:
        MissingKeysException: Отсутствует ключ "homework_name".
        UnexpectedStatusException: Получен неожиданный статус.
    """
    homework_name: str | None = homework.get('homework_name')
    if not homework_name:
        raise MissingKeysException('Отсутствует ключ "homework_name".')
    homework_status: str | None = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise UnexpectedStatusException('Получен неожиданный статус.')
    return (f'Изменился статус проверки работы "{homework_name}". '
            f'Работа проверена: {HOMEWORK_VERDICTS[homework_status]}')


def report_error(bot: TeleBot, prev_message: str | None, message: str) -> None:
    """Логирует и отправляет сообщение об ошибке.

    Отправляет сообщение только если оно отличается от предыдущего.

    Args:
        bot: Клиент телеграм-бота.
        prev_message: Предыдущее сообщение об ошибке.
        message: Сообщение об ошибке.
    """
    logger.error(message)
    if prev_message != message:
        send_message(bot, message)


def main() -> None:
    """Основная логика работы бота.

    Содержит бесконечный цикл, прерывающийся при получении исключения.
    """
    bot: TeleBot = TeleBot(TELEGRAM_TOKEN)
    try:
        check_tokens()
    except MissingKeysException as e:
        logger.critical(e)
        send_message(bot, str(e))
        return

    timestamp: int = int(time.time())
    prev_error_message: str | None = None
    last_status: str | None = None

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)

            homeworks = response.get('homeworks')
            if not homeworks:
                logger.debug('Список домашних работ пуст.')
                time.sleep(RETRY_PERIOD)
                continue

            homework = homeworks[-1]
            current_status = homework.get('status')
            if current_status != last_status:
                message = parse_status(homework)
                send_message(bot, message)
                last_status = current_status
            else:
                logger.debug('Отсутствуют изменения в статусе работы.')

            parse_status(homework)
            time.sleep(RETRY_PERIOD)
        except Exception as error:
            report_error(bot, prev_error_message, str(error))
            prev_error_message = str(error)
            return


if __name__ == '__main__':
    main()
