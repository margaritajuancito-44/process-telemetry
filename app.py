from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, ValidationError, post_load
from sqlalchemy.dialects.postgresql import JSONB
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Configuración de base de datos: por defecto SQLite pero se puede cambiar con DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///telemetry.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# API key simple (para producción usar OAuth/STS/JWT/Mutual TLS, etc.)
API_KEY = os.getenv("API_KEY", "changeme")

db = SQLAlchemy(app)


class Telemetry(db.Model):
    __tablename__ = "telemetry"
    id = db.Column(db.Integer, primary_key=True)
    sat_id = db.Column(db.String(128), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    alt = db.Column(db.Float, nullable=True)
    vx = db.Column(db.Float, nullable=True)
    vy = db.Column(db.Float, nullable=True)
    vz = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(128), nullable=True)
    metrics = db.Column(JSONB().with_variant(db.JSON, "sqlite"), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "sat_id": self.sat_id,
            "timestamp": self.timestamp.isoformat(),
            "position": {"lat": self.lat, "lon": self.lon, "alt": self.alt},
            "velocity": {"vx": self.vx, "vy": self.vy, "vz": self.vz},
            "status": self.status,
            "metrics": self.metrics,
        }


# Schemas de validación con marshmallow
class PositionSchema(Schema):
    lat = fields.Float(required=True)
    lon = fields.Float(required=True)
    alt = fields.Float(required=False, allow_none=True)


class VelocitySchema(Schema):
    vx = fields.Float(required=False, allow_none=True)
    vy = fields.Float(required=False, allow_none=True)
    vz = fields.Float(required=False, allow_none=True)


class TelemetrySchema(Schema):
    sat_id = fields.Str(required=True)
    timestamp = fields.DateTime(required=True)
    position = fields.Nested(PositionSchema, required=True)
    velocity = fields.Nested(VelocitySchema, required=False)
    status = fields.Str(required=False, allow_none=True)
    metrics = fields.Dict(required=False, allow_none=True)

    @post_load
    def make_dict(self, data, **kwargs):
        # Aplana para crear el modelo fácilmente
        pos = data.pop("position", {})
        vel = data.pop("velocity", {})
        data_out = {
            "sat_id": data.get("sat_id"),
            "timestamp": data.get("timestamp"),
            "lat": pos.get("lat"),
            "lon": pos.get("lon"),
            "alt": pos.get("alt"),
            "vx": vel.get("vx"),
            "vy": vel.get("vy"),
            "vz": vel.get("vz"),
            "status": data.get("status"),
            "metrics": data.get("metrics"),
        }
        return data_out


telemetry_schema = TelemetrySchema()


# Middleware simple de autenticación por header
def require_api_key():
    header = request.headers.get("X-API-KEY", "")
    if header != API_KEY:
        abort(401, description="Unauthorized")


@app.route("/telemetry", methods=["POST"])
def receive_telemetry():
    require_api_key()
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400
    payload = request.get_json()
    try:
        validated = telemetry_schema.load(payload)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    t = Telemetry(
        sat_id=validated["sat_id"],
        timestamp=validated["timestamp"],
        lat=validated["lat"],
        lon=validated["lon"],
        alt=validated.get("alt"),
        vx=validated.get("vx"),
        vy=validated.get("vy"),
        vz=validated.get("vz"),
        status=validated.get("status"),
        metrics=validated.get("metrics"),
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({"id": t.id}), 201


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "db": ("ok" if db.engine else "unknown")}), 200


@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": str(e)}), 401


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Crea tablas si no existen (para desarrollo). En producción usar migraciones.
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
