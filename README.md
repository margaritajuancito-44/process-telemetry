# API Flask para recibir telemetría satelital

Esta API mínima en Flask recibe telemetría satelital en JSON, la valida y la persiste en base de datos.

Endpoints principales:
- `POST /telemetry` — Recibe un objeto JSON con la telemetría.
  - Header obligatorio: `X-API-KEY: <tu_api_key>`
- `GET /health` — Healthcheck simple.

Ejemplo de payload (JSON):
```json
{
  "sat_id": "SAT-1234",
  "timestamp": "2026-01-11T12:00:00Z",
  "position": { "lat": -12.3456, "lon": 98.7654, "alt": 550.0 },
  "velocity": { "vx": 0.12, "vy": -7.45, "vz": 0.01 },
  "status": "nominal",
  "metrics": { "battery": 87.5, "temp": -5.2 }
}
```

Ejemplo curl:
```bash
curl -X POST http://localhost:5000/telemetry \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: super-secret-key" \
  -d '@payload.json'
```

Instalación rápida (virtualenv):
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# editar .env si es necesario
python app.py
```

Notas y mejoras recomendadas:
- Para producción: usar una base de datos gestionada (Postgres), habilitar TLS y usar autenticación fuerte (JWT/OAuth2/STS).
- Añadir migraciones: usar Flask-Migrate (Alembic).
- Procesamiento asíncrono (Celery/RQ) para validación/ingesta en alta tasa de mensajes.
- Añadir métricas (Prometheus) y logging estructurado.
- Rate limiting / API gateway si habrá muchos dispositivos/streams.
