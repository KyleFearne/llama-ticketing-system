# worker/init_db.py
from db import get_db_connection

def main():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id SERIAL PRIMARY KEY,
        external_id TEXT,
        subject TEXT,
        body TEXT,
        tags TEXT[],
        status TEXT DEFAULT 'open',
        ai_subject TEXT,
        category TEXT,
        suggested_assignee TEXT,
        source TEXT,
        enrichment_done BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT now()
    );
    """)

    # important for your ON CONFLICT(external_id)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS tickets_external_id_uq
    ON tickets(external_id);
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("init_db: schema ready")

if __name__ == "__main__":
    main()