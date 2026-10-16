FROM python:3.14.4-slim-trixie

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
CMD ["python", "-m", "centinela", "--bucle"]
