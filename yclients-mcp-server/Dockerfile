FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
COPY src/ src/
COPY data/ data/

RUN uv sync --no-dev

ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import socket; s = socket.create_connection(('localhost', 8000), timeout=5); s.close()" || exit 1

CMD ["uv", "run", "yclients-mcp-server"]
