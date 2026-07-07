import os

import redis
from rq import Queue


def _env(name, fallback=None):
    return os.environ.get(name, fallback)


_redis_conn = redis.Redis(host=_env("REDIS_HOST", "localhost"), port=int(_env("REDIS_PORT", "6379")))
job_queue = Queue("accounting-jobs", connection=_redis_conn)
