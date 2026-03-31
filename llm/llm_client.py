"""
LLM Client — Anthropic Claude Integration
Calls Claude API for breach explanations with fallback support.
Rate-limited: one call per ward per breach event.
"""
import os, json, sqlite3, logging, time
from datetime import datetime

logger = logging.getLogger("llm.client")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "hospital.db")

# Track calls to rate-limit
_call_tracker = {}  # ward_id -> last_breach_id

def call_llm(context: dict, breach_id: int = None) -> dict:
    """
    Call Claude API for breach explanation.
    Returns dict with explanation, confidence, model info.
    """
    from .context_assembler import assemble_breach_context
    from .prompt_templates import SYSTEM_PROMPT, build_breach_prompt, build_fallback_explanation

    ward_id = context.get('ward_id', '')

    # Rate limit: only call once per breach
    if breach_id and _call_tracker.get(ward_id) == breach_id:
        logger.info(f"Rate limited: already explained breach {breach_id} for {ward_id}")
        return None

    prompt = build_breach_prompt(context)
    start = time.time()

    try:
        import anthropic
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        if not api_key or api_key == 'your_anthropic_api_key_here':
            raise ValueError("No API key configured")

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        explanation = response.content[0].text
        latency = int((time.time() - start) * 1000)
        tokens = response.usage.input_tokens + response.usage.output_tokens

        # Extract confidence from response
        confidence = "medium"
        for level in ["high", "low"]:
            if level in explanation.lower():
                confidence = level; break

        result = {
            'explanation': explanation,
            'confidence': confidence,
            'model_used': 'claude-sonnet',
            'is_fallback': False,
            'tokens_used': tokens,
            'latency_ms': latency,
        }

    except Exception as e:
        logger.warning(f"LLM API failed ({e}), using fallback")
        explanation = build_fallback_explanation(context)
        result = {
            'explanation': explanation,
            'confidence': 'low',
            'model_used': 'rule-based-fallback',
            'is_fallback': True,
            'tokens_used': 0,
            'latency_ms': int((time.time() - start) * 1000),
        }

    # Save to DB
    _save_explanation(ward_id, breach_id, context, prompt, result)

    # Update rate limiter
    if breach_id:
        _call_tracker[ward_id] = breach_id

    # Update breach record with explanation
    if breach_id:
        _update_breach(breach_id, result)

    return result

def _save_explanation(ward_id, breach_id, context, prompt, result):
    """Save LLM explanation to database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        ward_name = context.get('current', {}).get('ward_name', '')
        conn.execute("""INSERT INTO llm_explanations
            (breach_id, ward_id, ward_name, context_json, prompt_used,
             explanation, confidence, model_used, is_fallback, tokens_used, latency_ms)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (breach_id, ward_id, ward_name, json.dumps(context, default=str),
             prompt, result['explanation'], result['confidence'],
             result['model_used'], result['is_fallback'],
             result['tokens_used'], result['latency_ms']))
        conn.commit(); conn.close()
    except Exception as e:
        logger.error(f"Failed to save explanation: {e}")

def _update_breach(breach_id, result):
    """Update breach record with LLM explanation."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""UPDATE sla_breaches SET
            llm_explanation=?, llm_confidence=? WHERE id=?""",
            (result['explanation'], result['confidence'], breach_id))
        conn.commit(); conn.close()
    except Exception as e:
        logger.error(f"Failed to update breach: {e}")

def explain_active_breaches():
    """Generate explanations for all active breaches without one."""
    from .context_assembler import assemble_breach_context
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    breaches = conn.execute(
        "SELECT id, ward_id FROM sla_breaches WHERE status='active' AND llm_explanation IS NULL"
    ).fetchall()
    conn.close()

    for b in breaches:
        context = assemble_breach_context(b['ward_id'], b['id'])
        call_llm(context, b['id'])
        logger.info(f"Explained breach {b['id']} for {b['ward_id']}")
