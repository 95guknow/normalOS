FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install uv && uv sync --no-dev

COPY src ./src

CMD ["uvicorn", "src.normal_os.dashboard.app:app", "--host", "0.0.0.0", "--port", "8000"]