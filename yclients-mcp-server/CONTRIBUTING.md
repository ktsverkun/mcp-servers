# Contributing

## Установка для разработки

```bash
git clone <repo-url>
cd yclients-mcp-server
uv sync          # установит и dev-зависимости
```

## Рабочий процесс

```bash
make lint        # проверить код линтером (ruff)
make format      # отформатировать код
make typecheck   # проверить типы (mypy)
make test        # запустить тесты
make all         # lint + typecheck + test
```

## Структура кода

```
src/yclients_mcp/
├── server.py        # Точка входа FastMCP (не менять без необходимости)
├── config.py        # Конфигурация из ENV
├── auth.py          # Формирование заголовков авторизации
├── client.py        # HTTP-клиент с rate limiting и _build_path()
└── tools/           # 32 модуля (авто-генерация!)
    ├── __init__.py  # register_all_tools()
    ├── clients.py
    └── ...
```

**Важно:** файлы в `tools/` генерируются автоматически скриптом `scripts/sync_spec.py`. Не редактируйте их вручную — изменения будут перезаписаны при следующей синхронизации.

## Как добавить новый тег API

Если YCLIENTS добавил новую группу эндпоинтов с новым тегом:

1. Добавьте маппинг тега в `TAG_TO_MODULE` внутри `scripts/sync_spec.py`
2. Добавьте описание модуля в `MODULE_DESC`
3. Запустите `python scripts/sync_spec.py --force`
4. Проверьте: `make test`

## Как менять core-логику

Файлы `config.py`, `auth.py`, `client.py`, `server.py` — ручные. Меняйте напрямую:

- `client.py` — HTTP-клиент, rate limiter, `_build_path()`
- `auth.py` — формирование заголовков
- `config.py` — переменные окружения

После изменений: `make all`

## Обновление OpenAPI-спецификации

```bash
make sync        # скачать свежую спецификацию и перегенерировать tools/
make sync-dry    # проверить, есть ли изменения (без обновления)
```

## Коммиты

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new tool for webhook management
fix: handle 429 rate limit correctly
chore: sync YCLIENTS API spec
docs: update README with new tool list
```

## Тесты

Тесты в `tests/`:

- `test_config.py` — конфигурация
- `test_auth.py` — заголовки авторизации
- `test_client.py` — HTTP-клиент, `_build_path()`, мок-запросы
- `test_tools.py` — проверка всех 32 tool-модулей (формат, наличие операций)

Для мокирования HTTP-запросов используется [respx](https://lundberg.github.io/respx/).
