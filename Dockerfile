FROM python:3.14.9-slim-trixie@sha256:35caba83af2fe6da9a5d922f9b0156f21d1246a48278c58a08bd253303ba42e8

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
