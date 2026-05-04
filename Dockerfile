FROM python:3.12-slim

# system deps
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# install uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# dependency caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# app source
COPY . .

EXPOSE 8000

# IMPORTANT: run gunicorn directly
CMD ["gunicorn",
     "-k", "uvicorn.workers.UvicornWorker",
     "app.main:app",
     "--bind", "0.0.0.0:8000",
     "--workers", "4",
     "--timeout", "120"]