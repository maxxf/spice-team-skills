---
name: monthly-update
description: Monthly Spice→Spicy investor update — punchy, structured, honest. Trigger on "monthly update", "investor update", "monthly investor letter", "update the investors", "send the monthly update", "write this month's update", or a month name + "investor update". Auto-pulls live financials (Mercury, Stripe, Notion) and mines the vault + running investor log for the narrative sections, then drafts TWO variants (private + public-safe) for review. Never sends. Distinct from /board-letter, which is the quarterly deep narrative — this is the monthly scorecard + asks in a beehiiv/Tyler-Denk register.
---

# Monthly Update (/monthly-update)

Write the monthly Spice→Spicy investor update: a short, honest, structured letter to advisors, partners, and current/prospective investors. One update tells one story — a bootstrapped services business (Spice) throwing off cash that funds the software bet (Spicy).

This is NOT a report or a dashboard. It's a founder's letter in the mold of a beehiiv/Big Desk Energy monthly update: TL;DR scorecard, candid narrative, direct asks, a real win, a real failure.

## Relationship to /board-letter

- **/board-letter** = quarterly, long-form narrative, deep client-by-client + strategic assessment. The quarter's accountability doc.
- **/monthly-update** = monthly, punchy scorecard + asks + one win + one failure. The month's heartbeat.

They share data sources but never overlap in output. If a quarter just closed, the board-letter is the deep version; the monthly is still the short beat.

## Audience & Framing

Bootstrapped. No outside capital, no board that requires this. The audience is advisors, partners, and anyone Maxx might bring on as an investor. Framing consequence: **being bootstrapped is the credibility, not a weakness** — no VC net means no incentive to spin. Lean into that in the open.

## Workflow

### 1. Resolve the month
Default to the most recently completed calendar month based on today's date. If mid-month and the user asks for the current month, label it partial ("through July 14") and adjust tense. Take an explicit month if the user names one.

### 2. Auto-pull financials (Spice's OWN revenue — never client GMV)
CRITICAL: report the fees Spice bills its clients, NOT the clients' delivery-platform sales. If a number is client-side GMV, it is reference-only and never appears as Spice revenue.

**Stripe** (search "stripe" tools):
- MRR at prior month-end vs this month-end (active subscriptions) → MoM %.
- Total revenue invoiced this month.
- Active paying client count, prior vs current month-end → net adds/churns (name them).
- Top-3 clients by revenue and combined % of month revenue (concentration).

**P&L reconciler — the financial spine** (run /revenue-reconciliation for the month, or reuse a fresh run):
- This is the primary financial source. It reconciles the Google Sheets P&L against Mercury cash and produces the scannable P&L breakdown blocks (revenue → COGS → contribution margin → operating expenses → operating income, plus tax reserve and owner's-draw waterfalls).
- Pull the P&L breakdown block verbatim for the **P&L snapshot** section (private variant).
- Compute **operating margin %** = operating income ÷ revenue, MoM vs prior month. Use this exact definition every month so the trend is comparable; state the definition once in a footnote.
- If the P&L isn't updated for the month, flag it and fall back to prior month as an estimate.

**Mercury** (getCurrentDate FIRST, then getAccounts + listTransactions) — only if the reconciler didn't already cover it:
- Cash generated (inflow − outflow) for the month, for context in the P&L snapshot.
- Paginate fully; if truncated, cut the limit. Compute aggregates programmatically and double-check the math.

**Notion** (search "notion" tools):
- Active managed-client count, onboards/churns if tracked.
- Pipeline value + deals closed-won this month if a pipeline DB is queryable.
- If the Notion DBs can't be queried directly, reconstruct from the most recent /weekly-prep output and FLAG it as reconstructed, not a live query.

### 3. Vault-mine the narrative
Read `00-home/hot.md`, `00-home/top-of-mind.md`, the month's `raw/meetings/`, and recent Slack to infer: Spicy product progress, the month's wins, one honest failure + its learning, and candidate asks. Cite the raw source for anything durable.

### 4. Merge the running investor log
Read `raw/captures/investor-log.md` (the note Maxx drops bullets into all month). Compile its entries into the draft; use the vault-mine to fill gaps the log missed. After drafting, append a dated "compiled into {month} update" marker so entries aren't reused next month.

### 5. Draft BOTH variants
Route all prose through the humanizer skill and Maxx's voice guide (`brand/content-skill-graph/voice/brand-voice.md`). Apply the Voice Rules below.

- **Private** → `workspace/monthly-update-{YYYY-MM}-private.md`: real dollar figures, client names, concentration risk, candid failure, specific asks.
- **Public-safe** → `workspace/monthly-update-{YYYY-MM}-public.md`: growth in %/multiples not raw $, clients anonymized or aggregated, failure softened to the lesson, narrative-forward. The version that could go to a hosted page later.

### 6. Output for review — NEVER send
Write both drafts, surface the private one in chat, note the public one exists. Sending is Maxx's call (email/publish require explicit approval per charter). Do not email, post, or publish.

## Template (fixed section order)

1. **Cold open** — one human line: a milestone, a life update, or a sharp contradiction hook. Sets the register before business content.
2. **TL;DR scorecard** — the 5-metric spine: MRR (MoM %), client count (net adds/churns), monthly revenue, operating margin % (MoM), one Spicy-progress line. Exact numbers live HERE.
3. **P&L snapshot** — the reconciler's breakdown block (revenue → contribution margin → operating income, tax reserve, cash context). Private variant only; public shows margin % + trend, not line items.
4. **Spice — the cash engine** — client portfolio health, revenue trend, notable wins/losses, concentration honesty. Round numbers in prose.
5. **Spicy — the bet** — product milestones, what shipped, what's next, the software-eating-services thesis update.
6. **Direct asks** — 1–3 concrete, mutual-benefit requests (intros, hires, design partners). Stated flat, no apology.
7. **Win of the month** — the single best moment.
8. **Failure & learning** — one honest miss + the takeaway. Non-negotiable; it's what makes the update trusted.
9. **Close** — what next month hinges on. Optional forward metric.

## Voice Rules (borrowed mechanics — Maxx's voice still governs)

These are register moves layered on top of the voice guide + humanizer. Do not turn Maxx into someone else; borrow the mechanics.

1. **Honesty as the opener, not the caveat.** Bad news goes at the top of a section, never buried after the spin.
2. **Earn the flex by undercutting it first.** Self-deprecate, then state the win plainly. Confidence reads as earned.
3. **Personal stakes on the table.** Bootstrapped = the chip on the shoulder. No VC net is a feature of the story — say it.
4. **Round in prose, exact in the scorecard.** "~$9K booked," "roughly breakeven," "nearly $290K." Decimals live only in the TL;DR block.
5. **Contradiction hook to open.** Tension, then resolve. Beats a warm-up sentence.
6. **Parenthetical asides** — thinking-aloud-to-a-friend texture. One or two per update, not more.
7. **Asks stated flat, framed as mutual, zero apology.**

Hard bans (voice guide + humanizer): no AI slurry (delve, landscape, "it's worth noting"), no precision theater in the narrative, no corporate-report stiffness. It's a letter, not a memo.

## Safety

- Never auto-send or publish. Drafts only.
- Never report client GMV as Spice revenue.
- Flag any reconstructed (non-live-query) figure so Maxx knows what to verify.
- Public-safe variant must not leak client names or raw dollar figures.
