import json
from fastapi import FastAPI
from db import get_db_connection
from models import Ticket
from cache import get_redis_client, CACHE_TTL

app = FastAPI()

@app.on_event("startup")
def startup_event():
    print("Starting up the API...")
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id SERIAL PRIMARY KEY,
            external_id TEXT,     -- to prevent duplicates on re-ingest
            subject TEXT,
            body TEXT,
            tags TEXT[],                -- store parsed tags
            status TEXT DEFAULT 'open', -- simple status field (open, closed, pending)
            ai_subject TEXT,            -- future AI-generated subject
            category TEXT,              -- future AI category / tag
            suggested_assignee TEXT,    -- future AI suggested assignee
            source TEXT,                -- mobile or webapp.
            enrichment_done BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT now()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/tickets", response_model=list[Ticket])
def get_tickets():
    try:
        cache = get_redis_client()
        cached = cache.get("tickets")
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tickets;")
    tickets = [dict(t) for t in cur.fetchall()]
    cur.close()
    conn.close()

    try:
        cache = get_redis_client()
        cache.setex("tickets", CACHE_TTL, json.dumps(tickets, default=str))
    except Exception:
        pass

    return tickets