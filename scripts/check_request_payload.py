import json

# This mimics what the backend likely receives
# The frontend sends the TEXT of the option, but the backend expects the VALUE
# Based on the error, the 'responses' dict contains the text.
responses = {"phq9_1": "Several days", "phq9_2": "Nearly every day"}

# The backend service expects an int, so we need a mapping
options_map = {
    "Not at all": 0,
    "Several days": 1,
    "More than half the days": 2,
    "Nearly every day": 3,
}

# Transform
transformed_responses = {k: options_map.get(v, v) for k, v in responses.items()}
print(f"Transformed: {transformed_responses}")
print(f"Sum: {sum(transformed_responses.values())}")
