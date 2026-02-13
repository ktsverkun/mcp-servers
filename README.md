# MCP Servers — Combined Deployment

Единый деплой двух MCP серверов через Docker Compose + nginx:

| Сервер | Endpoint | Описание |
|--------|----------|----------|
| yclients-mcp-server | `http://host/yclients/mcp` | YCLIENTS API (управление записями, клиентами, расписанием и т.д.) |
| ozon-mcp-server | `http://host/ozon/mcp` | Ozon.ru парсинг (поиск товаров, цены, категории) |

## Структура

```
mcp-servers/
├── docker-compose.yml   # Оркестрация: yclients + ozon + nginx
├── nginx.conf           # Reverse proxy: /yclients/* и /ozon/*
├── .env                 # Переменные окружения (создать из .env.example)
└── .env.example         # Шаблон переменных
```

```
mcp-servers/
├── docker-compose.yml
├── nginx.conf
├── .env.example
├── .gitignore
├── README.md
├── yclients-mcp-server/   # Python/FastMCP
└── ozon-mcp-server/       # Node.js/Playwright
```

## Быстрый старт (локально)

```bash
# 1. Скопировать и заполнить переменные
cp .env.example .env
# Заполнить YCLIENTS_PARTNER_TOKEN в .env

# 2. Запустить
docker compose up --build

# 3. Проверить
curl http://localhost/health
curl http://localhost/                # информация об endpoint'ах
```

## Проверка MCP серверов

```bash
# YClients
curl -X POST http://localhost/yclients/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}'

# Ozon
curl -X POST http://localhost/ozon/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}'
```

## Деплой на Timeweb.cloud App Platform

1. Создать новое приложение в [App Platform](https://timeweb.cloud/services/apps)
2. Выбрать **"Docker Compose"** как тип деплоя
3. Подключить репозиторий (GitHub/GitLab/Bitbucket)
4. Указать путь к `docker-compose.yml`: `mcp-servers/docker-compose.yml` *(или корень репо)*
5. В разделе **"Переменные окружения"** добавить значения из `.env.example`:
   - `YCLIENTS_PARTNER_TOKEN` — обязательно
   - `YCLIENTS_USER_TOKEN` — опционально
6. Деплой

> Это монорепо — весь код в одном репозитории, Timeweb видит всё сразу.

## Настройка в Claude Desktop / Claude Code

```json
{
  "mcpServers": {
    "yclients": {
      "type": "http",
      "url": "http://your-host/yclients/mcp"
    },
    "ozon": {
      "type": "http",
      "url": "http://your-host/ozon/mcp"
    }
  }
}
```

## Переменные окружения

| Переменная | Обязательно | Описание |
|-----------|-------------|----------|
| `YCLIENTS_PARTNER_TOKEN` | **Да** | Партнёрский токен YCLIENTS |
| `YCLIENTS_USER_TOKEN` | Нет | Пользовательский токен для операций с данными |

Остальные переменные (`MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT`, `PORT`, `NODE_ENV`) уже заданы в `docker-compose.yml` и не требуют изменений.
