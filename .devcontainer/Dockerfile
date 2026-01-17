FROM python:3.10-slim

WORKDIR /workspace
COPY . /workspace

RUN pip install --upgrade pip

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
