# DistriCloud

**Components for a Decentralized Cloud - Bachelor’s Thesis Project**

## Overview

DistriCloud is a distributed system for orchestrating and executing computational tasks across multiple nodes using a resource- and trust-aware scheduling algorithm.

It provides an extensible, modular architecture featuring:

- **Hub Component:** Central orchestrator and API, built with Django.
- **Node Component:** API and agent for executing tasks, built in Python - Flask.
- **Frontend:** Modern web UI for monitoring and control (Vite/React).

**Core Features:**
- Customizable orchestration: FIFO or custom trust/resource-aware algorithms.
- Trust-based result validation with configurable thresholds.
- Node health checking and automatic task validation.
- Real-time updates via Redis pub/sub channels.
- Experiment mode for benchmarking and controlled tests.

---

## Project Structure

```text
licenta_distri_cloud/
│
├── hub_component/            # Central hub (Django)
│   ├── experiments/          # Experiment scripts and configs
│   ├── hub/                  # Django app (core logic)
│   ├── licenta/              # Django project settings
│   ├── celerybeat-schedule   # Celery schedule DB
│   ├── docker-compose.yml    # Docker Compose for hub
│   ├── Dockerfile            # Hub Dockerfile
│   ├── manage.py
│   ├── pytest.ini
│   └── requirements.txt
│
├── node_component/           # Node agent/API
│   ├── frontend/             # Node-related frontend (if any)
│   ├── node/                 # Node API logic
│   ├── docker-compose.yml    # Docker Compose for node
│   └── Dockerfile            # Node Dockerfile
│
├── tests/                    # Shared and integration tests
├── .gitignore
├── docker-compose.yml        # Top-level orchestration
└── README.md                 # (You are here)
```

---

## Requirements

- **Python 3.12**
- **Docker & Docker Compose**
- **PostgreSQL**
- **Redis**

See each component’s `requirements.txt` for Python dependencies.

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd licenta_distri_cloud
```

### 2. Configure Environment

Create a `.env` file or set these variables as needed (defaults are provided in settings):

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

### 3. Build and Run with Docker Compose

```bash
# Run the full system (hub, node, frontend)
docker-compose up --build
```

You may also run components individually:

```bash
cd hub_component
docker-compose up --build

cd ../node_component
docker-compose up --build
```

### 4. Access Services

- **Frontend UI:** [http://localhost:18080](http://localhost:18080)
- **Hub API:** [http://localhost:18000/api](http://localhost:18000/api)
- **Hub Django Admin Interface:** [http://localhost:18000/admin](http://localhost:18000/admin)
- **Node API:** [http://localhost:18001](http://localhost:18001)

---

## Key Configuration (Django, Celery, Orchestration)

- **Database:** PostgreSQL (set in `hub_component/licenta/settings.py`)
- **Task Queue:** Celery + Redis
- **CORS:** Open by default for local dev (`CORS_ALLOW_ALL_ORIGINS = True`)
- **Custom orchestration parameters:**  
  (see `hub_component/licenta/settings.py` for `ORCHESTRATION_MECHANISM`, thresholds, trust parameters)

---

## Development

- **Run tests:**
  ```bash
  pytest
  ```
- **Django admin:**
  ```bash
  python manage.py createsuperuser
  python manage.py runserver
  ```

---

## Experimentation Mode

Set `EXPERIMENT_MODE = True` in Django settings to enable endpoints and views for validation and distributed experiment scenarios.

---

## Credits

Developed by Alexandru Dragos as part of the Bachelor’s thesis _Components for a Decentralized Cloud_.

---
