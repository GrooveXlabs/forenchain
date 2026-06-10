FROM python:3.11-slim

WORKDIR /app

# Install system deps for psycopg2 and cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY forenchain/ ./forenchain/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Run as non-root
RUN useradd --no-create-home --shell /bin/false forenchain
USER forenchain

EXPOSE 8000

CMD ["uvicorn", "forenchain.infrastructure.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
