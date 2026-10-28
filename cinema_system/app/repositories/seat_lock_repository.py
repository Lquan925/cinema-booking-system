"""Redis-backed seat lock data access."""
from functools import wraps

import redis

from app.redis_client import get_redis_client


class SeatLockStoreError(Exception):
    """Raised when the seat-lock store is unavailable."""


def _translate_store_errors(operation):
    @wraps(operation)
    def wrapper(*args, **kwargs):
        try:
            return operation(*args, **kwargs)
        except redis.exceptions.RedisError as error:
            raise SeatLockStoreError(str(error)) from error

    return wrapper


def _seat_lock_key(showtime_id, seat_id):
    return f"seat_lock:{showtime_id}:{seat_id}"


def _user_locks_key(user_id, showtime_id):
    return f"user_locks:{user_id}:{showtime_id}"


@_translate_store_errors
def get_holders(showtime_id, seat_ids):
    client = get_redis_client()
    keys = [_seat_lock_key(showtime_id, seat_id) for seat_id in seat_ids]
    holders = client.mget(keys) if keys else []
    return {
        seat_id: holder
        for seat_id, holder in zip(seat_ids, holders)
        if holder is not None
    }


@_translate_store_errors
def get_holder(showtime_id, seat_id):
    return get_redis_client().get(_seat_lock_key(showtime_id, seat_id))


@_translate_store_errors
def get_ttl(showtime_id, seat_id):
    ttl = get_redis_client().ttl(_seat_lock_key(showtime_id, seat_id))
    return ttl if ttl is not None and ttl >= 0 else None


@_translate_store_errors
def get_user_locked_seats(user_id, showtime_id):
    return get_redis_client().smembers(_user_locks_key(user_id, showtime_id)) or set()


@_translate_store_errors
def add_user_locked_seat(user_id, showtime_id, seat_id):
    get_redis_client().sadd(_user_locks_key(user_id, showtime_id), str(seat_id))


@_translate_store_errors
def remove_user_locked_seat(user_id, showtime_id, seat_id):
    get_redis_client().srem(_user_locks_key(user_id, showtime_id), str(seat_id))


@_translate_store_errors
def expire_user_locks(user_id, showtime_id, ttl):
    get_redis_client().expire(_user_locks_key(user_id, showtime_id), ttl)


@_translate_store_errors
def delete_user_locks(user_id, showtime_id):
    get_redis_client().delete(_user_locks_key(user_id, showtime_id))


@_translate_store_errors
def count_user_locks(user_id, showtime_id):
    return get_redis_client().scard(_user_locks_key(user_id, showtime_id))


@_translate_store_errors
def acquire(showtime_id, seat_id, user_id, ttl):
    acquired = get_redis_client().set(
        _seat_lock_key(showtime_id, seat_id),
        str(user_id),
        nx=True,
        ex=ttl,
    )
    return bool(acquired)


@_translate_store_errors
def refresh(showtime_id, seat_id, ttl):
    get_redis_client().expire(_seat_lock_key(showtime_id, seat_id), ttl)


@_translate_store_errors
def release(showtime_id, seat_id):
    get_redis_client().delete(_seat_lock_key(showtime_id, seat_id))
