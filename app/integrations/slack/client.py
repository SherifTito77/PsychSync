from typing import Any


class SlackClient:
    def __init__(self, token: str = None):
        pass

    def chat_postMessage(self, **kwargs: Any) -> Any:
        return {"ok": True}

    def views_open(self, **kwargs: Any) -> Any:
        return {"ok": True}
