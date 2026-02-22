# api/ingest.py
import glob
from db import get_db_connection
import os

DATA_FOLDER = "/data/tickets"  # mounted from docker-compose


def ingest_ticket(file_path):
    external_id = os.path.basename(file_path).replace(".txt", "")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split tags / body
    if "---" in content:
        tags_line, body = content.split("---", 1)
    else:
        tags_line = ""
        body = content

    tags_line = tags_line.replace("Tags:", "").strip()
    tags = [t.strip() for t in tags_line.split(",") if t.strip()]

    subject = body.strip().split("\n")[0]
    status = "closed" if "auto-closed" in tags else "open"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO tickets (external_id,subject, body, tags, status, enrichment_done)
        VALUES (%s, %s, %s, %s, %s, FALSE)
        ON CONFLICT (external_id) DO NOTHING
        RETURNING id
    """, (external_id, subject, body.strip(), tags, status))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    print(f"Ingested ticket: {subject} | tags: {tags} | status: {status}")
    return row["id"] if row else None


def ingest_all_tickets():
    files = glob.glob(f"{DATA_FOLDER}/*.txt")
    for f in files:
        ingest_ticket(f)