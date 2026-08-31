# IoT Platform API — Documentation

A production-ready IoT platform for collecting, processing, and storing sensor data from smart meters (water, electricity, gas, cooling) using **EMQX** (MQTT broker), **FastAPI** (backend), and **TimescaleDB** (time-series storage).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Getting Started](#getting-started)
   - [Option A: Docker (recommended)](#option-a-docker-recommended)
   - [Option B: Run locally on the host](#option-b-run-locally-on-the-host)
5. [MQTT Data Flow](#mqtt-data-flow)
   - [Step 1: MQTTX connects to EMQX](#step-1-mqttx-connects-to-emqx)
   - [Step 2: EMQX relays to the Backend](#step-2-emqx-relays-to-the-backend)
   - [Step 3: Backend validation logic](#step-3-backend-validation-logic)
   - [Step 4: Store to TimescaleDB](#step-4-store-to-timescaledb)
6. [MQTT Topics & Payloads](#mqtt-topics--payloads)
7. [Seeded Data](#seeded-data)
8. [API Endpoints](#api-endpoints)
9. [Verification & Testing](#verification--testing)
10. [Configuration](#configuration)
11. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
                    ┌──────────────────────────────────────────────────────────┐
                    │                      EMQX Broker (:1883)                │
                    │              (dashboard: http://localhost:18083)        │
                    └──────────────▲───────────────────────────▲──────────────┘
                                   │                           │
              publish             │                           │  subscribe
              topic:             │                           │  sensor/+/+/data
        sensor/{type}/{id}/data  │                           │
                                   │                           │
              ┌────────────┐       │          ┌───────────────▼──────────────────┐
              │   MQTTX    │       │          │       Backend API (FastAPI)     │
              │  (client)  │       │          │  app/mqtt/  → MQTT subscriber    │
              └────────────┘       │          │  app/service → validation logic  │
                                   │          └───────────────┬──────────────────┘
                                   │                           │
                                   │                           │  insert
                                   │          ┌───────────────▼──────────────────┐
                                   │          │        TimescaleDB (:5432)       │
                                   │          │     table: sensor_readings       │
                                   │          └──────────────────────────────────┘
```

The flow has **no HTTP hop** between EMQX and the backend — the backend runs its **own MQTT client** that subscribes to EMQX and receives messages directly.

---

## Tech Stack

| Layer        | Technology                          | Version     |
|--------------|-------------------------------------|-------------|
| MQTT Broker  | EMQX                                | latest      |
| MQTT Client  | paho-mqtt                           | 2.1.0       |
| Backend      | FastAPI                             | 0.104.1     |
| ORM          | SQLAlchemy                          | 2.0.23      |
| Migrations   | Alembic                             | 1.12.1      |
| Database     | TimescaleDB (PostgreSQL 16)         | latest-pg16 |
| Validation   | Pydantic / pydantic-settings        | 2.5.0       |
| ASGI Server  | Uvicorn                             | 0.24.0      |
| Admin UI     | pgAdmin 4 (optional)                | latest      |

---

## Project Structure

```
Test_emqx/
├── app/
│   ├── api/
│   │   └── routes/           # FastAPI routers: health, sensors, devices, alerts, device_types
│   ├── core/
│   │   ├── config.py         # Settings via pydantic-settings (.env)
│   │   ├── database.py       # SQLAlchemy engine + SessionLocal
│   │   ├── logging.py        # Console + rotating file logging
│   │   └── exceptions.py     # Custom exceptions
│   ├── models/               # SQLAlchemy models (sensor_reading, device, alert, ...)
│   ├── mqtt/
│   │   ├── client.py         # MQTT client (connect, subscribe, publish, dispatch)
│   │   ├── handler.py        # Message handlers (data/status/config/alert)
│   │   ├── initializer.py    # Wires client + handlers + DB session
│   │   ├── publisher.py      # Publish commands / config / status requests
│   │   └── topics.py         # Topic definitions & parsing
│   ├── repository/           # DB access layer
│   ├── schemas/              # Pydantic request/response schemas
│   └── service/              # Business logic (validation, alerts, anomalies)
├── migration/versions/       # Alembic migrations (001–007, incl. seed data)
├── docker-compose.yml        # emqx + timescaledb + pgadmin + api
├── Dockerfile
├── requirements.txt
└── .env
```

---

## Getting Started

### Option A: Docker (recommended)

Prerequisites: Docker Desktop with the compose plugin.

```bash
# Build and start all services (api runs alembic migrations on startup)
docker compose up -d --build
```

| Service      | Container   | URL / Port                        |
|--------------|-------------|-----------------------------------|
| Backend API  | `iot_api`   | http://localhost:8000             |
| Swagger UI   |             | http://localhost:8000/docs        |
| EMQX         | `emqx_broker` | MQTT :1883, Dashboard :18083    |
| TimescaleDB  | `timescaledb`| :5432 (admin/admin123)           |
| pgAdmin      | `pgadmin`   | http://localhost:5055 (admin@iot.com / admin123) |

> The `api` container runs `alembic upgrade head` before starting, which creates
> the tables **and** seeds device types + sample devices.

### Option B: Run locally on the host

Keep EMQX and TimescaleDB in Docker, run the API with the local venv:

```bash
# 1. Start broker + database only
docker compose up -d emqx timescaledb

# 2. Install the venv (first time only)
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Start the API (uses .env → localhost:5432 / localhost:1883)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`.env` points the host build at `localhost`, while the Docker container overrides
these via `docker-compose.yml` environment variables (`timescaledb` / `emqx`).

---

## MQTT Data Flow

### Step 1: MQTTX connects to EMQX

1. Open **MQTTX**, create a new connection:
   - Name: e.g. `Test Water Meter`
   - Protocol: MQTT
   - Host: `localhost`, Port: `1883`
   - Username / Password: empty (EMQX allows anonymous connections)
   - Click **Connect** (status shows `Connected`).

2. To publish a reading, set the **topic** and **payload** (see
   [MQTT Topics & Payloads](#mqtt-topics--payloads)) and click **Send**.

> MQTTX never connects to TimescaleDB — it only publishes to EMQX. Everything
> after that is EMQX → Backend → DB.

### Step 2: EMQX relays to the Backend

The backend acts as an MQTT **subscriber**, not an HTTP receiver:

- Startup triggers MQTT init in a background thread — `app/main.py:59`
- `app/mqtt/initializer.py:29` builds the client + handler and calls `connect()`
- `app/mqtt/client.py:39` connects to EMQX and subscribes to:
  - `sensor/+/+/data`
  - `sensor/+/+/status`

Verify the link is alive:

```bash
GET http://localhost:8000/health
# → "mqtt": { "status": "connected" }
```

### Step 3: Backend validation logic

Before anything reaches the database, each message passes **4 layers of checks**:

| Layer | Where | What it checks |
|-------|-------|----------------|
| 1. Parsing | `app/mqtt/client.py:117` `_on_message` | Valid JSON? Topic parses to sensor_type/device_id/message_type? |
| 2. Required fields | `app/mqtt/handler.py:28` `handle_data_message` | `value` present? `unit` non-empty? (else message dropped) |
| 3. Business rules | `app/service/sensor_reading_service.py:27` `validate_create` | Device exists? Valid sensor_type? value within min/max? quality 0–100? |
| 4. Create + side effects | `sensor_reading_service.py:56` `process_reading` | Insert row; threshold alert check; Z-score anomaly check |

Only messages that pass all layers reach the database. Failures are logged and the
message is silently dropped (no crash).

### Step 4: Store to TimescaleDB

- Connection: `app/core/database.py` via `DATABASE_URL`
- Table: `sensor_readings` (`app/models/sensor_reading.py`)
  - Composite primary key `(time, id)` — time-series friendly
  - `value NUMERIC(15,6)`, `unit VARCHAR(20)`, `metadata JSONB`

---

## MQTT Topics & Payloads

### Topic patterns

| Purpose | Topic |
|---------|-------|
| Sensor data | `sensor/{sensor_type}/{device_id}/data` |
| Status      | `sensor/{sensor_type}/{device_id}/status` |
| Config      | `sensor/{sensor_type}/{device_id}/config` |
| Alert       | `sensor/{sensor_type}/{device_id}/alert` |

`sensor_type` must be one of: `water`, `electricity`, `gas`, `cooling`.

### Data payload (JSON)

```json
{
  "value": 1234.56,
  "unit": "m3",
  "time": "2026-08-31T10:30:00Z",
  "quality": 100,
  "metadata": { "source": "MQTTX", "reading_type": "cumulative" }
}
```

| Field      | Required | Type          | Notes                              |
|------------|----------|---------------|------------------------------------|
| `value`    | ✅        | number        | Stored as NUMERIC(15,6)             |
| `unit`     | ✅        | string        | e.g. m3, kWh, kW, m³/h             |
| `time`     | ❌        | ISO datetime  | Defaults to `now()`                |
| `quality`  | ❌        | int 0–100     | Defaults to 100                    |
| `metadata` | ❌        | object        | Arbitrary JSON, stored as JSONB    |

---

## Seeded Data

Migration `007_seed_data.py` inserts device types and sample devices:

| sensor_type | device_id       | display_name                        | default_unit |
|-------------|-----------------|-------------------------------------|--------------|
| water       | `WTR-001-BLDG-A`  | Main Water Meter - Building A       | m³           |
| electricity | `ELC-003-FLOOR-2` | Smart Meter - Tower A Floor 2       | kWh          |
| gas         | `GAS-002-KITCHEN` | Gas Meter - Main Kitchen            | m³/h         |
| cooling     | `CLG-005-CHILLER` | Chiller Cooling Meter - Plant Room  | kW           |

---

## API Endpoints

Base URL: `http://localhost:8000` · Interactive docs: `/docs`

| Method | Endpoint                              | Description                      |
|--------|---------------------------------------|----------------------------------|
| GET    | `/health`                             | DB + MQTT status                 |
| GET    | `/`                                   | API metadata                     |
| GET    | `/info`                               | Feature/dependency info          |
| POST   | `/api/v1/devices/`                    | Create device                    |
| GET    | `/api/v1/devices/`                    | List devices (filters)           |
| GET    | `/api/v1/devices/{device_id}`         | Get device                       |
| PUT    | `/api/v1/devices/{device_id}`         | Update device                    |
| PATCH  | `/api/v1/devices/{device_id}/status`  | Update status                    |
| DELETE | `/api/v1/devices/{device_id}`         | Delete device                    |
| POST   | `/api/v1/sensors/readings`            | Create reading (HTTP alternative)|
| POST   | `/api/v1/sensors/readings/batch`      | Create readings in batch         |
| GET    | `/api/v1/sensors/readings`            | Query readings (filters)         |
| GET    | `/api/v1/sensors/readings/latest`     | Latest reading per device        |
| GET    | `/api/v1/sensors/readings/{id}/latest`| Latest reading for a device      |
| GET    | `/api/v1/sensors/readings/aggregated` | Time-bucket aggregation          |
| GET    | `/api/v1/sensors/readings/statistics` | Stats for a sensor type          |
| GET    | `/api/v1/sensors/readings/anomalies`  | Z-score anomaly detection        |
| CRUD   | `/api/v1/device-types/`               | Manage device types              |
| CRUD   | `/api/v1/alerts/`                     | Manage alerts                    |

---

## Verification & Testing

### 1. Publish with MQTTX

```text
Topic:   sensor/water/WTR-001-BLDG-A/data
Payload: {"value": 1234.56, "unit": "m3", "quality": 100}
```

### 2. Watch the backend react

```bash
docker logs iot_api --tail 20
# → Processing sensor data: WTR-001-BLDG-A
# → Processed reading for device WTR-001-BLDG-A: {'success': True, ...}
```

### 3. Confirm the row in TimescaleDB

```bash
# Via API
GET http://localhost:8000/api/v1/sensors/readings?device_id=WTR-001-BLDG-A

# Directly
docker exec timescaledb psql -U admin -d iot_platform \
  -c "SELECT * FROM sensor_readings ORDER BY time DESC;"
```

### 4. Test the validation gates (negative tests)

| Publish to | Payload | Expected result |
|------------|---------|-----------------|
| `sensor/water/WTR-001-BLDG-A/data` | `{"unit": "m3"}` | Dropped — missing `value` (Layer 2) |
| `sensor/water/NOT-A-DEVICE/data`  | `{"value": 1, "unit": "m3"}` | Dropped — device not found (Layer 3) |
| `sensor/water/WTR-001-BLDG-A/data` | `{"value": -5, "unit": "m3"}` | Dropped — below min_value (Layer 3) |

Check the reason in `docker logs iot_api`.

---

## Configuration

All settings live in `.env` (read by `app/core/config.py`).

| Variable              | Default                                        | Notes                        |
|-----------------------|------------------------------------------------|------------------------------|
| `DATABASE_URL`        | `postgresql://admin:admin123@localhost:5432/iot_platform` | `timescaledb` host inside Docker |
| `DATABASE_POOL_SIZE`  | 20                                             | SQLAlchemy pool size         |
| `MQTT_BROKER_HOST`     | `localhost`                                    | `emqx` inside Docker         |
| `MQTT_BROKER_PORT`     | 1883                                           |                              |
| `MQTT_CLIENT_ID`       | `iot_api_client`                               |                              |
| `API_PORT`             | 8000                                           |                              |
| `ALLOWED_ORIGINS`      | `["*"]` (JSON array)                           |                              |
| `LOG_FILE`             | `logs/app.log`                                 | Rotating, UTF-8              |
| `JWT_ALGORITHM`        | HS256                                          | Reserved for future auth     |

---

## Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| `could not translate host name "timescaledb"` | Running the API on the host but `.env` still points at the Docker hostname. Use `localhost`. |
| MQTT `Failed to connect` on host | `.env` `MQTT_BROKER_HOST` must be `localhost`; verify EMQX container is `Up` (`docker ps`). |
| `module 'paho.mqtt.client' has no attribute 'CallbackAPIVersion'` | paho-mqtt < 2.x installed. `pip install paho-mqtt==2.1.0`. |
| Duplicate rows in `sensor_readings` | Fixed in `app/mqtt/client.py` — the `data` handler ran twice. Rebuild/restart the container. |
| `GET /api/v1/devices` returns 500 | Services used to return raw ORM objects; serializers added in `device_service.py` / `sensor_reading_service.py`. |
| `UnicodeEncodeError: 'charmap'` on Windows | File handler now opens as UTF-8; console handler uses `errors="replace"`. For real emoji, run `chcp 65001` or set `PYTHONIOENCODING=utf-8`. |
| EMQX dashboard unreachable | http://localhost:18083, login `admin` / `public`. |
| `sensor_reading` insert fails with `DeviceNotFoundError` | The `device_id` in your topic isn't registered. `POST /api/v1/devices/` first, or use a seeded ID. |