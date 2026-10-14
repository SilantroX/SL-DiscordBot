# Dockerfile para SilantroLabs Bot
FROM python:3.13-slim

# Evitar generación de archivos .pyc y habilitar salida sin búfer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente del proyecto
COPY . .

# Crear directorio de datos persistentes
RUN mkdir -p /app/data

# Comando de arranque del bot
CMD ["python", "main.py"]
