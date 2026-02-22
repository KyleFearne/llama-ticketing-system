import json
from fastapi import FastAPI, HTTPException
from db import get_db_connection
from models import Ticket, Employee, TicketUpdate, TicketMessage, TicketMessageCreate
from cache import get_redis_client, CACHE_TTL

app = FastAPI()

@app.on_event("startup")
def startup_event():
    print("Starting up the API...")
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
    """)

    cur.execute("""
        INSERT INTO employees (name) VALUES ('Kyle'), ('Maria'), ('Lila'), ('Joseph')
        ON CONFLICT (name) DO NOTHING;
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id SERIAL PRIMARY KEY,
            external_id TEXT,     -- to prevent duplicates on re-ingest
            subject TEXT,
            body TEXT,
            tags TEXT[],                -- store parsed tags
            status TEXT DEFAULT 'new',  -- new, in-progress, closed
            ai_subject TEXT,            -- AI-generated subject
            category TEXT,              -- AI category / tag
            source TEXT,                -- Mobile or Webapp
            language TEXT,              -- detected ticket language
            assigned_to INTEGER REFERENCES employees(id) ON DELETE SET NULL,
            suggested_response TEXT,    -- AI suggested response
            enrichment_done BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT now()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ticket_messages (
            id SERIAL PRIMARY KEY,
            ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
            author TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT now()
        );
    """)

    # Migrations for existing databases
    _safe_new_cols = {
        "language": "TEXT",
        "suggested_response": "TEXT",
        "troubleshooting_steps": "TEXT",
    }
    for col, definition in _safe_new_cols.items():
        cur.execute(f"ALTER TABLE tickets ADD COLUMN IF NOT EXISTS {col} {definition};")

    # Migrate assigned_to from TEXT (name) to INTEGER FK referencing employees(id)
    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'tickets' AND column_name = 'assigned_to'
        ) THEN
            ALTER TABLE tickets ADD COLUMN assigned_to INTEGER REFERENCES employees(id) ON DELETE SET NULL;
        ELSIF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'tickets' AND column_name = 'assigned_to' AND data_type = 'text'
        ) THEN
            ALTER TABLE tickets ADD COLUMN assigned_to_id INTEGER;
            UPDATE tickets t SET assigned_to_id = e.id FROM employees e WHERE t.assigned_to = e.name;
            -- Warn about tickets whose assigned_to name had no matching employee
            IF EXISTS (SELECT 1 FROM tickets WHERE assigned_to IS NOT NULL AND assigned_to_id IS NULL) THEN
                RAISE NOTICE 'Some tickets had an unrecognised assigned_to name and will be set to NULL: %',
                    (SELECT string_agg(id::text, ', ') FROM tickets WHERE assigned_to IS NOT NULL AND assigned_to_id IS NULL);
            END IF;
            ALTER TABLE tickets DROP COLUMN assigned_to;
            ALTER TABLE tickets RENAME COLUMN assigned_to_id TO assigned_to;
            ALTER TABLE tickets ADD CONSTRAINT tickets_assigned_to_fkey
                FOREIGN KEY (assigned_to) REFERENCES employees(id) ON DELETE SET NULL;
        END IF;
    END $$;
    """)

    conn.commit()
    cur.close()
    conn.close()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/employees", response_model=list[Employee])
def get_employees():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM employees ORDER BY name;")
    employees = [dict(e) for e in cur.fetchall()]
    cur.close()
    conn.close()
    return employees

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
    cur.execute("""
        SELECT t.id, t.external_id, t.subject, t.body, t.tags, t.status,
               t.ai_subject, t.category, t.source, t.language,
               e.name AS assigned_to,
               t.suggested_response, t.troubleshooting_steps,
               t.enrichment_done, t.created_at
        FROM tickets t
        LEFT JOIN employees e ON e.id = t.assigned_to
    """)
    tickets = [dict(t) for t in cur.fetchall()]
    cur.close()
    conn.close()

    try:
        cache = get_redis_client()
        cache.setex("tickets", CACHE_TTL, json.dumps(tickets, default=str))
    except Exception:
        pass

    return tickets

@app.patch("/tickets/{ticket_id}", response_model=Ticket)
def update_ticket(ticket_id: int, update: TicketUpdate):
    conn = get_db_connection()
    cur = conn.cursor()

    # Explicit whitelist of updatable fields
    _allowed_fields = {"status", "assigned_to"}
    fields = {}
    if update.status is not None:
        fields["status"] = update.status
    if update.assigned_to is not None:
        # Resolve employee name to FK integer id
        cur.execute("SELECT id FROM employees WHERE name = %s", (update.assigned_to,))
        emp_row = cur.fetchone()
        if emp_row is None:
            cur.close()
            conn.close()
            raise HTTPException(status_code=400, detail="Employee not found")
        fields["assigned_to"] = emp_row["id"]

    # Validate all keys are in the allowed set (defence-in-depth)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    assert all(k in _allowed_fields for k in fields), "Unexpected field in update"

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [ticket_id]

    cur.execute(f"""
        WITH updated AS (
            UPDATE tickets SET {set_clause} WHERE id = %s RETURNING id
        )
        SELECT t.id, t.external_id, t.subject, t.body, t.tags, t.status,
               t.ai_subject, t.category, t.source, t.language,
               e.name AS assigned_to,
               t.suggested_response, t.troubleshooting_steps,
               t.enrichment_done, t.created_at
        FROM tickets t
        LEFT JOIN employees e ON e.id = t.assigned_to
        JOIN updated ON updated.id = t.id
    """, values)
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Invalidate cache
    try:
        cache = get_redis_client()
        cache.delete("tickets")
    except Exception:
        pass

    return dict(row)

@app.get("/tickets/{ticket_id}/messages", response_model=list[TicketMessage])
def get_ticket_messages(ticket_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, ticket_id, author, body, created_at FROM ticket_messages WHERE ticket_id = %s ORDER BY created_at ASC;",
        (ticket_id,)
    )
    messages = [dict(m) for m in cur.fetchall()]
    cur.close()
    conn.close()
    return messages

@app.post("/tickets/{ticket_id}/messages", response_model=TicketMessage)
def post_ticket_message(ticket_id: int, payload: TicketMessageCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    # Verify ticket exists
    cur.execute("SELECT id FROM tickets WHERE id = %s;", (ticket_id,))
    if cur.fetchone() is None:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Ticket not found")
    cur.execute(
        "INSERT INTO ticket_messages (ticket_id, author, body) VALUES (%s, %s, %s) RETURNING id, ticket_id, author, body, created_at;",
        (ticket_id, payload.author, payload.body)
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return dict(row)