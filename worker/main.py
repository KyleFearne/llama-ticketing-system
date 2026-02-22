import os
import time
import glob
from db import get_db_connection

DATA_FOLDER = "/data/tickets"  # path mounted from docker-compose


# CONSIDER STAGGERING INGESTION LATER?
def ingest_ticket(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # split into tags / body
    if "---" in content:
        tags_line, body = content.split("---", 1)
    else:
        tags_line = ""
        body = content

    tags_line = tags_line.replace("Tags:", "").strip()
    tags = [t.strip() for t in tags_line.split(",") if t.strip()]

    # first line as subject (AI summarization later)
    subject = body.strip().split("\n")[0]

    # determine status from tags (optional)
    status = "closed" if "auto-closed" in tags else "open"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO tickets (subject, body, tags, status)
        VALUES (%s, %s, %s, %s)
        """,
        (subject, body.strip(), tags, status)
    )
    conn.commit()
    cur.close()
    conn.close()

    print(f"Ingested ticket: {subject} | tags: {tags} | status: {status}")


def ingest_all_tickets(already_seen=None):
    """Ingest all tickets in the folder that haven't been ingested yet"""
    if already_seen is None:
        already_seen = set()
    files = glob.glob(f"{DATA_FOLDER}/*.txt")
    for f in files:
        if f not in already_seen:
            ingest_ticket(f)
            already_seen.add(f)
    return already_seen


def main():
    already_seen = set()

    # === First-pass ingestion ===
    already_seen = ingest_all_tickets(already_seen)

    # === Then start live polling ===
    while True:
        already_seen = ingest_all_tickets(already_seen)
        time.sleep(5)  # poll interval


if __name__ == "__main__":
    main()