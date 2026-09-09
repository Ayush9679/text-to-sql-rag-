FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml* requirements.txt* ./
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    pydantic-settings \
    sqlalchemy \
    psycopg[binary] \
    alembic \
    pgvector \
    pandas \
    python-multipart \
    groq \
    python-dotenv \
    pyjwt \
    cryptography \
    sqlglot \
    pytest

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
