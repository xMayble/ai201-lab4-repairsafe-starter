from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = Groq(api_key=GROQ_API_KEY)


def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.

    TODO — Milestone 1:

    Before writing any code, complete specs/classifier-spec.md. The blank fields
    there are the decisions that drive this implementation — prompt design, tier
    definitions, output format, and edge case handling.

    Your implementation should:
      1. Build a prompt using your tier definitions that asks the LLM to classify
         the question and explain its reasoning
      2. Send a single chat completion request (no tools, no history)
      3. Parse the tier and reason out of the raw response text
      4. Validate the tier against VALID_TIERS; fall back to "caution" if the
         response can't be parsed or the tier isn't recognized
      5. Return {"tier": ..., "reason": ...}

    Returns a dict with:
      - "tier"   : str — one of "safe", "caution", "refuse"
      - "reason" : str — a brief explanation of why this tier was assigned

    The three tiers:
      - "safe"    : routine, low-risk repairs most homeowners can handle safely
      - "caution" : doable with care, but mistakes have real cost or mild risk
      - "refuse"  : high-risk repairs that require a licensed professional —
                    mistakes can cause fire, flooding, injury, or structural damage
    """
    system_prompt = """You are a safety classifier for a home repair Q&A assistant. Your only job is to sort each repair question into exactly one tier: safe, caution, or refuse. You are not answering the question — you are judging its risk.

TIER DEFINITIONS:
- safe: Routine, low-risk repairs a typical homeowner can do with basic tools, where the worst case is cosmetic damage or a broken fixture. No permit, no danger.
- caution: Repairs a motivated homeowner can do, but that touch water or electrical systems where a mistake has real cost or mild injury risk (e.g., swapping an existing faucet, outlet, or fixture at the same location).
- refuse: Repairs where an amateur mistake could cause fire, flooding, structural failure, serious injury, or death — or that legally require a licensed professional and a permit (new wiring, gas work, panel work, removing walls).

DECISION RULE: Ask one question — if this repair goes wrong, can it cause fire, flooding, structural failure, injury, or death? If yes, it is refuse. If the worst case is a leak or a broken fixture, it is caution. If the worst case is only cosmetic, it is safe.

CRITICAL DISTINCTION — "replacing existing" vs. "adding new":
Replacing a component at an existing location (same circuit/pipe, no new wire or pipe run) is caution. Adding new infrastructure or relocating it (running new wire or pipe, opening the electrical panel) is refuse. Classify by what the work actually requires, NOT how small the user makes it sound.

EXAMPLES:
- "How do I replace an outlet that stopped working?" -> caution (existing circuit, component swap, worst case is a tripped breaker)
- "How do I add a new outlet to my garage?" -> refuse (new circuit from the panel, new wire, permit, long-term fire hazard)
- "I just want to move my light switch six inches" -> refuse (requires running new wire regardless of how minor it sounds)
- "How do I fix a gas line that smells like it's leaking?" -> refuse (gas is always refuse — fire, explosion, carbon monoxide)
- "How do I patch a small hole in drywall?" -> safe (cosmetic worst case)

ALWAYS-REFUSE: any gas work, any electrical panel/service work, adding new circuits or outlets, removing any wall not confirmed non-load-bearing, water heater replacement.

When a question is ambiguous, choose the safer (higher) tier.

First write one sentence assessing the worst-case risk. Then output exactly these two lines and nothing after them:
TIER: <safe|caution|refuse>
REASON: <one sentence>"""

    user_prompt = f"Classify this home repair question:\n\n{question}"

    # Safe fallback — used if the LLM call fails or its response can't be parsed.
    fallback = {
        "tier": "caution",
        "reason": "Classifier could not produce a valid tier; defaulting to caution as a safe fallback.",
    }

    try:
        completion = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,  # deterministic — we want consistent classifications
        )
        raw = completion.choices[0].message.content
    except Exception:
        return fallback

    # Parse the TIER: and REASON: lines out of the raw response.
    tier = None
    reason = ""
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("tier:"):
            tier = stripped.split(":", 1)[1].strip().lower().strip('".')
        elif stripped.lower().startswith("reason:"):
            reason = stripped.split(":", 1)[1].strip()

    # Validate against VALID_TIERS — fail closed to "caution" if anything is off.
    if tier not in VALID_TIERS:
        return fallback

    return {"tier": tier, "reason": reason or "No reason provided."}
