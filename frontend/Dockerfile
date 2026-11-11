# syntax=docker/dockerfile:1
# Frontend image: Vite production build served by nginx (non-root), which also proxies /api
# to the backend service so the app calls the API on the same origin.
# Build context: frontend/   (compose.yaml sets this).
# Untested here: Docker is not installed on the machine this was written on.

# --- Build stage ---
FROM node:22.23-alpine AS build
WORKDIR /src
RUN --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=package-lock.json,target=package-lock.json \
    --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund
COPY . .
# Empty VITE_API_BASE_URL = same origin; nginx forwards /api to the backend.
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# --- Runtime stage: static files only ---
FROM nginxinc/nginx-unprivileged:1.29-alpine AS runtime
LABEL org.opencontainers.image.source="https://github.com/shivarv/AutonomousAgentHousingPrices" \
      org.opencontainers.image.title="housing-frontend"
COPY --link nginx.conf /etc/nginx/conf.d/default.conf
COPY --link --from=build /src/dist /usr/share/nginx/html
# nginx-unprivileged runs as uid 101 and listens on 8080.
USER 101
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/healthz"]
