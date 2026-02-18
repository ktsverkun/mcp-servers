FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci --omit=dev

COPY index.js eng.traineddata ./
COPY tools/ tools/

ENV MCP_TRANSPORT=http
ENV MCP_PORT=8002

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD node -e "require('net').createConnection(8002,'localhost').on('connect',()=>process.exit(0)).on('error',()=>process.exit(1))"

CMD ["node", "index.js"]
