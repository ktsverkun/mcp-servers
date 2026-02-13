# YCLIENTS MCP Server

MCP-сервер для полного доступа к [YCLIENTS REST API](https://developer.yclients.com/) — 305 операций через 32 инструмента.

## Быстрый старт

### Требования

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (рекомендуется) или pip
- Partner-токен YCLIENTS (получить в [Маркетплейсе](https://yclients.com/marketplace))

### Установка

```bash
git clone <repo-url> yclients-mcp-server
cd yclients-mcp-server
uv sync
```

### Переменные окружения

| Переменная | Обязательна | Описание |
|---|---|---|
| `YCLIENTS_PARTNER_TOKEN` | Да | Партнёрский токен из Маркетплейса |
| `YCLIENTS_USER_TOKEN` | Нет | Пользовательский токен (для операций с данными компаний) |
| `MCP_TRANSPORT` | Нет | `stdio` (по умолчанию) или `http` |
| `MCP_HOST` | Нет | Хост для HTTP-режима (по умолчанию `0.0.0.0`) |
| `MCP_PORT` | Нет | Порт для HTTP-режима (по умолчанию `8000`) |
| `MCP_LOG_LEVEL` | Нет | Уровень логирования: `DEBUG`, `INFO`, `WARNING` (по умолчанию `INFO`) |

Скопируйте `.env.example` в `.env` и заполните токены:

```bash
cp .env.example .env
```

---

## Подключение

### Локально (Claude Desktop / Claude Code)

Добавьте в конфиг Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "yclients": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/yclients-mcp-server",
        "run", "yclients-mcp-server"
      ],
      "env": {
        "YCLIENTS_PARTNER_TOKEN": "ваш_партнёрский_токен",
        "YCLIENTS_USER_TOKEN": "ваш_пользовательский_токен"
      }
    }
  }
}
```

### Удалённо (HTTP)

Запуск сервера:

```bash
YCLIENTS_PARTNER_TOKEN=... YCLIENTS_USER_TOKEN=... MCP_TRANSPORT=http uv run yclients-mcp-server
```

Сервер будет доступен на `http://localhost:8000/mcp`.

Подключение клиента:

```json
{
  "mcpServers": {
    "yclients": {
      "url": "https://your-server.com/mcp"
    }
  }
}
```

### Docker

```bash
docker build -t yclients-mcp .
docker run -d -p 8000:8000 \
  -e YCLIENTS_PARTNER_TOKEN=... \
  -e YCLIENTS_USER_TOKEN=... \
  yclients-mcp
```

---

## Инструменты (32 шт.)

Каждый инструмент принимает два параметра:
- `operation` — имя операции (см. список ниже)
- `params` — словарь параметров:
  - Path-параметры (`company_id`, `client_id` и т.д.) — подставляются в URL
  - `"query"` — словарь query-параметров
  - `"body"` — тело запроса (для POST/PUT/PATCH)

### Пример вызова

```
yclients_clients(
  operation="get_client",
  params={"company_id": 123456, "id": 789}
)
```

```
yclients_clients(
  operation="create_clients_search",
  params={
    "company_id": 123456,
    "body": {"page": 1, "page_size": 50, "fields": ["name", "phone"]}
  }
)
```

### Список инструментов

| Инструмент | Описание | Кол-во операций |
|---|---|---|
| `yclients_auth` | Авторизация | 1 |
| `yclients_booking` | Онлайн-запись — формы, даты, сотрудники, услуги | 23 |
| `yclients_companies` | Компании и пользователи компаний | 8 |
| `yclients_services` | Услуги и категории услуг | 17 |
| `yclients_staff` | Сотрудники, должности, расчёт зарплат | 18 |
| `yclients_clients` | Клиенты — поиск, создание, импорт | 14 |
| `yclients_records` | Записи и визиты | 10 |
| `yclients_group_events` | Групповые события | 19 |
| `yclients_schedule` | Расписание, графики, лист ожидания | 23 |
| `yclients_comments` | Комментарии | 2 |
| `yclients_users` | Пользователи, роли, права | 8 |
| `yclients_finances` | Кассы, транзакции, ККМ, продажи | 13 |
| `yclients_loyalty` | Лояльность, карты, сертификаты, абонементы | 40 |
| `yclients_products` | Товары, категории, тех. карты | 23 |
| `yclients_inventory` | Склады, складские операции | 13 |
| `yclients_communications` | SMS и Email рассылки | 6 |
| `yclients_analytics` | Аналитика и Z-отчёты | 7 |
| `yclients_locations` | Страны, города, справочники | 3 |
| `yclients_images` | Изображения | 2 |
| `yclients_salon_chains` | Сети салонов | 1 |
| `yclients_custom_fields` | Дополнительные поля | 4 |
| `yclients_reviews` | Отзывы и чаевые | 2 |
| `yclients_resources` | Ресурсы | 1 |
| `yclients_marketplace` | Маркетплейс | 13 |
| `yclients_telephony` | Телефония | 2 |
| `yclients_fiscalization` | Фискализация чеков | 3 |
| `yclients_licenses` | Лицензии | 1 |
| `yclients_privacy` | Правила обработки ПД | 1 |
| `yclients_validation_tools` | Валидация данных | 1 |
| `yclients_personal_accounts` | Личные счета | 5 |
| `yclients_notifications` | Уведомления | 3 |
| `yclients_misc` | Прочее (настройки, типы абонементов) | 18 |

---

## Обновление спецификации

API YCLIENTS может меняться. Для синхронизации:

```bash
# Проверить, есть ли изменения (без обновления)
python scripts/sync_spec.py --dry-run

# Обновить спецификацию и перегенерировать инструменты
python scripts/sync_spec.py

# Принудительная перегенерация
python scripts/sync_spec.py --force
```

Скрипт скачивает HTML с `developer.yclients.com`, извлекает OpenAPI-спецификацию, сравнивает с текущей и при наличии изменений перегенерирует все tool-модули.

### Автоматическая проверка (GitHub Actions)

В проекте настроен workflow `.github/workflows/sync-spec.yml`:
- Запускается каждый понедельник в 9:00 UTC
- Можно запустить вручную (кнопка "Run workflow")
- При обнаружении изменений создаёт Pull Request

### Автоматическая проверка (cron)

```bash
# Каждый понедельник в 9:00
0 9 * * 1 cd /path/to/yclients-mcp-server && python scripts/sync_spec.py >> /var/log/yclients-sync.log 2>&1
```

---

## Структура проекта

```
yclients-mcp-server/
├── pyproject.toml                 # Зависимости
├── Dockerfile                     # Docker-образ
├── .env.example                   # Шаблон переменных окружения
├── scripts/
│   └── sync_spec.py               # Синхронизация спецификации
├── data/
│   ├── yclients_openapi.json      # OpenAPI 3.0.3 спецификация
│   └── tag_endpoints.json         # Эндпоинты сгруппированные по тегам
├── src/yclients_mcp/
│   ├── server.py                  # Точка входа FastMCP
│   ├── config.py                  # Конфигурация из ENV
│   ├── auth.py                    # Формирование заголовков авторизации
│   ├── client.py                  # HTTP-клиент с rate limiting
│   └── tools/                     # 32 модуля инструментов (авто-генерация)
│       ├── __init__.py
│       ├── auth.py
│       ├── booking.py
│       ├── clients.py
│       └── ...
└── .github/workflows/
    └── sync-spec.yml              # Авто-проверка обновлений API
```

## Лимиты API

- 5 запросов в секунду
- 200 запросов в минуту

Встроенный rate limiter автоматически соблюдает эти лимиты.

## Лицензия

MIT
