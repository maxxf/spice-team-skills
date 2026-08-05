# The Client Comms Governor

This is the thing that governs any client-facing message Spice produces. Not a
skill you remember to invoke. A layer that every path runs through.

`client-comms-style.md` is the canon. It decides what a good client message is.
This page does two jobs on top of it: it drafts one, and it checks one. Nothing
here restates a canon rule, and where the two ever disagree, the canon wins and
this page is the bug.

**Nothing here sends. Ever.** See the hard rule below.

## When this fires

Any client email or any client Slack message, no matter what produced it:

- A skill emitting client copy (`post-client-meeting`, `ratings-reply`,
  `client-onboarding`, `email-template-designer`, and anything added later).
- Spicy Nugget, on a scheduled run or a Slack delegation.
- A teammate typing into Cowork, whether they asked for the standard or not.

It applies whether or not anyone requested it. A teammate who says "just write
Hannah a quick note" gets the same standard as one who says "run the pass." That
is the point of making it a governor instead of a skill: there is nothing new to
remember, and the standard is not opt-in.

It does not fire on internal Slack, teammate DMs, docs, decks, or anything the
client will not read. Those have their own rules in `CLAUDE.md`.

## Two entry points, one document

**Drafting.** Someone gives you one sentence of intent and you produce the
message. Read [The speed contract](#the-speed-contract), then
[Writing to the ceiling](#writing-to-the-ceiling), then run the checks, then
[Where the draft goes](#where-the-draft-goes).

**Checking.** A message already exists, written by a person or by a skill, and
you are the thing standing between it and the client. Skip to
[The checks](#the-checks).

The difference in behavior is narrow but it matters. When you drafted the thing,
strip and report what you stripped. When a human wrote it, flag only and touch
nothing. Nobody wants their own sentences quietly rewritten.

---

## The speed contract

Drafting lane only. The bar is a good draft *in less time than typing the email
yourself takes*. Quality alone does not clear it. Open with four questions and
you have already lost, because the teammate goes back to composing in Gmail
where nothing checks anything.

So the contract is fixed:

**One sentence of intent, at most one clarifying question, then a draft.**

Never run an intake interview. Never ask for the numbers, the tone, the length,
or the format. Everything in the table below is inferred, and a wrong inference
is cheaper than a right question, because the teammate is looking at an editable
draft either way.

### What you infer, never ask

| Thing | Where it comes from |
|---|---|
| Which client | Named in the sentence, or the active client context in the session |
| Recipients | The client's Notion Client Wiki contacts, then the last thread with that client. If still ambiguous, draft anyway with `To: [confirm]` at the top |
| Which of the five formats | The verb in the sentence. "recap" is a weekly recap, "launch" or "goes live" is a campaign launch, "invoice" or "past due" is an escalation, "welcome" or "kickoff" is onboarding, "monthly" or "YoY" is a monthly report |
| The numbers | The client's tracker, the most recent reporting run, the meeting notes. Pull them, do not request them |
| Tone | The prior thread with this contact plus the voice guide. Match how they already get written to |
| Sender name | The teammate running the session |
| Reply or composed | Whether a live thread exists with that contact on that subject |
| Length | The canon decides this, not the teammate |

### The one question you are allowed

Spend it on the ask, and only on the ask.

If the intent sentence carries no request, no deadline, and no decision for the
client, ask exactly one question: **"What do you need back from them?"** Offer
"nothing, this is an FYI" as a real answer, because a declared no-ask email is
legitimate. If they pick that, set `no_ask: true` so C2 is skipped on purpose
rather than by accident.

If the sentence already carries an ask, ask nothing. Draft.

Never spend the question on recipients, format, numbers, tone, or length. A
placeholder in the draft beats a round trip.

### Load the client first

In order, stopping when you have enough:

1. The client's Notion Client Wiki. Contacts, current campaigns, open issues, any
   voice notes on that account.
2. The last two or three threads with this contact. You are reading for tone and
   for what they already know, not for content to copy. If they got the LIC
   numbers on Tuesday, do not re-explain them Thursday.
3. The artifact the message will point at. Weekly reporting run, campaign
   tracker, diagnostic page, monthly update, recap doc.

If none of it is reachable, say so in one line and draft from what you were
given. Do not stall on a missing wiki.

---

## Writing to the ceiling

The inversion that makes the rest work, and it runs against the natural
instinct.

You will usually be holding far more than 150 words of true, relevant material.
The instinct is to include it, because all of it is real and some of it took
work. Resist that. **The size of your context has no bearing on the length of
the message.** A weekly recap built off a 40-minute call and a full tracker pull
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
- Write the line of specific human attention. If you cannot find one, say so
  rather than manufacturing one. V2 will fail you on a manufactured line anyway,
  and the client can tell.

### When there is nothing to link to

This comes up more than you would think. Real numbers, no published artifact
behind them.

Do not inline the detail to compensate. That is the exact failure the ceiling
exists to prevent, and it turns a missing doc into a 400-word email.

Say it plainly, and offer the fix:

> These numbers have nothing behind them. There is no published analysis for the
> July LIC pull. I can generate one with `/deploy` and link it, which takes a
> minute, or you can send this with the numbers unsourced. Which?

Then do what they say. If they want the artifact, generate and deploy it, put the
link in slot four, and carry on. If they want to send unsourced, draft it and let
the receipt record the C3 failure. The point is that the teammate chose it.

---

## The checks

Every check below sits in one of two lanes, and the split is the whole design.

**Lane A is mechanical.** Five checks, each with a countable definition, each
returning PASS or FAIL with no room for taste. A script can run all of Lane A
against a draft with nobody in the room. That is deliberate: the follow-on audit
project scores sent mail automatically, and a check that needs a human to
adjudicate is a check that will quietly stop being run.

**Lane B needs judgment.** Two checks, voice and the line of human attention.
Neither is scriptable and neither should be faked into looking scriptable. A
regex can tell you a draft contains a sentence about the client. It cannot tell
you whether a person actually looked at the account, which is the entire point of
that rule.

The boundary matters more than any individual check. If a future version wants to
add a rule, it goes in Lane A only if you can write the counting procedure in one
paragraph without using the word "appropriate."

---

## Lane A: the mechanical checks

Run all five. Report all failures, not just the first. A draft that fails three
checks should come back with three lines, because the author is going to fix them
in one edit.

### Preparing the body

Every count below operates on the **composed body**, defined once here so the
five checks agree:

Start from the draft's plain text and remove, in this order:

1. **The quoted chain.** Any line whose first non-whitespace character is `>`.
   Also everything from the first line matching `On <anything> wrote:` to the
   end of the draft.
2. **The signature block.** Everything from the first line that is exactly `--`
   or `—` onward. If there is no such delimiter, remove the trailing block of
   lines that contains only the sender's name, title, company, phone, or a URL,
   working upward from the end of the draft until a line breaks that pattern.
3. **Link targets.** The URL itself, whether bare (`https://...`) or the target
   half of a markdown link. **Anchor text stays.** "Full breakdown:
   **Week 27 Recap**" contributes three words, not three words plus a
   sixty-character Notion URL.
4. **Formatting characters.** Markdown `*`, `_`, `#`, and list bullets. They are
   punctuation, not content.

What survives is the composed body. The greeting line ("Shai," or "Mike,
Hengky,") stays in the body for word counting and is excluded only where a check
says so explicitly.

### C1: Length

**A word** is a whitespace-delimited token in the composed body containing at
least one alphanumeric character. `$4,959.36` is one word. `14.4x` is one word.
A bare `—` or `•` is zero words.

**The rule:**

| Composed body | Result |
|---|---|
| Under 40 words **and** the draft is a reply | PASS, exempt, skip C2 through C5 |
| 40 to 150 words | PASS |
| 151 to 200 words | FAIL, soft. Name the overflow. |
| Over 200 words | FAIL, hard. |

A draft is **a reply** if the original message carried a quoted chain or an
`In-Reply-To` header before step 1 stripped it. A composed first-contact email
under 40 words is not exempt. It is just short, and it still has to carry an ask
and a human line.

The soft band is a real failure, not a warning. The difference is what the
receipt says: between 151 and 200 the check names the paragraph most likely
duplicating a linked artifact, because that is where the words are nine times out
of ten. Above 200 it does not bother diagnosing.

### C2: Ask in the first three lines

**A line** is a non-empty line of the composed body after the greeting line,
with consecutive non-empty lines joined into one line only when they are part of
the same wrapped paragraph. Practically: a paragraph is a line, a list item is a
line, a blank line separates lines. Count the first three.

**An ask** is a sentence in those three lines that does at least one of:

- Ends in `?` and is addressed to the recipient rather than to the writer's own
  reasoning. "Which main plate should we pair it with?" is an ask. "So where did
  the orders go?" as a rhetorical setup is not, and this is the one place Lane A
  tolerates a judgment call. Default to counting it as an ask; a false pass here
  is cheaper than training people to avoid question marks.
- Opens with an imperative directed at the recipient: `confirm`, `approve`,
  `send`, `reply`, `pick`, `choose`, `sign off`, `let us know by`, `say go`,
  `book`, `upload`, `pay`, `test`, `review by`.
- States something the recipient must do, with a date attached. "Creative draft
  lands July 10 and needs sign-off that day" is an ask even with no question mark
  and no imperative, because it names an action and a deadline for the reader.

PASS if at least one ask appears in the first three lines. FAIL otherwise, and
the receipt reports where the first ask actually landed, by line number. "Your
ask is on line 7" is more useful than "ask not found."

Some emails have no ask at all. A "this is live, nothing needed from you"
note is legitimate. Those drafts carry `no_ask: true` and C2 is skipped.
Declaring it is the point: it should be a decision, not an oversight.

### C3: A link when numbers are cited

**A cited number** is a token in the composed body matching
`\$?\d[\d,]*(\.\d+)?[%x]?` after these exclusions:

- Dates in any form: `July 14`, `Jul 3`, `7/23`, `2026`, `Jun 14 to 30`
- Times: `10am`, `9:30am PT`
- List numbering at the start of a line: `1.`, `2)`
- Phone numbers, street addresses, ZIP codes
- Version and invoice identifiers
- Numbers inside the anchor text of a link, which are already sourced

**A link** is a bare URL or a hyperlink anchor in the composed body, excluding
`mailto:` and excluding anything in the signature.

**The rule:** if the composed body contains one or more cited numbers, it must
contain at least one link. Zero numbers, no link required.

FAIL is loud and specific. The receipt lists the numbers it found, up to five,
and says there is no artifact behind them. It never passes silently on the theory
that the numbers are probably fine. If the draft has no artifact to point at,
that is a signal the artifact should exist, and the fix is the `/deploy` offer
above rather than inlining the detail.

Invoice-style drafts, where every dollar figure sits on a line with its own pay
link, pass C3 on those links. No carve-out needed.

### C4: Banned patterns

The twenty rows in the canon's banned-pattern table, matched as strings against
the composed body.

**Normalization before matching**, applied to both the pattern and the body:

- Lowercase
- Collapse runs of whitespace to a single space
- Curly quotes and apostrophes to straight ones
- Em dash, en dash, and hyphen all to a single hyphen
- Strip trailing `…`, `...`, `:` from the pattern

A pattern matches on substring. The five patterns the canon writes with a
trailing ellipsis are matched on the stem before it, so "I am writing to request
that" hits regardless of what follows. Row 18 carries two alternates and hits on
either.

PASS is zero matches. Any match is a FAIL, and the receipt gives the matched
string and the canon's replacement, because the replacement column is the part
that actually helps.

The voice guide's kill list is separate and lives in Lane B. It is about word
choice and needs context; this table is about specific padding Spice reaches for
with clients, and it does not.

### C5: No em dashes or en dashes

Count `—` and `–` in the composed body. Zero passes, anything else fails, and the
receipt says how many and where.

This is in Lane A because it is the most mechanical rule in the entire standard
and it is also the one most likely to slip through a model-generated draft.
Commas, periods, or parentheses. The canon's own escalation example shows the
shape.

---

## Lane B: the checks that need a person

### V1: Voice

Read the draft against `maxx-freedman-voice-guide.md` and the canon's tells. The
things worth looking for are the ones no counter catches:

- **Uniform rhythm.** Four sentences of roughly equal length in a row is the
  single loudest AI tell, and it survives every check in Lane A.
- **Hedge stacking.** "This might potentially be somewhat useful."
- **Restating the linked doc.** C3 confirms a link exists. Only a reader can
  tell whether the paragraph above it is the doc retyped.
- **Three soft exits instead of one real question.** Some of these are in the
  banned table; new ones get invented weekly.
- The voice guide's kill list, which is broader than the twenty rows and needs
  context to apply. "Navigate" in "navigate to the dashboard" is fine.

V1 returns PASS, or FAIL with the specific sentences named. Never "the tone
feels off." Quote the line.

### V2: One line of specific human attention

The canon requires at least one line per email that only somebody who looked at
this account this week could have written. This **fails the draft when that line
is absent.** Not a warning, not a nudge. A fail, at the same weight as going over
200 words.

Why it sits in Lane B: a script can confirm a draft mentions a store name and a
number. It cannot tell "Torrance is still on the old bowl pricing, so the 50%
math lands differently there" from "We're seeing strong performance at your
Torrance location." One of those took a person twenty minutes in the data. The
other took a template. They look identical to a regex and nothing like each other
to a client.

The test to apply, and it is a hard one on purpose: **could this sentence have
been written about a different client by changing the proper nouns?** If yes, it
is not the line. Keep looking. If there is no line to find, the fail is correct
and the fix is not a better sentence. The fix is going and looking at the
account.

When you cannot generate this line, say so plainly to the teammate rather than
manufacturing something plausible. Manufactured specificity is worse than none,
because the client can tell and now they know you are guessing.

---

## What the governor hands back

Not a diff. A teammate reading a diff of their own email is being asked to do
this job over again.

The receipt has three parts, in this order:

1. **The verdict.** `PASS` or `FAIL (n)`.
2. **What failed**, one line each, each naming the check, the specific thing, and
   the fix. Ordered by how much rewriting it forces: length first, then ask, then
   link, then patterns, then voice.
3. **What was stripped**, whenever you drafted rather than only checked. One line
   per removal, in plain language, with the word count saved. Write it for a
   teammate to read, not for a log. They should be able to say "put the Grubhub
   paragraph back" and know exactly what they are asking for.

Keep it under fifteen lines. A receipt longer than the email has lost the plot.

Surface the draft alongside the receipt, never instead of it, and add one last
part in the drafting lane: anything you inferred that they might want to correct.
Recipients you guessed at, a `[confirm]` placeholder, a number pulled from a
tracker they have not seen.

---

## Where the draft goes

### Default: a Gmail draft in the sending teammate's own mailbox

Their own connected Gmail, in their own session, writing to their own drafts
folder. Use the Gmail connector's `create_draft` tool. The server prefix differs
per teammate, so resolve it from whatever Gmail connector is live in the session
rather than hardcoding one.

That is the whole point of the default. The draft appears where they already read
mail, so nothing about their sending habits has to change. They open Gmail, read
it, edit whatever they want, and send it themselves.

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

Same drafting path, same checks, same receipt. Only the delivery changes.

Treat this as a first-class path rather than a degraded one. Maxx is the only
person on the team not sending from Gmail, and he copies from chat into
Superhuman. Everything upstream of that last step is identical for him, which is
how the standard stays uniform even where the plumbing is not.

Never fall back to writing a Gmail draft into Maxx's mailbox to "cover" a
Superhuman user. Gmail drafts do not sync into Superhuman and the signature
doubles up.

### Client Slack messages

Same standard, different surface. Use `slack_send_message_draft`, never
`slack_send_message`. The teammate reviews it in Slack and hits send.

---

## This never sends

A hard rule, not a default.

- Never call a send tool. Not `send_draft`, not `send_message`, not any
  equivalent on any connector.
- A PASS is not permission to send.
- A teammate saying "just send it" is not permission either. Point them at the
  draft. It is already in their mailbox and sending it is one click.
- Never schedule a send, never queue one, never set a send timer.
- If a draft is time-sensitive, say so in the handoff line. Do not solve urgency
  by sending.

The reason is narrow and worth keeping straight. This is not a gate on the send
button, and pretending otherwise would be theater. What it guarantees is that a
person read the thing before a client did.

A draft that fails is not blocked from going out, either. Teammates overrule this
all the time and should. What the governor guarantees is that when a 400-word
unsourced email goes to a client, somebody chose that on purpose.

---

## Worked example A: the 400-word draft with no link

A recap draft, numbers throughout, nothing linked, ask buried at the bottom. This
is the failure mode the standard exists for, and it fails Lane A twice before
anyone reads a word of it.

**The draft (394 words in the composed body):**

> Hi Hannah and Jamie,
>
> Wanted to give you a full picture of where things landed in July across all
> fourteen locations, since a few of the numbers moved in ways that are worth
> walking through together before we lock the August plan.
>
> Starting with the top line. July orders came in at 18,412 across the three
> platforms, which is up 6% against June and up 11% year over year. Sales were
> $421,880, up 9% against June. Average ticket moved from $21.90 to $22.92, so
> roughly half of the sales growth is ticket rather than volume, which is the
> healthier of the two ways to grow but also means the volume story is softer
> than the headline suggests.
>
> By platform, Uber Eats did 8,904 orders and $198,340, up 4% and 7%. DoorDash
> did 6,821 orders and $162,110, up 9% and 12%. Grubhub did 2,687 orders and
> $61,430, which is down 2% on orders and flat on sales. Grubhub has been the
> soft spot for three months running now and we think the promo mix there is
> stale relative to what the other two are carrying.
>
> On campaigns, the Olipop BOGA ran July 14 through July 28 on the Salmon Chef
> Bowl and drove 1,104 redemptions at a blended cost of $1.42 per unit, which
> works out to $1,568 in promo cost against $24,300 in attributed sales, so a
> 15.5x return. That is well ahead of the 9x we saw on the Turmeric shot in June.
> Attachment rate on the bowl was 31%, meaning roughly a third of Olipop
> redemptions came with a full bowl attached rather than as a standalone.
>
> Store naming reconciliation is complete across DoorDash and Uber Eats for all
> fourteen in-scope locations, so the Tampa, New Tampa, USF, and SoDo mismatches
> should be gone from reporting starting with the August pull. Weston is still
> running the $5 review reward and has added 47 reviews since it went live, which
> has moved its Uber rating from 4.5 to 4.7.
>
> The tiered ad plan is live at an 8% spend split, and we are watching whether
> the tier two stores can hold ROAS at that level given how thin some of their
> order volume is.
>
> One thing we need from you: can you confirm the August Olipop flavor mix by
> Friday so design has time to build creative?
>
> Let me know if anything's off.
>
> Daniel

**The receipt:**

```
FAIL (4)

C1  Length   394 words. Hard fail, ceiling is 150, hard stop 200.
             Paragraphs 3 and 4 are a performance table written out as prose.
             That is 187 words that belong in the monthly analysis doc.

C3  Link     30 cited numbers, zero links. Nothing in this email is sourced.
             Found: 18,412 orders / $421,880 / $22.92 / 8,904 / $198,340 /
             +25 more. Link the July analysis, or generate one first.

C2  Ask      First ask is on line 8, in the second-to-last paragraph.
             The August flavor mix needs a decision by Friday. Lead with it.

C4  Pattern  "let me know if anything's off" (row 14, daniel to Fresh Kitchen).
             Cut, or make it a real question.

Not reached: V1 and V2. Fix the structure first, the draft is
going to be a different email.
```

Note what the receipt does and does not do. It names both the length failure and
the missing-link failure, separately, because they have different fixes and the
second one is not solved by trimming. It does not silently accept thirty
unsourced numbers on the grounds that the writer probably has them somewhere. And
it stops before Lane B, because running a voice check on a draft that is about to
be rewritten from the studs is wasted work on both sides.

The fix is one move, not four. Link the analysis, keep the two numbers that carry
the point, put the flavor-mix question first. That email is about 110 words and
every number in it is still true.

## Worked example B: the compliant draft

Six lines, one link, one ask up top, one line only a person could write.

**The draft (94 words in the composed body):**

> Mike, Hengky,
>
> National Avocado Day is Jul 31 and design needs the offer locked by mid-July.
> Free avocado upgrade, or something else?
>
> The 4th of July offer goes live Jul 3 at 10am PT, buy one bowl get 50% off
> another, 24 hours only. We'll ping you an hour ahead so you can ring one up and
> confirm the reward fires.
>
> Everything else for July and August: **View Campaign Calendar**
>
> Hengky, Torrance is still on the old bowl pricing, so the 50% math lands
> differently there. Want us to normalize it before the 3rd?
>
> Harol

**The receipt:**

```
PASS

C1  94 words.
C2  Ask on line 1.
C3  3 cited numbers, 1 link.
C4  Clean.
C5  Clean.
V1  Rhythm varies, no restating, one closing question.
V2  Torrance pricing line. Account-specific, not portable.
```

That is the whole receipt. A passing draft gets seven lines and no advice.

Worth noticing why V2 passes here. "Torrance is still on the old bowl pricing, so
the 50% math lands differently there" cannot be moved to another client by
swapping names. It requires knowing which store, which price change, and which
offer, all at once. Compare it to something like "your locations are performing
well heading into the holiday," which would satisfy any counter you could write
and tell Mike nothing.

---

## Calling this from a skill

Skill authors: run it before surfacing anything, never after sending.

The sequence, in order:

1. Read the canon. Then draft, or take the draft you were handed.
2. Build the composed body. Every check downstream depends on this being right.
3. Run C1 through C5. Collect every failure.
4. If C1 hard-fails or C3 fails, stop. Report Lane A and skip Lane B. The draft
   is getting rewritten and voice-checking a doomed draft wastes the teammate's
   attention.
5. Otherwise run V1 and V2.
6. Emit the receipt. Surface the draft alongside it, never instead of it.
7. Stop. Nothing here sends, and no skill should read a PASS as permission to.

## Failure modes worth naming

- **Interviewing before drafting.** The most common way the drafting lane fails,
  and it fails completely, because the teammate types the email themselves next
  time.
- **Writing to the context instead of the ceiling.** Long email, every word true,
  all of it already in the doc you linked.
- **Manufacturing the human line.** "Your locations are performing well heading
  into the holiday" satisfies nothing and tells the client you are guessing. No
  line is better than a fake one.
- **Passing silently on unsourced numbers.** If there is no artifact, say there
  is no artifact.
- **Waiting to be invoked.** This governs client comms by default. A message that
  went out without running through it is the bug.
- **Sending.** See above. There is no version of this where sending is correct.
