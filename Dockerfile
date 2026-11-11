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

# Lo que se genera entre pasos (CSV por persona, identidades) vive en /app/trabajo, montado desde
# el host, así cada `docker compose run` encuentra lo que dejó el anterior.
RUN mkdir -p /app/trabajo \
 && for f in persona_agregado_estable_canary.csv persona_detalle_estable.csv metricas_persona.csv persona_duplicados_canon.csv; do \
      ln -sf /app/trabajo/$f /app/$f; done \
 && for f in identidades_git.csv identidades_ambiguas.csv; do ln -sf /app/trabajo/$f /app/db/$f; done

ENTRYPOINT ["python3", "tres_p.py"]
CMD ["--help"]
