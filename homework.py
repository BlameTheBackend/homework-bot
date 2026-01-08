import logging
import os
import requests
import time
from datetime import datetime

from dotenv import load_dotenv
from telebot import TeleBot

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    variables = {PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID}
    missing = [var for var in variables if var is None]
    if missing:
        logging.critical(f'{datetime.now()} [CRITICAL]'
                         + 'Отсутствует одна или несколько обязательных '
                         + 'переменных окружения!')


def send_message(bot, message):
    bot.send_message(message)
    logging.debug('Сообщение отправлено успешно.')


def get_api_answer(timestamp):
    request = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params={'from_date': timestamp}
    )
    return request.json()


def check_response(response):
    if isinstance(response, dict):
        return True
    else:
        return False


def parse_status(homework):
    status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(status)
    homework_name = homework.get('homework_name')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = TeleBot(TELEGRAM_TOKEN)
    if not check_tokens():
        return
    timestamp = int(time.time())
    current_status = None

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            previous_status = current_status
            homework = response[0].get('homeworks')[-1]
            current_status = parse_status(homework)
            if previous_status != current_status:
                send_message(HOMEWORK_VERDICTS.get(current_status))
            bot.polling(interval=RETRY_PERIOD)
            time.sleep(RETRY_PERIOD)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'


if __name__ == '__main__':
    main()
