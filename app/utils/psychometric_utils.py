# ============================================================================
# FILE 13: app/utils/psychometric_utils.py
# Utility functions for psychometric analysis
# ============================================================================

from typing import List, Dict, Tuple
import numpy as np
from datetime import datetime, timedelta
import json

def calculate_reliability_score(
    responses: List[Dict],
    reverse_items: List[int]
) -> float:
    """
    Calculate Cronbach's alpha for internal consistency
    
    Args:
        responses: List of item responses
        reverse_items: Indices of reverse-scored items
        
    Returns:
        Cronbach's alpha (0-1)
    """
    # Convert responses to matrix
    data = []
    for response in responses:
        value = response["answer_value"]
        if response["question_id"] in reverse_items:
            value = 6 - value  # Reverse score (assuming 1-5 scale)
        data.append(value)
    
    data = np.array([data])
    
    if len(data[0]) < 2:
        return 0.0
    
    # Calculate variance
    item_variances = np.var(data, axis=0)
    total_variance = np.var(data.sum(axis=1))
    
    # Cronbach's alpha formula
    k = len(data[0])
    if total_variance == 0:
        return 0.0
    
    alpha = (k / (k - 1)) * (1 - (sum(item_variances) / total_variance))
    return float(np.clip(alpha, 0, 1))

def detect_response_patterns(responses: List[Dict]) -> Dict:
    """
    Detect invalid response patterns (e.g., all same answer)
    
    Args:
        responses: List of responses
        
    Returns:
        Dict with pattern detection results
    """
    values = [r["answer_value"] for r in responses]
    
    # Check for straight-lining (all same answer)
    if len(set(values)) == 1:
        return {
            "valid": False,
            "issue": "straight_lining",
            "description": "All responses are identical"
        }
    
    # Check for alternating pattern
    if len(values) >= 4:
        alternating = all(values[i] != values[i+1] for i in range(len(values)-1))
        if alternating:
            return {
                "valid": False,
                "issue": "alternating_pattern",
                "description": "Responses show alternating pattern"
            }
    
    # Check for excessive variance
    if np.std(values) > 1.5:
        return {
            "valid": True,
            "warning": "high_variance",
            "description": "Responses show high variance - may indicate inconsistency"
        }
    
    return {
        "valid": True,
        "issue": None
    }

def calculate_percentile_rank(score: float, norm_data: List[float]) -> int:
    """
    Calculate percentile rank based on normative data
    
    Args:
        score: Individual score
        norm_data: List of normative scores
        
    Returns:
        Percentile rank (0-100)
    """
    if not norm_data:
        return 50  # Default to median
    
    percentile = (sum(1 for x in norm_data if x < score) / len(norm_data)) * 100
    return int(np.clip(percentile, 0, 100))

def generate_confidence_interval(
    score: float,
    std_error: float,
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Generate confidence interval for a score
    
    Args:
        score: Point estimate
        std_error: Standard error
        confidence_level: Desired confidence level
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    from scipy import stats
    
    # Z-score for confidence level
    z = stats.norm.ppf((1 + confidence_level) / 2)
    
    margin = z * std_error
    
    return (
        float(max(0, score - margin)),
        float(min(1, score + margin))
    )

def format_psychometric_report(
    results: Dict,
    include_visualizations: bool = True
) -> str:
    """
    Format psychometric results into readable report
    
    Args:
        results: Analysis results
        include_visualizations: Whether to include visualization data
        
    Returns:
        Formatted report string
    """
    report = []
    
    report.append("=" * 60)
    report.append("PSYCHOMETRIC ANALYSIS REPORT")
    report.append("=" * 60)
    report.append("")
    
    # Client info
    if "client_id" in results:
        report.append(f"Client ID: {results['client_id']}")
    
    if "session_date" in results:
        report.append(f"Session Date: {results['session_date']}")
    
    report.append("")
    report.append("-" * 60)
    report.append("SENTIMENT ANALYSIS")
    report.append("-" * 60)
    
    sentiment = results.get("sentiment_analysis", {})
    report.append(f"Overall Sentiment: {sentiment.get('interpretation', 'N/A')}")
    report.append(f"Polarity Score: {sentiment.get('overall_score', 0):.2f}")
    report.append(f"Confidence: {sentiment.get('confidence', 0):.2%}")
    
    report.append("")
    report.append("-" * 60)
    report.append("EMOTION ANALYSIS")
    report.append("-" * 60)
    
    emotions = results.get("emotion_analysis", {})
    report.append(f"Dominant Emotion: {emotions.get('dominant_emotion', 'N/A').title()}")
    
    if "scores" in emotions:
        report.append("\nEmotion Scores:")
        for emotion, score in sorted(emotions["scores"].items(), key=lambda x: x[1], reverse=True)[:5]:
            report.append(f"  {emotion.title()}: {score:.2%}")
    
    report.append("")
    report.append("-" * 60)
    report.append("KEY INSIGHTS")
    report.append("-" * 60)
    
    insights = results.get("key_insights", [])
    for i, insight in enumerate(insights, 1):
        report.append(f"{i}. {insight}")
    
    if results.get("red_flags"):
        report.append("")
        report.append("-" * 60)
        report.append("⚠️  RED FLAGS")
        report.append("-" * 60)
        
        for flag in results["red_flags"]:
            report.append(f"[{flag['severity'].upper()}] {flag['description']}")
    
    report.append("")
    report.append("=" * 60)
    report.append(f"Report Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("=" * 60)
    
    return "\n".join(report)

def export_to_json(results: Dict, filepath: str):
    """Export results to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2, default=str)

def export_to_csv(results_list: List[Dict], filepath: str):
    """Export multiple results to CSV"""
    import csv
    
    if not results_list:
        return
    
    # Extract keys from first result
    keys = results_list[0].keys()
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results_list)


