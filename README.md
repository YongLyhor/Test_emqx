# IoT Platform API

A production-ready IoT platform for collecting, processing, and storing sensor data from smart meters (water, electricity, gas, cooling) using **EMQX** (MQTT broker), **FastAPI** (backend), and **TimescaleDB** (time-series storage).

> For a deep dive into the MQTT ingestion pipeline (validation layers, topics, payloads), see [docs/MQTT_DATA_FLOW.md](docs/MQTT_DATA_FLOW.md).

## Architecture

```
MQTTX / Device ──publish──▶ EMQX Broker ──subscribe──▶ FastAPI (MQTT client) ──▶ TimescaleDB
                                │
                         Dashboard :18083
```

The backend runs its own MQTT client that subscribes to EMQX — there is no HTTP hop between the broker and the API for ingesting sensor data.

## Tech Stack

| Layer       | Technology                   |
|-------------|-------------------------------|
| MQTT Broker | EMQX                          |
| MQTT Client | paho-mqtt                     |
| Backend     | FastAPI + Uvicorn              |
| ORM         | SQLAlchemy                    |
| Migrations  | Alembic                       |
| Database    | TimescaleDB (PostgreSQL 16)   |
| Validation  | Pydantic / pydantic-settings  |
| Admin UI    | pgAdmin 4 (optional)          |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Compose)
- Python 3.11+ (only needed if running the API outside Docker)
- Git

## Project Structure

```
app/
├── api/routes/       # FastAPI routers (health, sensors, devices, alerts, device_types)
├── core/             # Settings, database engine, logging, exceptions
├── models/           # SQLAlchemy models
├── mqtt/             # MQTT client, message handlers, publisher, topics
├── repository/       # Data access layer
├── schemas/           # Pydantic request/response schemas
└── service/           # Business logic (validation, alerts, anomaly detection)
migration/versions/    # Alembic migrations (schema + seed data)
docker-compose.yml     # emqx + timescaledb + pgadmin + api
```

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd Test_emqx
```

### 2. Create the environment file

Create a `.env` file in the project root (this file is git-ignored):

```env
# Database
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_DB=iot_platform
DATABASE_URL=postgresql://admin:admin123@localhost:5432/iot_platform
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
DATABASE_ECHO=false

# MQTT
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID=iot_api_client
MQTT_KEEPALIVE=60

# API
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
SECRET_KEY=change-me
DEBUG=true
API_VERSION=v1

# CORS
ALLOWED_ORIGINS=["*"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Security (reserved for future JWT auth)
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# TimescaleDB
TIMESCALEDB_TELEMETRY=off
```

> Replace `SECRET_KEY` and any credentials with your own values before deploying anywhere beyond local development.

### 3. Run with Docker (recommended)

```bash
docker compose up -d --build
```

This starts EMQX, TimescaleDB, pgAdmin, and the API. The `api` container automatically runs `alembic upgrade head` (creating tables and seeding sample device types/devices) before starting Uvicorn.

| Service     | URL / Port                                          |
|-------------|------------------------------------------------------|
| API         | http://localhost:8000                                |
| Swagger UI  | http://localhost:8000/docs                           |
| EMQX Dashboard | http://localhost:18083 (`admin` / `public`)        |
| TimescaleDB | `localhost:5432` (`admin` / `admin123`)               |
| pgAdmin     | http://localhost:5055 (`admin@iot.com` / `admin123`) |

### 4. Run locally without Docker (optional)

Keep EMQX and TimescaleDB in Docker, run the API on the host:

```bash
# Start broker + database only
docker compose up -d emqx timescaledb

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows
# source venv/bin/activate       # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Apply migrations
alembic upgrade head

# Start the API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

When running on the host, `DATABASE_URL` and `MQTT_BROKER_HOST` in `.env` should point to `localhost` (as shown above). The Docker Compose file overrides these to `timescaledb`/`emqx` for the containerized API.

## Verifying the Setup

1. Check health: `GET http://localhost:8000/health` → should report `"mqtt": { "status": "connected" }`.
2. Publish a test message with an MQTT client (e.g. [MQTTX](https://mqttx.app/)):
   - Topic: `sensor/water/WTR-001-BLDG-A/data`
   - Payload: `{"value": 1234.56, "unit": "m3", "quality": 100}`
3. Confirm it was stored: `GET http://localhost:8000/api/v1/sensors/readings?device_id=WTR-001-BLDG-A`

See [docs/MQTT_DATA_FLOW.md](docs/MQTT_DATA_FLOW.md) for the full list of topics, payload schema, and API endpoints.

## Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration
alembic revision -m "description"

# Rollback one revision
alembic downgrade -1
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `could not translate host name "timescaledb"` | Running the API on the host but `.env` still points at the Docker hostname — use `localhost`. |
| MQTT `Failed to connect` on host | Ensure `MQTT_BROKER_HOST=localhost` and the EMQX container is `Up` (`docker ps`). |
| EMQX dashboard unreachable | Visit http://localhost:18083, login `admin` / `public`. |
| `sensor_reading` insert fails with `DeviceNotFoundError` | Register the device first via `POST /api/v1/devices/`, or use a seeded device ID. |

More troubleshooting scenarios are documented in [docs/MQTT_DATA_FLOW.md](docs/MQTT_DATA_FLOW.md#troubleshooting).

## License

MIT
