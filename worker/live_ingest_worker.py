import glob
import time
from ingest import ingest_ticket

DATA_FOLDER = "/data/tickets"
already_seen = set()

def ingest_all_new():
    global already_seen
    files = glob.glob(f"{DATA_FOLDER}/*.txt")
    for f in files:
        if f not in already_seen:
            ingest_ticket(f)
            already_seen.add(f)

def main():
    # initial run
    ingest_all_new()

    # poll continuously
    while True:
        ingest_all_new()
        time.sleep(5)  # adjust polling interval as needed

if __name__ == "__main__":
    main()