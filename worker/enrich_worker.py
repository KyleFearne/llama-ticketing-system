import time
from db import get_db_connection
from ai_enrichment import detect_source, generate_ai_subject


def run():
    while True:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, body, tags
            FROM tickets
            WHERE enrichment_done = FALSE
        """)

        tickets = cur.fetchall()

        for t in tickets:
            ticket_id = t["id"]
            body = t["body"]
            tags = t["tags"]

            print(f"Enriching ticket {ticket_id}")

            source = detect_source(body)
            ai_subject = generate_ai_subject(body)

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

        time.sleep(5)


if __name__ == "__main__":
    run()