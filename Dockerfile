FROM python:3.14.8-slim-trixie@sha256:fbecd461fc72d21b2143c6eaba25143738079154a6d0ea3da3aec724f50eed4a

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
