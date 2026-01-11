FROM python:3.11-slim

WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Exponer puerto
EXPOSE 5000

# Comando para correr la app
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000"]
