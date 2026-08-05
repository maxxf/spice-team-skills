---
name: client-email
description: The front door for any email going to a client. Turns one sentence of intent into a canon-shaped draft sitting in your own Gmail drafts, checked against the Spice client email standard before you ever see it. Trigger on "draft an email to [client]", "email [client] about", "send a recap to", "follow up with [contact]", "write [client] about last week", "draft a check-in", "chase [client] on", "client email", "recap email", "launch email", "onboarding email", or any request to write a message that a client will read. Also trigger when a teammate pastes a pile of notes and asks what to send.
---

# Client Email

One sentence in, one draft out. This skill exists so that following the client
email standard is faster than ignoring it.

The standard itself lives in two places and this file restates neither:

- `references/client-comms-style.md` is the canon. Skeleton, 150-word ceiling,
  the banned-pattern table, before and after pairs from real Spice threads.
  Read it before drafting.
- `references/client-comms-pass.md` is the checking procedure. Run it on the
  draft before surfacing anything.

If this file and the canon ever disagree, the canon wins and this file is the
bug.

**This skill never sends.** Not with permission, not on request, not when the
teammate says "just send it." Drafting only. A person hits send. See the hard
rule at the bottom.

---

## The speed contract

The bar is a good draft *in less time than typing the email yourself takes*.
Quality alone does not clear it. A skill that opens with four questions has
already lost, because the teammate goes back to composing in Gmail where nothing
checks anything.

So the contract is fixed:

**One sentence of intent, at most one clarifying question, then a draft.**

Never run an intake interview. Never ask for the numbers. Never ask what tone
they want. Never ask how long it should be. Never ask which format applies.
Everything in the next section is inferred, and a wrong inference is cheaper
than a right question, because the teammate is looking at an editable draft
either way.

### What you infer, never ask

| Thing | Where it comes from |
|---|---|
| Which client | Named in the sentence, or the active client context in the session |
| Recipients | The client's Notion Client Wiki contacts, then the last thread with that client. If still ambiguous, draft anyway with `To: [confirm]` at the top |
| Which of the five formats | The verb in the sentence. "recap" is a weekly recap, "launch" or "goes live" is a campaign launch, "invoice" or "past due" is an escalation, "welcome" or "kickoff" is onboarding, "monthly" or "YoY" is a monthly report |
| The numbers | The client's tracker, the most recent reporting run, the meeting notes. Pull them, do not request them |
| Tone | The prior thread with this contact plus the voice guide. Match how they already get written to |
| Sender name | The teammate running the skill |
| Reply or composed | Whether a live thread exists with that contact on that subject |
| Length | The canon decides this, not the teammate |

### The one question you are allowed

Spend it on the ask, and only on the ask.

If the intent sentence carries no request, no deadline, and no decision for the
client, ask exactly one question: **"What do you need back from them?"** Offer
"nothing, this is an FYI" as a real answer, because the canon and the pass both
treat a declared no-ask email as legitimate. If they pick that, set `no_ask:
true` when you run the pass so C2 is skipped on purpose rather than by
accident.

If the sentence already carries an ask, ask nothing. Draft.

Never spend the question on recipients, format, numbers, tone, or length. Those
are inferences, and a placeholder in the draft beats a round trip.

---

## Sequence

### 1. Read the canon and the pass

Both, every run. `references/client-comms-style.md` first, then
`references/client-comms-pass.md`. They are short and the whole skill is
downstream of them.

### 2. Load the client

In order, stopping when you have enough:

1. The client's Notion Client Wiki. Contacts, current campaigns, open issues,
   any voice notes on that account.
2. The last two or three threads with this contact. You are reading for tone and
   for what they already know, not for content to copy. If they got the LIC
   numbers on Tuesday, do not re-explain them Thursday.
3. The relevant artifact. Weekly reporting run, campaign tracker, diagnostic
   page, monthly update, meeting recap doc. This is the thing the email will
   point at.

If none of this is reachable in the session, say so in one line and draft from
what the teammate gave you. Do not stall on a missing wiki.

### 3. Draft to the ceiling, not to the context

This is the part that matters, and it is the opposite of the natural instinct.

You will usually be holding far more than 150 words of true, relevant material.
The instinct is to include it, because all of it is real and some of it took
work. Resist that. **The size of your context has no bearing on the length of
the email.** A weekly recap built off a 40-minute call and a full tracker pull
is the same six lines as one built off two Slack messages.

Concretely:

- Pick the one thing that needs a decision. It goes first, in the first three
  lines, ahead of whatever happened first chronologically.
- Pick the one or two numbers that prove the headline. Not the platform
  breakdown. One comparison each.
- Everything else goes behind the link. The email points at the analysis. The
  email is not the analysis.
- When you catch yourself writing a paragraph that is also in the linked doc,
  delete the paragraph and keep the link. That paragraph is where your overflow
  words are, every time.
- Write the line of specific human attention. One line only a person who looked
  at this account this week could have written. If you cannot find one, say so
  to the teammate rather than manufacturing something that could be true of any
  client. The pass will fail you on a manufactured one anyway, and the client
  can tell.

### 4. When there is nothing to link to

This comes up more than you would think. A teammate has real numbers and no
published artifact behind them.

Do not inline the detail to compensate. That is the exact failure the ceiling
exists to prevent, and it turns a missing doc into a 400-word email.

Say it plainly, and offer the fix:

> These numbers have nothing behind them. There is no published analysis for
> the July LIC pull. I can generate one with `/deploy` and link it, which takes
> a minute, or you can send this with the numbers unsourced. Which?

Then do what they say. If they want the artifact, generate and deploy it, put
the link in slot four, and carry on. If they want to send unsourced, draft it
and let the pass record the C3 failure on the receipt. The point is that the
teammate chose it.

### 5. Run the pass

Run `references/client-comms-pass.md` against the draft before the teammate
sees it. Follow its calling sequence exactly, including the stop condition: if
C1 hard-fails or C3 fails, report Lane A and skip Lane B.

This skill **generates** the draft rather than checking one a human wrote, so it
strips and reports rather than flagging only. The pass's own guidance on that
split is what governs.

Do not surface a draft you have not passed. Do not surface a receipt without the
draft.

### 6. Surface it

Output, in this order:

1. The draft, in full.
2. Where it landed. Gmail draft link, or a note that it is in chat and why.
3. The pass receipt, including what you stripped. One line per removal, plain
   language, with the words saved. The teammate should be able to say "put the
   Grubhub paragraph back" and know what they are asking for.
4. Anything you inferred that they might want to correct. Recipients you
   guessed at, a `[confirm]` placeholder, a number you pulled from a tracker
   they have not seen.

Then stop.

---

## Where the draft goes

### Default: a Gmail draft in the teammate's own mailbox

The teammate's own connected Gmail, in their own Cowork session, writing to
their own drafts folder. Use the Gmail connector's `create_draft` tool. The
server prefix differs per teammate, so resolve it from whatever Gmail connector
is live in the session rather than hardcoding one.

This is the whole point of the default. The draft appears where they already
read mail, so nothing about their sending habits has to change. They open Gmail,
read it, edit whatever they want, and send it themselves.

Rules on the write:

- Their mailbox only. Never write a draft into someone else's account, and never
  write into a shared or role account on someone's behalf.
- Check for an existing unsent draft on the same thread before creating a new
  one. If one exists, update it or say it exists. Do not stack duplicates in
  somebody's drafts folder.
- No signature. Gmail appends theirs.
- Subject line follows the canon's opener logic: the fact, not the category.
  "Olipop BOGA needs sign-off July 10" beats "Weekly Recap."

### Fallback: chat, for copy and paste

When no Gmail connector is available in the session, output the draft in chat as
a copy-paste block:

```
To: [recipients]
CC: [cc, if any]
Subject: [subject]

[body]
```

Same drafting path, same pass, same receipt. Only the delivery changes.

Treat this as a first-class path rather than a degraded one. Maxx is the only
person on the team not sending from Gmail, and he copies from chat into
Superhuman. Everything upstream of that last step is identical for him, which is
how the standard stays client-agnostic even where the plumbing does not.

Never fall back to writing a Gmail draft into Maxx's mailbox to "cover" a
Superhuman user. Gmail drafts do not sync into Superhuman and the signature
doubles up.

---

## This skill never sends

A hard rule, not a default.

- Never call a send tool. Not `send_draft`, not `send_message`, not any
  equivalent on any connector.
- A PASS from the pass is not permission to send. The pass says so itself.
- A teammate saying "just send it" is not permission either. Point them at the
  draft. It is already in their mailbox and sending it is one click.
- Never schedule a send, never queue one, never set a send timer.
- If a draft is time-sensitive, say so in the handoff line. Do not solve
  urgency by sending.

The reason is narrow and worth keeping straight. Nothing here is a gate on the
send button, and pretending otherwise would be theater. What this skill
guarantees is that a person read the thing before a client did.

---

## Worked run

**Teammate types:** "draft a recap to Fresh Kitchen about last week"

**What happens, with no further questions:** Client is Fresh Kitchen. Format is
weekly recap. Recipients come from the wiki, Hannah and Jamie. The intent
sentence has no explicit ask, but the context does: creative for the Olipop BOGA
lands July 10 and needs sign-off that day. That is a real ask, so the one
question goes unspent. Numbers come from the week's reporting run. The recap doc
is the artifact.

Six topics came out of that call. Two make the email. The other four are in the
recap doc, which gets linked. The Olipop unit cost question becomes the closing
line because it is the open number only somebody working this account would
know is still open.

Result is roughly 117 words, ask on line one, one link, one human line, and a
receipt saying four topics moved into the linked doc and what that saved. The
canon's Fresh Kitchen before and after pair shows the exact shape.

---

## Known limits

- The Gmail draft path runs in a teammate's own Cowork session against their own
  connected Gmail. It cannot be exercised from HQ, so it has been verified by
  reading the instructions rather than by executing them. The first teammate to
  run this should confirm the draft lands in their own drafts folder and say so.
  The never-send guarantee is likewise verified by inspection: there is no send
  call anywhere in this file.
- Prior-thread tone matching is only as good as the session's mail access. With
  no Gmail read, you are drafting off the wiki and the canon alone. That is
  fine. Say so in the handoff line.
- If the client's wiki is stale, the inferred recipients will be stale too.
  The `[confirm]` placeholder is the pressure valve. Use it rather than
  guessing confidently.

---

## Failure modes worth naming

- **Interviewing before drafting.** The most common way this skill fails, and it
  fails completely, because the teammate types the email themselves next time.
- **Writing to the context instead of the ceiling.** Long email, every word
  true, all of it already in the doc you linked.
- **Manufacturing the human line.** "Your locations are performing well heading
  into the holiday" satisfies nothing and tells the client you are guessing.
  No line is better than a fake one.
- **Passing silently on unsourced numbers.** If there is no artifact, say there
  is no artifact.
- **Sending.** See above. There is no version of this where sending is correct.
