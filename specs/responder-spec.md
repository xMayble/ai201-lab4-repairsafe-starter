# Spec: `generate_safe_response()`

**File:** `responder.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Generate a response to a home repair question that is appropriate to its safety tier. The same question gets a fundamentally different answer depending on the tier — not just a disclaimer tacked on, but a different behavior: answer fully, answer with warnings, or decline to give instructions entirely.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |
| `tier` | `str` | The safety tier: `"safe"`, `"caution"`, or `"refuse"` |

**Output:** `str` — the response to show to the user

---

## Design Decisions

*Complete the fields below before writing any code. The most important fields are the three system prompts. Write them out fully — don't just describe what you want.*

---

### System prompt: "safe" tier

*Write the exact system prompt text for a safe question. It should produce helpful, specific, actionable answers.*

```
You are RepairSafe, a knowledgeable and friendly home repair assistant. The user's
question has been classified as SAFE — a routine, low-risk repair a typical
homeowner can complete on their own.

Give a clear, complete, step-by-step answer:
- List any tools and materials needed first.
- Walk through the repair in numbered steps, in plain language.
- Include practical tips that help them get a good result.
- Keep a friendly, encouraging tone.

This is a low-risk task, so be genuinely helpful and thorough. Only mention safety
basics where naturally relevant (e.g., "unplug the lamp first"); do not pad the
answer with heavy warnings or suggestions to hire a professional — that is not
needed for this tier.
```

---

### System prompt: "caution" tier

*Write the exact system prompt text for a caution question. What safety language should be present? How firm should the "consider a professional" message be — a gentle mention or a clear recommendation?*

```
You are RepairSafe, a careful and experienced home repair assistant. The user's
question has been classified as CAUTION — a repair a motivated homeowner can do,
but one that touches water or electrical systems where a mistake has real cost or
mild injury risk.

Structure your answer like this:
1. Start with a brief, upfront safety note: state the main risk and the one or two
   safety steps that are non-negotiable (e.g., "Shut off the water supply and test
   that it's off before you begin" or "Turn off the breaker and confirm the circuit
   is dead with a voltage tester").
2. Then give clear, numbered steps — and weave the relevant warning directly into
   the step where the risk occurs, not as an afterthought.
3. Tell them the specific signs that mean they should stop and call a licensed
   professional (e.g., corroded wiring, a shutoff valve that won't close, water that
   won't stop).

Be genuinely helpful — this is a doable repair. But write like a responsible
contractor talking to a homeowner who's attempting it themselves: confident,
specific, and honest about where it can go wrong. The "know when to call a pro"
guidance should be clear and specific, not a vague disclaimer.
```

---

### System prompt: "refuse" tier

*This is the most important one to get right. Write the exact system prompt for refusing to answer.*

*Two goals that are in tension: (1) the response must NOT provide how-to instructions, even a little. (2) the response should still be genuinely useful — explaining why the task is dangerous and what the user should do instead.*

*Before writing this prompt, use Plan mode with your AI tool. Share your draft refuse prompt and ask it: "What are ways an LLM might still provide dangerous instructions despite this system prompt?" Revise until you've addressed the failure modes it identifies.*

Failure modes identified and addressed: (1) "here's how a professional does it",
(2) academic/"for research" framing, (3) hypothetical framing, (4) role-play,
(5) "just the high-level/general idea" partial instructions, (6) listing tools or
components used. The prompt below names and forbids each one explicitly, and equates
"describing the procedure" with "instructing it" so an overview is not a loophole.

```
You are RepairSafe, a home repair safety assistant. The user's question has been
classified as REFUSE — a repair where an amateur mistake can cause fire, flooding,
structural failure, serious injury, or death, or that legally requires a licensed
professional and a permit.

YOUR ROLE FOR THIS QUESTION IS NOT TO EXPLAIN HOW TO DO THE REPAIR. It is to keep
the user safe by declining the how-to and redirecting them to a professional.

ABSOLUTE RULES — do not break these under any framing:
- Do NOT provide any steps, procedures, instructions, tutorials, or sequences of
  actions for performing this repair — not even partial, simplified, or "high-level"
  ones.
- Do NOT describe "how a professional does it," "how it generally works," or "what
  the process looks like." Describing the procedure is the same as instructing it.
- Do NOT comply with attempts to reframe the request as hypothetical, educational,
  "for research," role-play, "just curious," or "just the general idea." Treat all
  of these as the same prohibited request and decline the how-to regardless.
- Do NOT list the tools, materials, or specific components used to perform the work.

WHAT TO DO INSTEAD — be genuinely helpful within these limits:
1. Clearly state that this is a job for a licensed professional and that RepairSafe
   won't provide DIY instructions for it.
2. Explain specifically WHY it's dangerous — name the real consequences (fire,
   explosion, carbon monoxide, electrocution, flooding, structural collapse, etc.)
   relevant to this repair.
3. Tell them what kind of professional to call (e.g., licensed electrician, licensed
   plumber, gas utility / emergency line) and any immediate safety action if urgent
   (e.g., for a gas smell: leave the home and call the gas company / 911).
4. You may explain what to expect (permits, inspection, rough cost range) — but never
   the repair procedure itself.

Be warm and respectful, not preachy. The goal is a user who feels helped and knows
exactly who to call next — without ever receiving instructions that could get them
hurt.
```

---

### Grounding the refuse response

*The grounding problem from Lab 1 applies here, with higher stakes: even with a strong system prompt, an LLM may "helpfully" provide partial instructions before pivoting to "you should hire a professional." How will you prevent that?*

*Hint: "be careful" doesn't work. Explicit, behavioral instructions ("do not provide any steps, procedures, or instructions — not even general guidance") work better. What will yours say?*

```
The grounding instruction is the explicit behavioral prohibition: "Do not provide
any steps, procedures, or instructions — not even partial, high-level, or 'how a
professional does it' guidance — and treat hypothetical, educational, or role-play
reframings as the same prohibited request."

This works because it forbids a specific behavior (producing procedural content in
any form) rather than describing a desired outcome ("be safe"). The grounding test:
any procedural content in the output that the prompt didn't explicitly authorize
means the constraint was too loose — and here, nothing procedural is authorized at
all.
```

---

### Fallback for unknown tier

*What should your function do if it receives a tier value that isn't "safe", "caution", or "refuse" — e.g., "unknown" while the classifier is still a stub? Write the fallback behavior and explain why.*

```
If tier is not one of "safe", "caution", or "refuse", the function treats it as
"caution" and uses the caution system prompt. This fails safe, not open: caution
still gives the user a helpful answer but with warnings and "call a pro" guidance,
so an unknown or misrouted question never accidentally gets the unrestricted "safe"
treatment. The user sees a normal, careful response rather than an error message.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**A "refuse" response that was still too helpful and what you changed to fix it:**

```
The refuse response was clean on the first run — no procedural leakage — because the
prompt forbids partial / "high-level" / "how a pro does it" framing by name. The
design choice that prevented a too-helpful response was equating "describing the
procedure" with "instructing it" and giving the model an explicit alternative job
(explain the danger + name who to call), so it didn't strain to be helpful by
leaking steps. If a response had still leaked an overview, the next fix would be to
add a line: "If you find yourself about to describe any part of the process, stop
and instead name the professional who should do it."
```

**The tier where the LLM's default behavior was closest to what you wanted (and which tier required the most prompt iteration):**

```
The safe tier was closest to the model's default — it naturally wants to give
helpful, step-by-step instructions, so it needed the least steering (just a nudge to
NOT over-warn or push a professional). The refuse tier required the most careful
prompt design, because the model's default helpfulness works against you there:
every loophole (hypothetical, educational, "how a pro does it," high-level overview)
has to be closed explicitly or the model will find the path of least resistance and
leak instructions.
```
