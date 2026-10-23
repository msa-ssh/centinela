FROM python:3.14.4-slim-trixie@sha256:2ca02f32b4d9d893863367ce07ec1972819f476dd38d8612f2a9cb6a41cbb727

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CENTINELA_ESTADO=/datos/estado.json \
    CENTINELA_HISTORIAL=/datos/historial.db

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 centinela \
    && mkdir /datos \
    && chown centinela:centinela /datos

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY centinela/ centinela/

USER centinela
HEALTHCHECK --interval=1m --timeout=30s --start-period=2m --retries=3 \
    CMD ["python", "-m", "centinela", "--salud"]
CMD ["python", "-m", "centinela", "--bucle"]
