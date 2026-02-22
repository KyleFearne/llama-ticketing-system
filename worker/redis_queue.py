import os
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
QUEUE_KEY = "ticket_enrichment_queue"
API_CACHE_KEY = "tickets"

_client = None


def get_redis_client():
    global _client
    if _client is None:
        _client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    return _client


def push_ticket(ticket_id: int):
    """Push a ticket ID onto the enrichment queue."""
    get_redis_client().rpush(QUEUE_KEY, ticket_id)


def pop_ticket(timeout: int = 10):
    """Blocking pop with timeout. Returns ticket_id (int) or None on timeout."""
    result = get_redis_client().blpop(QUEUE_KEY, timeout=timeout)
    if result:
        _, ticket_id = result
        return int(ticket_id)
    return None


def invalidate_tickets_cache():
    """Delete the cached /tickets response so the API serves fresh data."""
    get_redis_client().delete(API_CACHE_KEY)
