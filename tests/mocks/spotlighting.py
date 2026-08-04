class SpotlightingEngine:
    def __init__(self, strict_mode=False):
        pass

    def create_spotlighted_prompt(self, template_type, prompt):
        return f"=== USER INPUT START ===\n{prompt}\n=== USER INPUT END ==="


class SpotlightTemplateType:
    SENTIMENT_ANALYSIS = "sentiment"
