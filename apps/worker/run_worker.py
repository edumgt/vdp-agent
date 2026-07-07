import os

import redis
from rq import Queue, Worker


def _env(name, fallback=None):
    return os.environ.get(name, fallback)


if __name__ == "__main__":
    conn = redis.Redis(host=_env("REDIS_HOST", "localhost"), port=int(_env("REDIS_PORT", "6379")))
    queue = Queue("accounting-jobs", connection=conn)
    worker = Worker([queue], connection=conn)
    print("[worker] running. queue=accounting-jobs")
    worker.work()
