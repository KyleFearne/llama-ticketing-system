import glob
import logging
import time
from ingest import ingest_ticket
from redis_queue import push_ticket
import redis.exceptions

DATA_FOLDER = "/data/tickets"
already_seen = set()

def ingest_all_new():
    global already_seen
    files = glob.glob(f"{DATA_FOLDER}/*.txt")
    for f in files:
        if f not in already_seen:
            ticket_id = ingest_ticket(f)
            already_seen.add(f)
            if ticket_id is not None:
                try:
                    push_ticket(ticket_id)
                except redis.exceptions.ConnectionError as e:
                    logging.warning("Redis unavailable, ticket %s will be enriched via reconcile: %s", ticket_id, e)

def main():
    # initial run
    ingest_all_new()

    # poll continuously
    while True:
        ingest_all_new()
        time.sleep(5)  # adjust polling interval as needed

if __name__ == "__main__":
    main()