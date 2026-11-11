FROM python:3.12-slim

# git: las métricas locales leen la historia del clon (git log, ls-tree, blame)
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# los clones montados desde el host tienen otro dueño
RUN git config --system --add safe.directory '*'

# Todo lo que genera la herramienta (proyecto.json, datos/ y salidas/) vive en /app/trabajo, montado
# desde el host, así cada `docker compose run` encuentra lo que dejó el anterior.
# git no pide usuario y contraseña: un repo inexistente (como la wiki de un proyecto que no la usa)
# falla en vez de dejar la corrida esperando en la terminal.
ENV GIT_TERMINAL_PROMPT=0 \
    TRES_P_PROYECTO=/app/trabajo/proyecto.json \
    TRES_P_DATOS=/app/trabajo/datos \
    TRES_P_SALIDAS=/app/trabajo/salidas
RUN mkdir -p /app/trabajo

ENTRYPOINT ["python3", "tres_p.py"]
CMD ["--help"]
