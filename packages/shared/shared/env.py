import os


def env(name: str, fallback: str | None = None) -> str | None:
    return os.environ.get(name, fallback)
