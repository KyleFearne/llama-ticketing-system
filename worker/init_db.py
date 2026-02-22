# worker/init_db.py
from db import get_db_connection

def main():
    conn = get_db_connection()
    cur = conn.cursor()

    # Employees table (must exist before tickets FK is added)
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
        external_id TEXT,
        subject TEXT,
        body TEXT,
        tags TEXT[],
        status TEXT DEFAULT 'new',
        ai_subject TEXT,
        category TEXT,
        source TEXT,
        language TEXT,
        assigned_to TEXT,
        suggested_response TEXT,
        enrichment_done BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT now()
    );
    """)

    # important for your ON CONFLICT(external_id)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS tickets_external_id_uq
    ON tickets(external_id);
    """)

    # Migrations for existing databases: add new columns if they don't exist
    _safe_new_cols = {
        "language": "TEXT",
        "assigned_to": "TEXT",
        "suggested_response": "TEXT",
    }
    for col, definition in _safe_new_cols.items():
        cur.execute(f"ALTER TABLE tickets ADD COLUMN IF NOT EXISTS {col} {definition};")

    conn.commit()
    cur.close()
    conn.close()
    print("init_db: schema ready")

if __name__ == "__main__":
    main()