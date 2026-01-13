# homework-bot

Простой Telegram-бот для отслеживания статуса домашних работ через API Practicum.

## Быстрый старт

1. Клонировать репозиторий и перейти в рабочую папку;

2. Создать виртуальное окружение и установить зависимости:
   - python -m venv venv
   - venv\Scripts\activate
   - pip install -r requirements.txt

3. Создать файл `.env` в корне проекта с переменными:

```
PRACTICUM_TOKEN=<ваш_yandexpracticum_token>
TELEGRAM_TOKEN=<token_вашего_бота>
TELEGRAM_CHAT_ID=<ваш_chat_id_в_telegram>
```

4. Запуск бота:
   - python homework.py

## Как это работает

- При запуске скрипт загружает переменные окружения из `.env`.
- Периодически опрашивает эндпоинт YandexPracticum и проверяет список домашних работ.
- При смене статуса последней работы отправляет уведомление в Telegram.
- Логи выводятся в stdout через StreamHandler (настройка уже присутствует в коде).
