# Ticketing System

An AI-powered support ticketing system that ingests ticket files, enriches them with an LLM (Llama 3.2 via Ollama), and exposes a React dashboard for managing tickets.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────────────┐
│   UI         │────▶│   API        │────▶│   PostgreSQL       │
│ React/Vite  │     │  FastAPI     │     │  (tickets, users)  │
│  :3000      │     │   :8000      │     └────────────────────┘
└─────────────┘     └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │    Redis     │
                    │  (queue +    │
                    │   cache)     │
                    └──────▲───────┘
                           │
              ┌────────────┴────────────┐
              │                         │
   ┌──────────┴──────────┐  ┌──────────┴──────────┐
   │  live_ingest_worker  │  │    enrich_worker     │
   │  Polls /data/tickets │  │  Reads Redis queue   │
   │  & writes to Postgres│  │  Calls Ollama (LLM)  │
   └─────────────────────┘  └──────────────────────┘
                                        │
                               ┌────────▼────────┐
                               │  Ollama          │
                               │  llama3.2:8b     │
                               │  (host machine)  │
                               └─────────────────┘
```

### Services

| Service | Description | Port |
|---|---|---|
| `ui` | React + Vite frontend (served by Nginx) | 3000 |
| `api` | FastAPI REST backend | 8000 |
| `postgres` | PostgreSQL database | 5432 |
| `redis` | Queue (enrichment jobs) + response cache | 6379 |
| `live_ingest_worker` | Watches `./data/tickets/` for new `.txt` files and inserts them into Postgres | — |
| `enrich_worker` | Dequeues ticket IDs from Redis and enriches them via Ollama | — |
| `init_db` | One-shot service that runs DB migrations on startup | — |

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) (v3.8+)
- [Ollama](https://ollama.com/download) installed and running on your **host machine**
- The `llama3.2:8b` model pulled into Ollama

---

## Setting Up Ollama and Llama 3.2

The `enrich_worker` communicates with Ollama over `http://host.docker.internal:11434`, which resolves to the host machine from inside the Docker containers (works out-of-the-box on Docker Desktop for Mac/Windows; Linux users see the note below).

### 1. Install Ollama

Download and install from [https://ollama.com/download](https://ollama.com/download), or via the install script:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull the Llama 3.2 model

```bash
ollama pull llama3.2:8b
```

This downloads the ~5 GB quantised model. Once complete, verify it is available:

```bash
ollama list
# Should show: llama3.2:8b
```

### 3. Start the Ollama server

Ollama starts automatically as a background service after installation. If it is not running, start it manually:

```bash
ollama serve
```

The server listens on `http://localhost:11434` by default.

> **Linux note:** `host.docker.internal` is not automatically resolved on Linux.
> Add the following to each worker service in `docker-compose.yaml`:
> ```yaml
> extra_hosts:
>   - "host.docker.internal:host-gateway"
> ```

---

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd ticketing-sys
```

### 2. Create the ticket data directory

```bash
mkdir -p data/tickets
```

### 3. Start all services

```bash
docker compose up --build
```

Docker Compose will:
1. Start PostgreSQL and Redis.
2. Run `init_db` to create the schema and seed employees.
3. Start the `api`, `live_ingest_worker`, `enrich_worker`, and `ui` services.

### 4. Open the dashboard

Navigate to [http://localhost:3000](http://localhost:3000).

### 5. Add tickets

Drop `.txt` ticket files into `./data/tickets/`. The `live_ingest_worker` polls this directory every 5 seconds and automatically ingests new files.

---

## Ticket File Format

Ticket files are plain text with an optional front-matter block:

```
Tags: billing, urgent, mobile
---
MOBILE: Unable to process payment

I tried to complete my purchase three times and each time the payment fails at the final step.
Order ID: 12345. Using iOS 17 on iPhone 15.
```

- **Tags line** (optional): comma-separated tags before the `---` separator.
- **Body**: everything after `---`. If there is no `---`, the entire file is treated as the body.
- The first line of the body is used as the raw subject; a better subject line is generated by the LLM.
- Tickets with the `auto-closed` tag are set to `closed` status immediately on ingest.
- Bodies that start with `MOBILE:` are classified as `source = Mobile`; all others as `Webapp`.

---

## AI Enrichment

After a ticket is ingested it is queued in Redis and processed by the `enrich_worker`, which calls Ollama for the following:

| Field | Description |
|---|---|
| `ai_subject` | Concise subject line (≤ 10 words, same language as ticket) |
| `language` | Detected language of the ticket body |
| `suggested_response` | Draft customer-facing reply (skipped for closed tickets) |
| `troubleshooting_steps` | Numbered internal steps for the assigned agent (≤ 5 steps) |
| `assigned_to` | Employee with the fewest currently assigned tickets (round-robin) |
| `source` | `Mobile` or `Webapp` based on body content |

Tickets with no meaningful content (e.g., only punctuation) are automatically closed with `ai_subject = "Auto-Closed: No content"` and a generic follow-up response.

---

## API Reference

Base URL: `http://localhost:8000`

### Health

```
GET /health
```
Returns `{"status": "ok"}`.

### Employees

```
GET /employees
```
Returns the list of employees available for ticket assignment.

### Tickets

```
GET /tickets
```
Returns all tickets. Results are cached in Redis for 60 seconds.

```
PATCH /tickets/{ticket_id}
```
Updates a ticket. Accepted fields:

| Field | Type | Values |
|---|---|---|
| `status` | string | `new`, `open`, `in-progress`, `closed` |
| `assigned_to` | string | Employee name |

Example request body:
```json
{ "status": "in-progress", "assigned_to": "Kyle" }
```

### Ticket Messages

```
GET /tickets/{ticket_id}/messages
```
Returns the message thread for a ticket, ordered by `created_at` ascending.

```
POST /tickets/{ticket_id}/messages
```
Adds a message to the thread.

Example request body:
```json
{ "author": "Kyle", "body": "Looking into this now." }
```

---

## Project Structure

```
ticketing-sys/
├── api/                    # FastAPI REST backend
│   ├── main.py             # App entry point & route definitions
│   ├── models.py           # Pydantic schemas
│   ├── db.py               # PostgreSQL connection helper
│   ├── cache.py            # Redis client & cache TTL
│   ├── requirements.txt
│   └── Dockerfile
│
├── worker/                 # Background workers
│   ├── live_ingest_worker.py  # Polls /data/tickets for new files
│   ├── enrich_worker.py       # Dequeues & enriches tickets via LLM
│   ├── ingest.py              # Ticket file parser & DB insert
│   ├── ai_enrichment.py       # LLM prompt logic
│   ├── ollama_client.py       # HTTP client for Ollama API
│   ├── redis_queue.py         # Push/pop helpers for Redis queue
│   ├── db.py                  # PostgreSQL connection helper
│   ├── init_db.py             # Schema creation & employee seeding
│   ├── wait-for-it.sh         # Service readiness probe
│   ├── requirements.txt
│   └── Dockerfile
│
├── ui/                     # React + TypeScript frontend
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/     # UI components
│   │   └── lib/            # API client utilities
│   ├── package.json
│   ├── vite.config.ts
│   ├── nginx.conf
│   └── Dockerfile
│
├── data/
│   └── tickets/            # Drop ticket .txt files here
│
└── docker-compose.yaml
```

---

## Configuration

All configuration is handled via environment variables. The defaults used in `docker-compose.yaml` are:

| Variable | Default | Used by |
|---|---|---|
| `POSTGRES_USER` | `studyflash` | `postgres`, `api`, `worker` |
| `POSTGRES_PASSWORD` | `studyFlash123!` | `postgres`, `api`, `worker` |
| `POSTGRES_DB` | `studyflash` | `postgres`, `api`, `worker` |
| `OLLAMA_URL` | `http://host.docker.internal:11434/api/chat` | `worker/ollama_client.py` |

To change the Ollama endpoint, update `OLLAMA_URL` in `worker/ollama_client.py` or pass it as an environment variable in `docker-compose.yaml`.

---

## Stopping the Application

```bash
docker compose down
```

To also remove persisted volumes (database data):

```bash
docker compose down -v
```
