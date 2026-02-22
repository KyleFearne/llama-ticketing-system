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
        assigned_to INTEGER REFERENCES employees(id) ON DELETE SET NULL,
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
        "suggested_response": "TEXT",
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
    print("init_db: schema ready")

if __name__ == "__main__":
    main()