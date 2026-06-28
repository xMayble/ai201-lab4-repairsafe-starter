# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Tier definitions

*Write a one-sentence definition for each tier that is precise enough to use as part of your classification prompt. Vague definitions produce inconsistent classifications.*

**safe:**
```
Routine, low-risk repairs a typical homeowner can do with basic tools, where the worst-case outcome is cosmetic damage or a broken fixture — no permit, no danger.
```

**caution:**
```
Repairs a motivated homeowner can do, but that touch water or electrical systems where a mistake has real cost or mild injury risk — like swapping an existing faucet, outlet, or fixture at the same location.
```

**refuse:**
```
Repairs where an amateur mistake could cause fire, flooding, structural failure, serious injury, or death — or that legally require a licensed professional and a permit (new wiring, gas work, panel work, removing walls).
```

---

### Classification approach

*How will the LLM classify the question? Will you give it just the tier definitions, or also examples (few-shot)? Will you ask it to reason step-by-step before naming the tier, or output the tier directly?*

*Consider: what happens when a question is genuinely ambiguous — e.g., "can I replace my own outlets?" Which tier should that land in, and how does your approach handle questions at the boundary?*

```
Approach: few-shot + reason-then-classify. Provide the three tier definitions plus
3-4 worked examples that target the caution/refuse boundary (especially "replace
existing" vs. "add new" electrical). Ask the LLM to give a one-sentence risk
assessment first, then output the tier.

Ambiguous questions default toward the safer (higher) tier. For a vague case like
"can I replace my own outlets?", the like-for-like replacement reading lands in
caution, but if the question implies adding/relocating, it escalates to refuse —
the few-shot examples and the risk-first reasoning step force this distinction
rather than leaving it to a coin flip.
```

---

### Output format

*How will the LLM communicate the tier and reason back to you? Describe the exact text format you'll ask it to use, so you can parse it reliably.*

*The format you used in Lab 3 (`Label: X / Reasoning: Y`) is a reasonable starting point, but you're not required to use it. Whatever you choose, you'll need to parse it in code — so consider how much variation the LLM might introduce and how you'll handle that.*

```
The LLM ends its response with two labeled lines:

TIER: <safe|caution|refuse>
REASON: <one sentence>

The parser scans for the line starting with "TIER:", takes the text after the
colon, strips whitespace and lowercases it, then validates against VALID_TIERS.
The REASON line is captured the same way. This tolerates the model adding its
risk-assessment reasoning text above the labels.

Normalization handles common LLM variation: "Refuse", " refuse ", "refuse." all
collapse to "refuse" before validation.
```

---

### Prompt structure

*Write the actual prompt you'll use — both the system message and the user message. Don't describe it — write it. Vague prompt descriptions produce vague prompts, which produce inconsistent classifications.*

**System message:**
```
You are a safety classifier for a home repair Q&A assistant. Your only job is to
sort each repair question into exactly one tier: safe, caution, or refuse. You are
not answering the question — you are judging its risk.

TIER DEFINITIONS:
- safe: Routine, low-risk repairs a typical homeowner can do with basic tools,
  where the worst case is cosmetic damage or a broken fixture. No permit, no danger.
- caution: Repairs a motivated homeowner can do, but that touch water or electrical
  systems where a mistake has real cost or mild injury risk (e.g., swapping an
  existing faucet, outlet, or fixture at the same location).
- refuse: Repairs where an amateur mistake could cause fire, flooding, structural
  failure, serious injury, or death — or that legally require a licensed
  professional and a permit (new wiring, gas work, panel work, removing walls).

DECISION RULE: Ask one question — if this repair goes wrong, can it cause fire,
flooding, structural failure, injury, or death? If yes, it is refuse. If the worst
case is a leak or a broken fixture, it is caution. If the worst case is only
cosmetic, it is safe.

CRITICAL DISTINCTION — "replacing existing" vs. "adding new":
Replacing a component at an existing location (same circuit/pipe, no new wire or
pipe run) is caution. Adding new infrastructure or relocating it (running new wire
or pipe, opening the electrical panel) is refuse. Classify by what the work
actually requires, NOT how small the user makes it sound.

EXAMPLES:
- "How do I replace an outlet that stopped working?" -> caution (existing circuit,
  component swap, worst case is a tripped breaker)
- "How do I add a new outlet to my garage?" -> refuse (new circuit from the panel,
  new wire, permit, long-term fire hazard)
- "I just want to move my light switch six inches" -> refuse (requires running new
  wire regardless of how minor it sounds)
- "How do I fix a gas line that smells like it's leaking?" -> refuse (gas is always
  refuse — fire, explosion, carbon monoxide)
- "How do I patch a small hole in drywall?" -> safe (cosmetic worst case)

ALWAYS-REFUSE: any gas work, any electrical panel/service work, adding new
circuits or outlets, removing any wall not confirmed non-load-bearing, water
heater replacement.

When a question is ambiguous, choose the safer (higher) tier.

First write one sentence assessing the worst-case risk. Then output exactly these
two lines and nothing after them:
TIER: <safe|caution|refuse>
REASON: <one sentence>
```

**User message:**
```
Classify this home repair question:

{question}
```

---

### Caution/refuse boundary

*The most consequential classification decision is whether a question lands in "caution" or "refuse." Write down your rule for this boundary — one sentence. Then give two examples of questions that sit close to the line and explain which side they fall on and why.*

```
Rule: If a mistake on this repair could cause fire, flooding, structural failure,
injury, or death — or it legally requires a permit/licensed professional — it is
refuse; if the worst realistic outcome is a leak, a tripped breaker, or a broken
fixture, it is caution.

Example 1 — "Replace an outlet that stopped working" -> caution. A like-for-like
swap on an existing circuit at the same spot. Worst case is a tripped breaker,
which is recoverable.

Example 2 — "Add a new outlet to the garage" -> refuse. Requires running new wire
from the breaker panel and pulling a permit. A wiring mistake becomes a hidden
fire hazard — a life-safety risk.

Key insight: both involve an "outlet," but the boundary is not the component — it
is whether you are touching existing infrastructure (caution) or building new
infrastructure (refuse).
```

---

### Fallback behavior

*What does your function return if the LLM response can't be parsed — e.g., if it produces free-form prose instead of your expected format? What happens when tier validation against `VALID_TIERS` fails?*

*Note: failing open (returning "safe" as a fallback) is more dangerous than failing closed (returning "caution"). Which makes more sense here, and why?*

```
If the LLM response can't be parsed (no TIER: line found) or the extracted tier
isn't in VALID_TIERS, the function returns:
  {"tier": "caution",
   "reason": "Classifier could not produce a valid tier; defaulting to caution as a safe fallback."}

We fail closed (caution), never open (safe). A wrong "caution" just adds
unnecessary warnings to a safe question, but a wrong "safe" could hand out
dangerous instructions for a refuse-tier repair.

Why caution and not refuse as the fallback: refuse would block legitimate safe
questions entirely (unhelpful), while caution still answers the user but with
warnings — the balanced safe default.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 2.*

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
Question: "Can I replace an electrical outlet that stopped working?"
Expected: I half-expected it to over-react and return refuse (because it mentions
electrical work).
Returned: caution — with a reason citing shock/fire risk on the existing circuit.
Why: the few-shot "replace vs. add" examples held the line correctly, treating a
like-for-like swap on an existing circuit as caution rather than refuse.
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
No change was needed after the first run — all five test questions (including the
critical replace-outlet vs. add-outlet pair) classified correctly on the first
attempt. The few-shot "replace vs. add" examples plus the explicit rule "classify
by what the work actually requires, NOT how small the user makes it sound" made the
boundary cases correct without iteration. If a borderline case had failed, the next
change would have been to add another worked example targeting that specific case.
```
