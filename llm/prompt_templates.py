"""
LLM Prompt Templates
Structured prompts for clinical operations analysis.
"""

SYSTEM_PROMPT = """You are a clinical operations analyst. Generate concise, factual explanations \
of occupancy alerts for hospital charge nurses. Be specific, avoid jargon, and end with an \
expected resolution window based on historical patterns. Keep responses to 2-3 sentences maximum."""

def build_breach_prompt(context: dict) -> str:
    """Build user prompt for SLA breach explanation."""
    c = context.get('current', {})
    b = context.get('breach', {})
    bl = context.get('baseline', {})
    a = context.get('anomaly', {})

    prompt = f"""OCCUPANCY ALERT — Explain this situation:

Ward: {c.get('ward_name', 'Unknown')}
Current Occupancy: {c.get('occupancy_percent', 0)}% ({c.get('occupied_beds', 0)}/{c.get('total_beds', 0)} beds)
Status: {c.get('status', 'unknown')}
Trend: {c.get('trend', 'unknown')}

Breach Duration: {b.get('consecutive_hours', 0)} consecutive hours above 85%
Peak During Breach: {b.get('peak_occupancy', 0)}%

7-Day Baseline for this hour: {bl.get('avg_occupancy', 'N/A')}% (±{bl.get('std_occupancy', 'N/A')}%)
Baseline Sample Size: {bl.get('sample_count', 0)} data points

Anomaly Z-Score: {a.get('z_score', 'N/A')} (anomaly={'Yes' if a.get('is_anomaly') else 'No'})
Current Admissions vs Baseline: {a.get('current_count', 'N/A')} vs {a.get('baseline_mean', 'N/A')}

Provide: 1) Why this is happening, 2) Expected resolution window, 3) Confidence level (high/medium/low)."""
    return prompt

def build_fallback_explanation(context: dict) -> str:
    """Generate rule-based explanation when LLM is unavailable."""
    c = context.get('current', {})
    b = context.get('breach', {})
    bl = context.get('baseline', {})
    a = context.get('anomaly', {})

    ward = c.get('ward_name', 'This ward')
    pct = c.get('occupancy_percent', 0)
    hours = b.get('consecutive_hours', 0)
    baseline = bl.get('avg_occupancy', 0)

    if a.get('is_anomaly'):
        reason = f"Admission rates are significantly above the 7-day average (z-score: {a.get('z_score', 0):.1f}), suggesting an unusual surge."
    elif pct > baseline + 10:
        reason = f"Occupancy is {pct - baseline:.0f}% above the typical baseline of {baseline}% for this hour."
    else:
        reason = f"Occupancy has gradually risen to {pct}% over the past {hours} hours."

    resolution = "Based on typical discharge patterns, occupancy should begin declining within 2-4 hours." \
        if hours < 4 else "Extended breach duration suggests resolution may take 4-8 hours."

    return f"{ward} is at {pct}% occupancy. {reason} {resolution}"
