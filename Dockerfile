# Optional sandbox for the autonomous run (any Docker engine works; Docker Desktop not required).
#   docker build -t housing-agent .
#   docker run -it --rm -v "$PWD":/workspace -v housing-claude:/home/agent/.claude housing-agent claude   # log in once
#   docker run -d --name housing-run -v "$PWD":/workspace -v housing-claude:/home/agent/.claude housing-agent bash run-agent.sh
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      git curl wget unzip jq ca-certificates nodejs npm coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code@2.1.322
COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /usr/local/bin/uv

RUN useradd -m -u 1000 agent \
    && git config --system user.name "Housing Agent" \
    && git config --system user.email "agent@localhost" \
    && git config --system --add safe.directory /workspace

USER agent
WORKDIR /workspace
