# Мониторинг демо-консультаций B17.ru

Скрипт раз в 10 минут проверяет [форум B17.ru](https://www.b17.ru/forum/) и отправляет уведомление в Telegram, если появилась новая тема формата «демо-консультация» (`ico_svg_f2`) без ответов.

## Критерии отбора

- Иконка темы: `ico_svg_f2` (консультация с одним специалистом)
- Количество ответов в колонке `td.n`: `0`
- Повторные уведомления по одной теме не отправляются

## Локальный запуск

```bash
pip install -r requirements.txt
cp .env.example .env
# заполните TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env
```

На Windows (PowerShell):

```powershell
$env:TELEGRAM_BOT_TOKEN="..."
$env:TELEGRAM_CHAT_ID="..."
python main.py
```

Тесты:

```bash
pip install pytest
pytest test_parser.py -v
```

## Настройка Telegram

1. Создайте бота через [@BotFather](https://t.me/BotFather) и получите токен.
2. Напишите боту `/start` с аккаунта [@iana_svet108](https://t.me/iana_svet108).
3. Откройте в браузере:

   ```
   https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates
   ```

4. Найдите `"chat":{"id":123456789,...}` — это ваш `TELEGRAM_CHAT_ID`.

## Деплой на Railway

1. Залейте репозиторий на GitHub.
2. В [Railway](https://railway.com): **New Project** → **Deploy from GitHub repo**.
3. Cron-расписание подтянется из [`railway.toml`](railway.toml): `*/10 * * * *` (UTC, каждые 10 минут).
4. Добавьте **Volume**, смонтируйте в `/data`.
5. В **Variables** сервиса задайте:

   | Переменная | Значение |
   |------------|----------|
   | `TELEGRAM_BOT_TOKEN` | токен бота |
   | `TELEGRAM_CHAT_ID` | числовой chat_id |
   | `DATA_DIR` | `/data` |

6. Сделайте **Redeploy** и проверьте логи первого запуска.

## Переменные окружения

| Переменная | Обязательна | По умолчанию |
|------------|-------------|--------------|
| `TELEGRAM_BOT_TOKEN` | да | — |
| `TELEGRAM_CHAT_ID` | да | — |
| `DATA_DIR` | нет | `./data` |
| `FORUM_URL` | нет | `https://www.b17.ru/forum/` |

## Как это работает

1. Скрипт загружает главную страницу форума.
2. Ищет строки `tr.list` с `ico_svg_f2` и `0` ответов.
3. Сравнивает найденные темы с `seen_topics.json` в `DATA_DIR`.
4. Отправляет уведомления только о новых темах.
5. Сохраняет ID уведомлённых тем (записи старше 7 дней удаляются).

## Формат уведомления

```
Новая демо-консультация без ответов

Заголовок темы
Автор: … (Консультирует: …)

https://www.b17.ru/forum/topic.php?id=XXXXX
```
