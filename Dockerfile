# Imagem do demo publico. Instala o pacote (que puxa earthsolver do git) e
# sobe o app NiceGUI. `git` e necessario para a dependencia git+https.
FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

# PORT: porta do servidor | EARTHGUI_HEADLESS: nao tenta abrir navegador
# EARTHGUI_MAX_SEG: teto de segmentos do solver (0 = ilimitado)
ENV PORT=8080 \
    EARTHGUI_HEADLESS=1 \
    EARTHGUI_MAX_SEG=2000

EXPOSE 8080
CMD ["python", "-m", "gui.main"]
