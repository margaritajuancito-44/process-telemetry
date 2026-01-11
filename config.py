import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///telemetry.db")
API_KEY = os.getenv("API_KEY", "changeme")
PORT = int(os.getenv("PORT", 5000))