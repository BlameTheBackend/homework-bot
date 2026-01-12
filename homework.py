import logging
import os
import requests
import time
from datetime import datetime

from dotenv import load_dotenv
from requests.exceptions import ConnectionError
from telebot import TeleBot


load_dotenv()

logging.basicConfig(level=logging.DEBUG)

PRACTICUM_TOKEN: str | None = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: str | None = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: str | None = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD: int = 600
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS: dict = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> None:
    """Проверка на наличие переменных окружения.

    При отсутствии одной или нескольких переменных - логирует и отправляет
    сообщение пользователю о критической ошибке.
    """
    variables: dict = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    missing: list = [var for var, val in variables.items() if not val]
    if missing:
        logging.critical(f'{datetime.now()} [CRITICAL] '
                         + 'Отсутствуют обязательные переменные окружения:'
                         + ', '.join(missing))


def send_message(bot: TeleBot, message: str) -> None:
    """Отправка сообщения от телеграм-бота.

    Логирование сообщений с уровнем debug;
    Логирование ошибок с уровнем error и отправление отчета пользователю.

    args:
        bot: Клиент телеграм-бота.
        message: Сообщение для отправки.
    """
    try:
        bot.send_message(message)
        logging.debug(f'{datetime.now()} [DEBUG] '
                      + f'Бот отправил сообщение: "{message}".')
    except Exception as e:
        logging.error(f'{datetime.now()} [ERROR] '
                      + f'При отправке сообщения произошла ошибка: {e}')


def get_api_answer(timestamp: int) -> dict:
    """Получение ответа от эндпоинта.

    Логирует ошибки с уровнем error

    Args:
        timestamp: Точка отсчета в виде даты,
            представленной в формате Unix time.

    Returns:
        Возвращает json объект, содержащий ответ эндпоинта.
    """
    try:
        request = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except ConnectionError as e:
        logging.error(f'{datetime.now()} [ERROR] Произошла ошибка '
                      + f'при подключении к эндпоинту {ENDPOINT}. '
                      + f'Код ответа API: {e.response.status_code}')
    except Exception as e:
        logging.error(f'{datetime.now()} [ERROR] Произошла сторонняя ошибка, '
                      + f'связанная с эндпоинтом YandexPracticum: {e}')
    return request.json()


def check_response(response) -> bool:
    """Проверяет ответ API на наличие ожидаемых ключей."""
    response_json = response.json()
    if response_json.get('homeworks') and response_json.get('current_date'):
        return True
    else:
        return False


def parse_status(homework):
    """Возвращает строку со статусом работы (если изменился статус)."""
    possible_statuses = HOMEWORK_VERDICTS.keys()
    status = homework.get('status')
    if status not in possible_statuses:
        logging.error(f'{datetime.now()} [ERROR] '
                      + 'Получили неожиданный статус домашней работы.')
    verdict = HOMEWORK_VERDICTS.get(status)
    return verdict


def main():
    """Основная логика работы бота."""
    bot = TeleBot(TELEGRAM_TOKEN)
    if not check_tokens():
        return
    timestamp = int(time.time())
    current_status = None
    error_sent = False

    while True:
        try:
            response = get_api_answer(timestamp)
            if not check_response(response):
                return
            previous_status = current_status
            homework = response[0].get('homeworks')[-1]
            current_status = parse_status(homework)
            if previous_status != current_status:
                send_message(bot, HOMEWORK_VERDICTS.get(current_status))
            else:
                logging.debug('Отсутствуют изменения в статусе работы.')
            bot.polling(interval=RETRY_PERIOD)
            time.sleep(RETRY_PERIOD)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if not error_sent:
                send_message(bot, message)


if __name__ == '__main__':
    main()
