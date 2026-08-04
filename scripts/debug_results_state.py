# Simulating the object passed to state
state = {
    "result": {"assessment_result": {"total_score": 2}},
    "score": 2,
    "severity": {"label": "Minimal"},
    "crisisAlert": False,
}


# Simulating useClinicalResults' extraction logic
def extract(state):
    severityLevel = state.get("result", {}).get("severity_level") or state.get(
        "severity_level"
    )
    # In my case: result is {"assessment_result": {"total_score": 2}}
    # The state object does not have severity_level at the top, nor in result.
    # So severityLevel becomes undefined/None.
    score = state.get("result", {}).get("score") or state.get("score")
    print(f"SeverityLevel: {severityLevel}")
    print(f"Score: {score}")


extract(state)
