# Compile JavaScript.
FROM docker.io/library/node:25.1.0-alpine3.21 AS frontend
WORKDIR /pisite
COPY package*.json tsconfig.json ./
COPY src/ src/
RUN npm ci
RUN npx tsc

FROM alpine:3.22.2 AS runner
# Set up Python environment.
WORKDIR /pisite
COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /uvx /bin/
COPY pisite/ pisite/
COPY pyproject.toml .
RUN uv sync
# Copy JavaScript.
# COPY --from=frontend /pisite/dist/*.js ./pisite/static/
RUN cp pisite/static/pisite.js.old pisite/static/pisite.js
