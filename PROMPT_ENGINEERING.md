Without this example, models occasionally wrapped output in markdown code fences (` ```json ... ``` `) or added explanatory text before/after the JSON, breaking automated parsing. The explicit "respond ONLY with a valid JSON object (no markdown, no extra text)" instruction plus the example significantly reduced malformed output — though a defensive `strip("`")` cleanup step remains in the code as a safeguard, since model output formatting isn't 100% guaranteed across providers.

**Constrained category/urgency values**

Categories are restricted to a fixed list (`Technical`, `Billing`, `Account`, `Feature Request`, `Other`) rather than open-ended classification. This keeps downstream logic predictable (e.g., routing tickets by category) and avoids category sprawl (e.g., the model inventing "Security Issue" as a category for every encryption-related ticket).

---

## 2. Response Generation Prompt + RAG Integration

### Goal
Generate a professional draft reply that reflects actual company policy (response timeframes, escalation procedures) rather than generic, policy-agnostic boilerplate.

### Design decisions

**Context injection structure**

The retrieved RAG documents are placed *before* the ticket details, with an explicit instruction at the end: "Using the policy information above where relevant, write the reply." This ordering — context first, task instruction last — proved more effective than interleaving policy text with the ticket, since it gives the model the full picture before it's asked to act.

**System prompt update for RAG awareness**

The original response prompt (Phase 1, no RAG) only instructed the model to "acknowledge their issue and explain the next step." After adding RAG (Phase 2), the system prompt was updated to explicitly say: *"If the policy information includes specific procedures, timelines, or escalation paths relevant to this ticket, incorporate them naturally into your reply."* Without this addition, the model sometimes ignored the retrieved context entirely, even when relevant policy text was provided — simply having the context available wasn't enough; the model needed to be told to use it.

---

## 3. Edge Case Testing & Findings

Ten test cases were designed to stress-test classification accuracy, RAG retrieval quality, and response appropriateness across realistic and adversarial scenarios.

| # | Test Case | Result |
|---|---|---|
| 1 | Billing — duplicate charge | Correctly classified as Billing; retrieved `billing_policy.txt`; referenced 5-7 business day refund timeline |
| 2 | Security/encryption, High urgency | Correctly classified as Technical/High; retrieved `encryption_policy.txt` |
| 3 | Feature request (export to Excel) | Correctly classified as Feature Request, Low/Medium urgency |
| 4 | Integration failure after update | Correctly classified as Technical/Medium; retrieved `integration_support.txt` |
| 5 | Platform-wide outage, High urgency | Correctly classified as Technical/High; retrieved `outage_response.txt`; referenced 15-minute acknowledgment |
| 6 | Vague ticket ("Help" / "It's not working") | Classified as Technical/Medium without hallucinating specifics; reply asked clarifying questions (error messages, timing, recent changes) |
| 7 | Account email change request | Classified as Account; exposed a knowledge base gap (no account-specific doc existed at the time — see Finding 1 below) |
| 8 | Mixed signals (billing error caused by a system bug) | Classified as Billing (primary symptom) while reply acknowledged the technical root cause and referenced escalation to "Billing Engineering team" — a specific instruction pulled via RAG from `billing_policy.txt` despite the query not mentioning "database migration" directly |
| 9 | Non-English ticket (French) | Classified as Account; RAG retrieval was weaker (pulled `billing_policy.txt` and `integration_support.txt`, neither a strong match); reply responded in French, matching the input language |
| 10 | Long ticket with multiple unrelated issues | Classified as "Other" rather than forcing a single category; reply explicitly asked the customer to separate each issue — the realistic support response rather than guessing |

### Finding 1: Knowledge base gap (Cases 7 & 9)

Neither test case had a strong RAG match because no knowledge base document covered account access, password resets, or login issues. **Fix applied**: added `data/knowledge_base/account_management.txt`, covering identity verification, password reset timelines (1-hour link expiry), and email change procedures (1 business day, dual-address verification). This is a direct example of using test results to iteratively improve the RAG knowledge base — testing surfaced a real gap that wasn't apparent from the original ticket sample alone.

### Finding 2: Category ambiguity is sometimes irreducible (Case 8)

"Billing error caused by system bug" has no single correct category — both Billing and Technical are defensible. The model's choice (Billing, with technical context acknowledged in the reply) is reasonable, but this highlights a limitation of single-label classification for tickets spanning multiple domains. A production system might support multi-label classification or a secondary "related category" field.

### Finding 3: Language consistency is undefined behavior (Case 9)

The model responded in French to a French ticket without being instructed to do so. This could be a feature (better customer experience) or a problem (support agents reviewing drafts may not read French), depending on the business context. **Not yet resolved** — listed in README's Future Improvements. A fix would be adding an explicit instruction to `RESPONSE_SYSTEM_PROMPT`, either enforcing English output or explicitly supporting multilingual replies as a deliberate feature.

---

## 4. Summary

The most impactful prompt engineering changes were:
1. Adding a worked JSON example to enforce structured output (Phase 1)
2. Explicitly instructing the model to use injected RAG context, not just providing it (Phase 2)
3. Using edge-case testing to find and fix a knowledge base gap (account management) rather than assuming the initial knowledge base was complete

These reflect an iterative process: each phase's prompts were shaped by observed failures in the previous phase's output, not designed perfectly upfront.