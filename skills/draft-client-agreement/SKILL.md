---
name: draft-client-agreement
description: Drafts client agreements (MSA + one or more service SOWs) via Agree.com. Triggered when a deal is Closed Won. Pulls the deal AND the client's Notion proposal, runs a guided intake to confirm services/tiers/tracks/locations, reconciles computed pricing against the proposal, assembles a modular envelope (MSA + selected SOWs + Schedule A + one master signature), pre-fills fields, and returns the envelope URL for Maxx to review and send.
---

# Draft Client Agreement Skill (v2 — multi-service)

Automates the post-close agreement step: Notion deal + proposal → guided intake →
pricing reconciliation → modular Agree.com envelope ready to send.

**Primary user:** Maxx (only Maxx has Agree.com access)
**Trigger:** Deal flips to Closed Won in Notion Sales Pipeline

## Trigger Phrases
- "draft agreement for [client]"
- "draft MSA for [client]"
- "send [client] to Agree.com"
- "client closed: [client]"
- `/draft-client-agreement [client]`

---

## What v2 changed (vs v1)
- **Five service models**, not one: Delivery, Retention, ezCater Catering, Advisory, Marketplace Launch. Any combination stacks under one MSA.
- **Guided intake** — pulls the client's Notion proposal, pre-fills every answer from it, and walks Maxx through structured one-question-at-a-time confirmations before building.
- **Pricing reconciliation** — computes fees from canon and diffs against the proposal; mismatches must be resolved before the envelope is built.
- **Modular assembly** — MSA + selected SOW blocks + a consolidated Schedule A fee page + one master signature block.
- **Dynamic field assignment** — field positions are scanned at assembly time, never hardcoded (hardcoded positions break the moment SOW count varies).
- **Current pricing** — July 2026 Two-Track Standard; Loop removed; 5-location minimum.

Design detail lives in `templates/v2/00_BUILD-SPEC.md`. SOW drafts + shared
boilerplate live in `templates/v2/sows/`.

---

## Locked structural decisions (Maxx, Jul 22 2026)
1. **One master signature block** for the whole package (7 signer fields, position-independent).
2. **Schedule A** consolidated fee page — one combined total across all SOWs.
3. **Term centralized in the MSA** — SOWs reference it, don't repeat it.
4. **Chosen track baked in** — signed DM/Catering SOW shows only the selected track.
5. **Launch = one envelope**, one-time milestones + recurring-at-go-live together.

---

## Pricing Canon (July 2026 — source of truth: Notion Scope & Pricing Hub `2bdd3ff0-18e7-80ad-9df5-000bfbb5262a`)

**Cross-cutting:** 5-location minimum, every model. Base fee covers the first 5
locations. 6-month initial term, month-to-month after, 60-day notice. Upfront
ACH/card. Adding a module mid-term does not reset the clock; new module prorated.
Exclusions: platform commissions, ad spend (pass-through), third-party software,
photo/video production, physical collateral. Loop is discontinued.

### 1. Delivery Marketplaces (two-track)
- **Track A (Flat):** `$2,750` base (first 5) + `$175`/location beyond 5.
- **Track B (Performance):** `$1,750` base (first 5) + `$100`/location beyond 5, + 10% of net-payout dollars above (baseline + 5%), summed across UE/DD/GH, same-store basis.
- **Track B gate:** ≥ $125K/mo top-line delivery (~$1.5M/yr), or ≥ $75K/mo net payout if shared. Below the floor → Track A only.
- Menu updates $50/hr; design $75/hr (not billed monthly).

```
DM Track A monthly = 2750 + 175 × max(locs − 5, 0)
DM Track B monthly = 1750 + 100 × max(locs − 5, 0)   (+ performance kicker, trued up monthly)
```

### 2. Retention Marketing (flat only)
- Basic `$1,000` / Standard `$1,750` / Pro `$2,500` per month.
- Setup `$3,500` one-time — **waived on 6-month commitment**.
- SMS add-on `$500`/mo + `$500` activation (waived on 6-mo add-on commit). +$200/extra SMS campaign, +$375/extra email campaign.

### 3. ezCater Catering (two-track)
- **Track A (Flat):** `$1,250` base (first 5) + `$150`/loc 6–10 + `$75`/loc 11+. 50+ = custom.
- **Track B (Performance):** `$750` base (first 5) + `$100`/loc 6–10 + `$50`/loc 11+, + 10% of net-payout above (baseline + 5%).
- **Track B gate:** ≥ $65K/mo ezCater sales (~$780K/yr), or ≥ $50K/mo payout if shared.

### 4. Advisory (flat, **add-on only — never standalone**)
- Advisory-Lite `$2,500`/mo · Fractional Head of Growth `$5,000`/mo.
- **Must attach to ≥1 operational SOW.** Refuse an Advisory-only envelope.

### 5. Marketplace Launch (one-time milestone + recurring at go-live)
- `$12,000` one-time (first 5) + `$500`/location beyond 5. Milestones: 40% signing / 30% build-complete / 30% go-live.
- Ongoing management starts at go-live, DM Track A ($2,750 base). Not waivable.
- 6-mo ongoing clock starts at go-live. Optional: 12-mo commit at signing → $2,000 credit.
- Track A only at signing (no baseline yet).

---

## Step 0: Load context (required)
Read in parallel before anything else:
- `Obsidian Vault/00-home/hot.md`
- `Obsidian Vault/spice/_spice-moc.md`

---

## Step 1: Pull the deal AND the proposal from Notion

### 1a. Deal — Sales Pipeline DB (`1c0d3ff0-18e7-805b-ba76-000b04cc35c4`)
Require **Closed Won** before proceeding (warn but don't block on explicit override).
Extract: client brand name, Service(s), Locations, Decision Maker (client signer),
Email, Close Date (Effective Date), Notes / Billing Notes (custom pricing).

### 1b. Proposal — the reconciliation source (do NOT skip)
Find the client's proposal. Two places:
- The deal page body often contains the full proposal (as with Kitava).
- Otherwise search Notion for `"[Client] proposal"` and the **Scope & Pricing Hub** for the client's scoped doc.

From the proposal, extract what was actually offered and accepted: which services,
which retention tier, which track (A/B), location count, SMS yes/no, advisory tier,
launch options, and every dollar figure. **These become the pre-filled answers and
the numbers the computed pricing is checked against.** If no proposal is found, say
so and run intake from the deal record only (flag that there's nothing to reconcile
against).

---

## Step 2: Guided intake (structured, one question at a time)

Use `AskUserQuestion` for each decision. Pre-fill every question from the proposal
and mark the proposal's value `(from proposal)` as the first option. Ask only the
questions relevant to the selected services.

1. **Services** (multi-select) — pre-checked from the proposal. Options: Delivery, Retention, Catering, Advisory, Launch.
   - Guard: if **Advisory** is selected with no operational service → block and re-ask (Advisory is add-on only).
2. **Locations** — pre-filled. Guard: if `< 5`, surface the 5-location minimum and confirm the intended handling before proceeding.
3. **Delivery track** (only if Delivery selected) — Track A or Track B.
   - If Track B: require the trailing delivery sales figure; auto-check the gate (≥$125K/mo or ≥$75K/mo payout). Below floor → Track A only, explain why.
4. **Catering track** (only if Catering selected) — same gate logic against the catering floor (≥$65K/mo or ≥$50K/mo payout).
5. **Retention** (only if Retention selected) — tier (Basic/Standard/Pro) + SMS add-on yes/no.
6. **Advisory** (only if Advisory selected) — Advisory-Lite or Head of Growth.
7. **Launch** (only if Launch selected) — location count + optional 12-month-commit credit.
8. **Client signer** — pre-filled from Decision Maker + Email; confirm.

Every confirmed answer that diverges from the proposal is noted for Step 3.

---

## Step 3: Compute pricing, reconcile, checkpoint

1. Compute each selected service's fees from the canon above.
2. Build **Schedule A** — a rollup of all recurring monthly fees + one-time fees (Retention setup, SMS activation, Launch milestones) + combined monthly total.
3. **Reconcile against the proposal.** Diff every computed figure vs the proposal's figure. If anything differs (e.g. proposal quoted old DM pricing, or a tier changed), surface the diff explicitly and ask Maxx to resolve before building. Never silently override the proposal or silently follow it — show the delta.
4. Show the confirmation checkpoint and wait for explicit **"go"**:

```
## Ready to send to Agree.com

Client: [name]
Services: [list]
Locations: [N]

Schedule A — Fees
  [Service]  [track/tier]      $[X]/mo
  [Service]  [track/tier]      $[Y]/mo
  One-time:  [setup/milestone] $[Z]
  ────────────────────────────────────
  Combined monthly total:      $[T]/mo

Reconciliation vs proposal: [MATCHES / diffs listed]
Term: 6 months initial, then month-to-month
Effective Date: [handling]
Client signer: [POC] <[email]>

Reply "go" to open Agree.com.
```

Per CLAUDE.md: never open the browser or send external content without confirmation.

---

## Step 4: Assemble the envelope in Agree.com

Agree.com is browser-only (Chrome MCP `mcp__claude-in-chrome__*`). **Never use
computer-use tools.** Load the Chrome tools via ToolSearch first (see the
claude-in-chrome batch in the connector instructions).

### 4a. Create the base envelope
Navigate directly to the base combined template and click **Use template** (do NOT
use the "+ Agreement" browse modal). Capture the new `/docs/[uuid]` URL from
`tabs_context_mcp`.

```javascript
navigate('https://secure.agree.com/templates/1abce0bb-1ab3-4183-8fa9-d0c0bf44e7ef')
// then:
(async () => { await new Promise(r=>setTimeout(r,3000));
  const b = Array.from(document.querySelectorAll('button')).find(b=>b.textContent.includes('Use template'));
  if (b) b.click(); })()
```

> **Build dependency (until the certified per-service templates exist):** the base
> template is still the DM-only combined doc. For a stacked deal, after creating the
> envelope, inject the selected SOW block sets from the block library (see
> "Modular assembly" below) before assigning fields. For a Delivery-only deal on
> current pricing, the base template works once its DM SOW is updated to the
> Two-Track Standard.

### 4b. Modular assembly (stacked deals)
Assemble the document as: **MSA blocks + [each selected SOW block set, page-break
separated] + Schedule A block + master signature block.** Use the same
`localStorage` + `editor.replaceBlocks()` + `saveRevision()` mechanism documented
in "Injection Method". Fees are written as pre-filled text (not signer fields).

Block library (certified sources — populate as they're built):
| Block set | Source template | Status |
|---|---|---|
| MSA (governing, term centralized) | `b7525a86-641a-4e16-b6f3-93dde05a3240` | live (needs term-centralization edit) |
| SOW — Delivery (two-track) | TBD certify from `templates/v2/sows/SOW_1_DeliveryMarketplaces.md` | to build |
| SOW — Retention | TBD certify from `SOW_2_Retention.md` | to build |
| SOW — Catering | TBD certify from `SOW_3_Catering.md` | to build |
| SOW — Advisory | TBD certify from `SOW_4_Advisory.md` | to build |
| SOW — Launch | TBD certify from `SOW_5_MarketplaceLaunch.md` | to build |
| Schedule A (fee rollup) | TBD | to build |
| Master signature block | TBD | to build |

### 4c. Rename the envelope
Title format: `Spice <> [Client] | [Service Model]`. Service model = the services
joined with ` + ` (e.g. `Delivery Marketplaces + Retention + Advisory`).

> Note: Agree.com sanitizes the `<>` on some saves, leaving `[Client] | [Service]`.
> Harmless. Re-apply the title before sending if it matters.

```javascript
(async () => { await new Promise(r=>setTimeout(r,2000));
  const t = Array.from(document.querySelectorAll('[contenteditable="true"]'))
    .find(el => /DM Agreement|Copy|Spice|Kitava/.test(el.textContent));
  if (t){ t.focus(); document.execCommand('selectAll',false,null);
    document.execCommand('insertText',false,'Spice <> [CLIENT] | [SERVICE MODEL]'); t.blur(); }
})()
```

### 4d. Add the client signer as second party
Spice (Maxx) is already present. Open the party dropdown (the "Freedman" button),
try "Add an existing contact" and search by first name; if not found, "Create new
contact" (inputs[1] = full name, inputs[2] = email) and Save contact.

```javascript
(async () => {
  const f = Array.from(document.querySelectorAll('button')).find(b=>b.textContent.includes('Freedman'));
  if (f) f.click(); await new Promise(r=>setTimeout(r,600));
  const addEx = Array.from(document.querySelectorAll('*')).find(el=>el.children.length<3 && el.textContent.trim()==='Add an existing contact');
  if (addEx) addEx.click(); await new Promise(r=>setTimeout(r,800));
  const s = document.querySelector('input[placeholder="Existing contacts"]');
  if (s){ s.focus(); document.execCommand('insertText',false,'[CLIENT FIRST NAME]'); }
  await new Promise(r=>setTimeout(r,600));
  return Array.from(document.querySelectorAll('label')).map(l=>l.textContent.trim());
})()
// If not found:
(async () => {
  const c = Array.from(document.querySelectorAll('*')).find(el=>el.children.length<3 && el.textContent.trim()==='Create new contact');
  if (c) c.click(); await new Promise(r=>setTimeout(r,800));
  const i = Array.from(document.querySelectorAll('input'));
  if (i[1]){ i[1].focus(); document.execCommand('insertText',false,'[POC FULL NAME]'); }
  if (i[2]){ i[2].focus(); document.execCommand('insertText',false,'[POC EMAIL]'); }
  await new Promise(r=>setTimeout(r,300));
  const sv = Array.from(document.querySelectorAll('button')).find(b=>b.textContent.trim()==='Save contact');
  if (sv) sv.click(); await new Promise(r=>setTimeout(r,1500));
})()
```

### 4e. Assign signer fields — DYNAMIC SCAN (do not hardcode positions)

Recipient IDs are envelope-specific. Fetch them, then scan the doc for `field`
nodes and assign by **role/order**, not absolute position. With term + signature
centralized, the field set is fixed at **7**: effective_date (Spice),
company_name + address (Client), and the master signature set (spice_signature +
spice_date = Spice; client_signature + client_name + client_title + client_date =
Client).

```javascript
// i) fetch recipients (party-me = Maxx, party-0 = client)
(async () => { await new Promise(r=>setTimeout(r,2000));
  const el=document.querySelector('.tiptap.ProseMirror');
  const fk=Object.keys(el).find(k=>k.startsWith('__reactFiber')); let fb=el[fk],d=0;
  while(fb&&d<30){ if(fb.memoizedProps?.editor)break; fb=fb.return; d++; }
  let p=fb,rc=null; d=0;
  while(p&&d<25){ if(p.memoizedProps?.recipients){rc=p.memoizedProps.recipients;break;} p=p.return; d++; }
  return rc.map(r=>({id:r.id,role:r.role,color:r.color,email:r.contact?.email||r.user?.email}));
})()

// ii) scan every field node, assign by order. The doc order of the 7 fields is:
//     [effective_date, company_name, address, spice_sig, client_sig, client_name, client_title, spice_date, client_date]
//     — VERIFY on a fresh envelope with the scan below, then map by index, not literal pos.
(async () => {
  const MAXX_ID='[from step i, color party-me]', CLIENT_ID='[from step i, color party-0]';
  const el=document.querySelector('.tiptap.ProseMirror');
  const fk=Object.keys(el).find(k=>k.startsWith('__reactFiber')); let fb=el[fk],d=0,bn=null;
  while(fb&&d<30){ if(fb.memoizedProps?.editor){bn=fb.memoizedProps.editor;break;} fb=fb.return; d++; }
  const tt=bn._tiptapEditor;
  let p=fb,save=null; d=0;
  while(p&&d<25){ if(p.memoizedProps?.saveRevision){save=p.memoizedProps.saveRevision;break;} p=p.return; d++; }

  // collect fields in document order
  const fields=[]; tt.view.state.doc.descendants((n,pos)=>{ if(n.type.name==='field') fields.push({pos,attrs:n.attrs}); });
  // role map by the field's own type/name attr where available; else by known order
  const role = f => {
    const t=(f.attrs.field_type||f.attrs.type||'').toLowerCase();
    const name=(f.attrs.name||'').toLowerCase();
    if(name.includes('effective')||name.includes('spice_date')||name.includes('spice_sig')) return MAXX_ID;
    if(name) return CLIENT_ID; // company/address/client_*
    return null; // unknown → resolve by order fallback
  };
  const { tr }=tt.view.state; let updated=0;
  fields.forEach(f=>{ const rid=role(f); if(rid&&f.attrs.recipient_id!==rid){ tr.setNodeMarkup(f.pos,null,{...f.attrs,recipient_id:rid}); updated++; } });
  tt.view.dispatch(tr); await new Promise(r=>setTimeout(r,800)); save(); await new Promise(r=>setTimeout(r,3000));

  const me=document.querySelectorAll('[class*="bg-party-me"]').length;
  const c0=document.querySelectorAll('[class*="bg-party-0"]').length;
  const none=document.querySelectorAll('[class*="bg-party-none"]').length;
  return { totalFields:fields.length, updated, partyNone:none, partyMe:me, party0:c0 };
})()
```

**Success:** `partyNone: 0`. For the centralized single-signature layout the target
is `partyMe: 3` (effective_date + spice_sig + spice_date) and `party0: 4`
(company + address + client_sig + client_name + client_title + client_date = 5 —
recount on the real template and record here once built). **Reload the envelope and
re-check** — if `partyNone > 0` after reload, `saveRevision()` didn't take; re-run.

> If a field's `name`/`type` attr isn't reliable, fall back to assigning by the
> verified document-order index. Always confirm on a fresh envelope and record the
> confirmed order in `templates/v2/00_BUILD-SPEC.md`.

### 4f. Send — MANUAL (classifier blocks the automated send)

**Finding (Jul 2026):** the Claude Code auto-mode safety classifier **blocks**
injected JS that fires the Send / "Send now" handlers (irreversible outbound to a
client). Do not loop-retry it. Instead:
1. Stage it: click the **Send** button to open the send modal (this is allowed).
2. Verify field assignment is clean (`partyNone: 0`).
3. **Hand off to Maxx**: tell him to click **"Send via email"** → **"Send now"** in the open Chrome tab. That emails the client the signing link.

```javascript
// staging only — opens the modal, sends nothing
(async () => {
  const s=Array.from(document.querySelectorAll('button')).find(b=>b.textContent.trim()==='Send');
  if (s){ s.click(); await new Promise(r=>setTimeout(r,1500)); }
  return { modalOpen: !!document.querySelector('[role="dialog"]') };
})()
```

To confirm afterward, read status (read-only) — a sent envelope shows `sent`
badges and drops the draft state.

---

## Step 5: Update Notion (after Maxx confirms sent)
Sales Pipeline DB (`1c0d3ff0-18e7-805b-ba76-000b04cc35c4`):
- **Deal stage** → `Agreement Sent`
- **Notes** → append: `Agree.com [services] sent [DATE]. Signer: [POC] ([email]). Envelope: [URL]`
- **Last contact date** → today

Requires explicit Maxx confirmation per CLAUDE.md. Show the proposed change first.

---

## Step 6: Output
```
## Agreement sent for [Client]

Agree.com envelope: https://secure.agree.com/docs/[uuid]
Notion deal → Deal stage "Agreement Sent"

Services: [list]
Schedule A total: $[T]/mo (+ one-time $[Z] if any)
Reconciliation vs proposal: [MATCHES / resolved diffs]
Term: 6 months initial, then month-to-month
Client signer: [POC] <[email]>

Emailed to [email]. You'll be notified when they sign; countersign (Effective Date) when ready.
```

---

## Critical Agree.com technical findings (unchanged — these work)
- **Save mechanism:** `saveRevision = () => r.current?.save()` — React fiber prop ~depth 11 above `.tiptap.ProseMirror`. The ONLY way to persist. `replaceBlocks()` alone does not save.
- **BlockNote vs TipTap:** the fiber `editor` is a BlockNote wrapper; the real ProseMirror is `editor._tiptapEditor`.
- **No auto-save on typing.** **localStorage is shared** across `secure.agree.com` tabs (use for block transfer). **Clipboard does NOT survive navigation.**
- **Recipient IDs are envelope-specific** — fetch per envelope from `memoizedProps.recipients`; not the same as contact IDs.
- **Cloudflare 403** after intensive JS sessions — waits out in ~10 min.
- **Title sanitization** — `<>` may be stripped on save; re-apply before send if needed.
- **Send is classifier-gated** — automate up to opening the modal; Maxx clicks send.

---

## Injection Method (rebuild a template / assemble blocks)
Same three-tab pattern as v1: extract block sets to `localStorage` from each source
template, then on the target envelope `editor.replaceBlocks(editor.document,
[...msa, pageBreak, ...sow1, pageBreak, ...sow2, scheduleA, signature])` and call
`saveRevision()`. Page-break block:
```javascript
{ id:'pb', type:'page-break', props:{textColor:'default',backgroundColor:'default',textAlignment:'left'}, content:[], children:[] }
```
`replaceBlocks()` without `saveRevision()` will not persist.

---

## Notion Database References
| Database | ID | Use |
|---|---|---|
| Sales Pipeline | `1c0d3ff0-18e7-805b-ba76-000b04cc35c4` | Deal data + proposal body |
| Scope & Pricing Hub | `2bdd3ff0-18e7-80ad-9df5-000bfbb5262a` | Pricing canon source of truth |
| Clients (onboarding) | `1c8d3ff0-18e7-80e9-8381-000b4448cb87` | Post-signature onboarding |

## Team Signer
Maxx Freedman — CEO / Spice signer — maxx@spicedigital.co

## Related Skills
- **post-sale-proposal** — runs before this; writes the proposal this skill reconciles against.
- **client-onboarding-v2** — picks up after signature (Stripe price IDs, onboarding DB).
- **contractor-agreement** — team contractor agreements (not client).

---

## Build status / open items (v2)
- [x] Pricing canon updated to July 2026 Two-Track Standard (5 models).
- [x] Guided intake + proposal reconciliation designed into the flow.
- [x] Dynamic field scan replaces hardcoded positions.
- [x] Structural decisions locked (signature, Schedule A, term, track, launch).
- [ ] **Certify per-service SOW templates in Agree.com** from `templates/v2/sows/` (gated on legal review). Populate the 4b block-library table with real template IDs + confirmed field order.
- [ ] Update the MSA source to centralize term; build Schedule A + master signature blocks.
- [ ] Verify Agree.com billing widget carries one-time + recurring together (Launch dependency).
- [ ] Retire the DM-only base template (`1abce0bb…`) once the modular library is live.
- [ ] E2E test: single service, stacked recurring (DM+Retention+Advisory), Launch (milestone+recurring).
