import logging
from db import get_db_connection
from ai_enrichment import detect_source, generate_ai_subject
from redis_queue import pop_ticket, invalidate_tickets_cache
import redis.exceptions

# How many BLPOP timeouts before we do a full Postgres reconciliation scan
# (catches any tickets that were inserted before the queue was available)
RECONCILE_AFTER = 6  # exactly 60 seconds of idle time (6 × 10s timeout)


def enrich_ticket(ticket_id: int):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, body, tags
        FROM tickets
        WHERE id = %s AND enrichment_done = FALSE
    """, (ticket_id,))

    t = cur.fetchone()
    if t is None:
        cur.close()
        conn.close()
        return

    print(f"Enriching ticket {ticket_id}")

    source = detect_source(t["tags"])
    ai_subject = generate_ai_subject(t["body"])

    cur.execute("""
        UPDATE tickets
        SET source=%s,
            ai_subject=%s,
            enrichment_done=TRUE
        WHERE id=%s
    """, (source, ai_subject, ticket_id))

    conn.commit()
    cur.close()
    conn.close()

    try:
        invalidate_tickets_cache()
    except redis.exceptions.ConnectionError as e:
        logging.warning("Redis unavailable, could not invalidate cache: %s", e)


def reconcile():
    """Enrich any tickets that slipped through (e.g. ingested before Redis was ready)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM tickets WHERE enrichment_done = FALSE")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    for row in rows:
        enrich_ticket(row["id"])


def run():
    idle_count = 0
    while True:
        try:
            ticket_id = pop_ticket(timeout=10)
        except redis.exceptions.ConnectionError as e:
            logging.warning("Redis unavailable, falling back to reconcile: %s", e)
            ticket_id = None

        if ticket_id is not None:
            idle_count = 0
            enrich_ticket(ticket_id)
        else:
            idle_count += 1
            if idle_count >= RECONCILE_AFTER:
                idle_count = 0
                reconcile()


if __name__ == "__main__":
    run()