FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci --omit=dev \
    && npm install -g supergateway

COPY index.js eng.traineddata ./
COPY tools/ tools/

ENV PORT=8002

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD node -e "require('net').createConnection(8002,'localhost').on('connect',()=>process.exit(0)).on('error',()=>process.exit(1))"

# Wrap the stdio MCP server with supergateway to expose HTTP/SSE transport
CMD ["supergateway", "--port", "8002", "--stdio", "node /app/index.js"]
