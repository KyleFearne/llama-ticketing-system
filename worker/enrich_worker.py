import logging
from db import get_db_connection
from ai_enrichment import detect_source, detect_language, generate_ai_subject, generate_suggested_response
from redis_queue import pop_ticket, invalidate_tickets_cache
import redis.exceptions

# How many BLPOP timeouts before we do a full Postgres reconciliation scan
# (catches any tickets that were inserted before the queue was available)
RECONCILE_AFTER = 6  # exactly 60 seconds of idle time (6 × 10s timeout)


def get_next_assignee(cur):
    """Return the name of the employee with the fewest assigned tickets."""
    cur.execute("""
        SELECT e.name, COUNT(t.id) AS cnt
        FROM employees e
        LEFT JOIN tickets t ON t.assigned_to = e.name
        GROUP BY e.name
        ORDER BY cnt ASC, e.name ASC
        LIMIT 1
    """)
    row = cur.fetchone()
    return row["name"] if row else None


def enrich_ticket(ticket_id: int):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, body, tags, status
        FROM tickets
        WHERE id = %s AND enrichment_done = FALSE
    """, (ticket_id,))

    t = cur.fetchone()
    if t is None:
        cur.close()
        conn.close()
        return

    print(f"Enriching ticket {ticket_id}")

    source = detect_source(t["body"])
    ai_subject = generate_ai_subject(t["body"])
    language = detect_language(t["body"])
    assigned_to = get_next_assignee(cur)

    # Only generate a suggested response for non-closed tickets
    suggested_response = None
    if t["status"] != "closed":
        suggested_response = generate_suggested_response(t["body"])

    cur.execute("""
        UPDATE tickets
        SET source=%s,
            ai_subject=%s,
            language=%s,
            assigned_to=%s,
            suggested_response=%s,
            enrichment_done=TRUE
        WHERE id=%s
    """, (source, ai_subject, language, assigned_to, suggested_response, ticket_id))

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