class ModelAdapter:
    def __init__(self, kind: str, config: dict):
        self.kind = kind
        self.config = config

    def run(self, prompt: str) -> dict:
        # single place to integrate Claude/GPT/other LLMs
        # For now, this is a stub returning mock output
        return {"text": "mock response for: " + prompt}


# higher-level helper
orchestrators = {}


def get_orchestrator(name: str) -> ModelAdapter:
    return orchestrators.get(name) or ModelAdapter("mock", {})
