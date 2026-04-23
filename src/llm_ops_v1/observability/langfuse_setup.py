from langfuse import get_client


def get_langfuse_client():
    return get_client()


def flush_langfuse() -> None:
    get_langfuse_client().flush()
