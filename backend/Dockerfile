FROM python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
    EVIDENCE_DATA_DIR=/data/evidence \
    REFERENCE_DATA_DIR=/app/references \
    API_MAX_REQUEST_BODY_BYTES=12582912 \
    API_MAX_CSV_UPLOAD_BYTES=2097152 \
    API_MAX_REFERENCE_UPLOAD_BYTES=10485760 \
    BARCODE_SEARCH_TIMEOUT_SECONDS=30

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends vsearch ncbi-blast+ \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.lock ./requirements.lock
RUN pip install --no-cache-dir --require-hashes -r requirements.lock

RUN groupadd --system --gid 10001 ecogenesis \
    && useradd --system --uid 10001 --gid ecogenesis --home-dir /app --shell /usr/sbin/nologin ecogenesis \
    && mkdir -p /data/evidence /app/data \
    && chown -R ecogenesis:ecogenesis /data/evidence /app

COPY --chown=ecogenesis:ecogenesis backend/app ./app
COPY --chown=ecogenesis:ecogenesis backend/fixtures ./fixtures
COPY --chown=ecogenesis:ecogenesis references ./references
COPY --chown=ecogenesis:ecogenesis reports/competition-100-sequences ./reports/competition-100-sequences
COPY --chown=ecogenesis:ecogenesis reports/adversarial-100-sequences ./reports/adversarial-100-sequences

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--limit-concurrency", "32", "--timeout-keep-alive", "5", "--no-server-header"]
