FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
    EVIDENCE_DATA_DIR=/data/evidence \
    REFERENCE_DATA_DIR=/app/references

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends vsearch ncbi-blast+ \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/fixtures ./fixtures
RUN mkdir -p ./data
COPY references ./references
COPY reports/competition-100-sequences ./reports/competition-100-sequences
COPY reports/adversarial-100-sequences ./reports/adversarial-100-sequences

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
