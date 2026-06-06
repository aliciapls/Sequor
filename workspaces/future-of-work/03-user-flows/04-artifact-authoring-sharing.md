# User Flow 04 — Artifact Authoring + Cross-Org Sharing: Capture a Process Once, Reuse It Everywhere

> **What this flow shows.** A non-coder captures a company-specific way of doing a piece of
> work — a process, a procedure, a policy — by simply **doing the work once** and letting the
> platform watch. The platform proposes a reusable **artifact** (a skill, a rule, or a named
> command). The person **reviews and edits** it in a plain-language change-review screen, stores
> it, and then **shares** it: first **inside their own organization** (the personalization +
> engagement loop, which works today), then **across organizations** through a **governed
> marketplace** (the cross-org network-effects engine). The flow walks the whole governance
> spine on screen — **provenance** (who made it, how), **trust classification** (how risky is it
> to run), the **untrusted-publisher gate** (the genuinely-new piece), **licensing and
> attribution**, and the **recall** of a bad artifact after the fact.
>
> **Which moat this is.** This is **M4 — governed, versioned, provenance-tracked cross-org
> artifact exchange** — the platform's **strongest** network effect and its **primary
> flywheel** (`01-analysis/06-network-effects.md` §8.1). It is sequenced **second**: the within-org
> loop ignites first because it has no cold-start gap, and the cross-org exchange turns only
> after the within-org loop has produced a seed catalog AND the net-new untrusted-publisher
> trust model has been designed (`06` §8.3, §8.4). This flow is honest about that ordering and
> about the one load-bearing dependency that is genuinely unbuilt.
>
> **Grounding.** Brief: `briefs/01-vision.md` §3g ("artifacts are easily created, modified,
> stored, and shared across organizations and teams"), §3a (non-coder), §3e (posture),
> §3f (transparency). Analysis: `01-analysis/01-research/01-coc-artifact-system.md` (the
> artifact machinery that already runs in production), `01-analysis/04-platform-model.md`
> (producers/consumers/partners + the curated-marketplace shape + cold-start), and
> `01-analysis/06-network-effects.md` (the two-stage ignition + the five behaviors).
> Ecosystem DNA cited by path: loom `~/repos/loom`; pact `~/repos/terrene/contrib/pact`;
> eatp in `~/repos/loom/kailash-py`; aegis `~/repos/dev/aegis`. Uncertainty is flagged inline
> as **[UNCERTAIN]**. Effort is in **autonomous execution cycles**, never human-days, per
> `.claude/rules/autonomous-execution.md`. CLI-neutral throughout per
> `.claude/rules/cross-cli-artifact-hygiene.md`.

---

## 0. Read this first (plain language)

Every company does the same kinds of work in **its own particular way**. Onboarding a new
client, closing the books at month-end, triaging a support ticket, approving an expense,
writing a board-update — the _shape_ of the task is shared across companies, but the _steps_,
the _rules_, and the _judgment calls_ are specific to each one (this is the brief's premise,
`briefs/01-vision.md` §1b: "Processes/procedures… vary from company to company"). Today that
specific know-how lives in three bad places: in one expert's head, in a stale wiki nobody
reads, or scattered across the five tools the work touches. When the expert leaves, it leaves
with them.

An **artifact** is that know-how turned into a thing the platform can actually _run_. Not a
document _about_ the process — the process itself, executable, that the agent follows the way
your best person would. The platform already has five kinds of artifact, and the names matter
less than what each one does (full taxonomy in `01-analysis/01-research/01-coc-artifact-system.md`
§1). In plain language:

| Artifact kind | What it is, plainly                                      | Everyday example                                             |
| ------------- | -------------------------------------------------------- | ------------------------------------------------------------ |
| **Skill**     | Reference know-how the agent looks up when it's relevant | "How we categorize expenses for tax"                         |
| **Rule**      | A boundary the agent must always respect                 | "Never send a refund over $500 without a manager's sign-off" |
| **Command**   | A named procedure you can invoke by name                 | "Run the month-end close"                                    |
| **Agent**     | A specialist with its own judgment + tools               | "Our contract-review specialist"                             |
| **Hook**      | An automatic safety tripwire on specific actions         | "Pause before anything touches the payroll system"           |

The thing this flow is really about: **you do not write any of these by hand.** The brief is
explicit that users are not coders (`briefs/01-vision.md` §3a). So the platform captures the
artifact by **watching you do the work once** and proposing the artifact back to you in plain
language. You then **review it, fix it, and decide who gets to use it.** That's the whole loop.

The one-sentence version: **do a piece of work once, the platform turns it into a reusable
procedure, you approve it, and then you can share that procedure with your team — and,
eventually, sell or give it to other companies — with full tracking of who made it, how risky
it is to run, and the ability to pull it back if it turns out to be bad.**

> **The honest headline, up front.** Two of the three stages below **work today** in
> skeleton form, for one organization's code artifacts, in production
> (`01-analysis/01-research/01-coc-artifact-system.md` §0: "runs in production"). The third
> stage — **sharing across companies** — requires a piece that is **genuinely new and not yet
> built**: a way to trust an artifact published by a company you've never met. The platform
> spine names this the "untrusted-publisher trust model" and calls it the load-bearing 5%
> (`01-analysis/04-platform-model.md` §7.3, `06` §8.3). This flow walks all three stages but
> marks clearly where the proven machinery ends and the new design begins.

---

## 1. The scenario — "Maria captures the new-client onboarding process"

One person, one real piece of work, followed all the way out to other companies.

| Participant         | Who/what                                                           | Role in this scenario                                            |
| ------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------- |
| **Maria**           | Human, Operations Lead at **Northwind** (a mid-size services firm) | Knows the onboarding process cold; not a coder                   |
| **agent-work**      | Agent Maria works through daily                                    | Does the onboarding work _with_ Maria; later drafts the artifact |
| **Devin**           | Human, a colleague on Maria's team at Northwind                    | First _internal_ consumer of Maria's artifact                    |
| **Sofia**           | Human, Ops Lead at **Cascade** (a _different_ company)             | First _cross-org_ consumer — the M4 leap                         |
| **Northwind admin** | Human, governs what Northwind publishes outward                    | The publish gate for cross-org sharing                           |
| **The platform**    | Sequor                                                             | Watches, proposes, governs the exchange, runs recall             |

The work itself: **onboarding a new client.** At Northwind this means: create the client
record, send a specific welcome packet, schedule a kickoff call within 3 business days, set up
their billing profile, and — Northwind's particular rule — **never activate billing until the
signed contract is on file.** That last clause is exactly the kind of company-specific judgment
that lives only in Maria's head today.

The flow has **three stages**, mapped to the platform's two-stage ignition
(`01-analysis/06-network-effects.md` §8.1):

```
STAGE A — CAPTURE        Maria does onboarding once → platform proposes an artifact
   │                     → Maria reviews/edits in a plain-language screen → stored
   ▼
STAGE B — SHARE WITHIN    Devin (same company) discovers + runs Maria's artifact
   THE ORG                → his corrections flow back → the artifact improves
   │                       [this is the within-org loop — works today, no cold-start]
   ▼
STAGE C — SHARE ACROSS    Northwind publishes to the marketplace → Sofia (Cascade)
   ORGS                   discovers, checks provenance + trust, runs it under caution
                          → recall machinery stands ready if it turns out bad
                          [this is M4 — needs the net-new untrusted-publisher trust model]
```

> **Why this ordering matters to you (the business reader).** Stages A and B make **your own
> company's work compound** — every process someone captures makes the next person faster, and
> the know-how stops walking out the door. That value lands first and does not depend on anyone
> else showing up (`06` §8.4 "no cold-start gap"). Stage C is the bigger prize — your processes
> become assets you can trade — but it arrives later, on purpose, because it needs a trust
> mechanism that does not exist yet anywhere (`04` §7.3). You get a sticky product now and a
> category-defining marketplace later; you are not betting the company on the unbuilt part.

---

## 2. STAGE A — Capture: do the work once, get an artifact back

### 2.1 Maria does the onboarding, the normal way

Maria gets a new client. She does what she always does — but she does it **inside the
platform's one interface**, stating intent in plain language instead of crossing five tools
(this is the ACCESSIBILITY behavior, proven in the comms wedge's <10-minute onboarding,
`06` §2.1). On her screen:

```
Maria:  New client — Birchwood Partners. Onboard them.

agent-work:  Here's what I'll do (you can change any step):
  1. Create client record for Birchwood Partners
  2. Send the standard welcome packet
  3. Schedule a kickoff call (target: within 3 business days)
  4. Set up the billing profile
  5. Activate billing
  Proceed?  [Approve all]  [Step-by-step]  [Edit the plan]
```

Maria catches the danger immediately. She intervenes — and this is the key moment for capture:

```
Maria:  Stop — never activate billing until the signed contract is on file.
        Hold step 5 until I confirm the contract is in.

agent-work:  Understood. Holding billing activation until you confirm a signed
        contract. Running steps 1–4 now.
```

The work completes. The client is onboarded correctly. **Nothing about this looks like
"authoring an artifact"** — Maria just did her job and corrected the agent once. That
correction is the gold. The platform captured it.

### 2.2 The platform proposes the artifact (the generalized `/codify`-from-observed-work pattern)

This is the load-bearing mechanism, so it's worth naming precisely. The platform already has a
production loop that **watches a completed work session and proposes a reusable artifact from
it** — in the existing system it is the `/codify` flow, which reads a structured digest of what
happened in a session and drafts artifact changes for a human to approve
(`01-analysis/01-research/01-coc-artifact-system.md` §3a: "observe → digest → codify into real
artifacts"). Today that loop captures **code-session** signals; generalizing it to
**non-coding work** is the stated adaptation, not a from-scratch build
(`01-coc-artifact-system.md` §7b.4, §8.3 — flagged there as real work).

A day later, the platform surfaces a proposal — **unprompted, as a gentle nudge, not a
blocking demand**:

```
┌─ The platform noticed something reusable ──────────────────────────┐
│                                                                      │
│  You onboarded Birchwood Partners yesterday. The steps you took     │
│  look like a repeatable process. Want to save it so you (and your   │
│  team) can run it with one instruction next time?                   │
│                                                                      │
│  I'd save it as a COMMAND called "onboard-new-client" plus one      │
│  RULE that protects the billing step.                               │
│                                                                      │
│        [Review the proposal]      [Not now]      [Never suggest]    │
└──────────────────────────────────────────────────────────────────┘
```

Maria clicks **Review the proposal.**

> **Where the proposed shape comes from.** The platform proposes a _command_ for the procedure
> and a _rule_ for the boundary because that is what the artifact taxonomy says each is for —
> a named procedure is a command; an always-respected boundary is a rule
> (`01-coc-artifact-system.md` §1). The person never has to know the taxonomy; the platform
> picks the right shape and **explains it in plain language**, exactly as the recommendation
> rule requires (`.claude/rules/recommendation-quality.md` — recommend, don't enumerate).

### 2.3 The plain-language change-review screen (the non-coder authoring surface)

Under the existing system, artifacts are hand-written Markdown and code, reviewed by engineers
in a Git diff. **That is exactly what a non-coder cannot do** — and it is named as a net-new
build: "non-coder authoring UX… artifacts today are hand-authored Markdown/JS"
(`01-coc-artifact-system.md` §7b.4). So this screen is one of the genuinely-new surfaces the
platform must build. It shows the artifact as **plain-language steps and rules**, not code:

```
┌─ Review: "Onboard a new client" ───────────────────────────────────┐
│                                                                      │
│  WHAT THIS DOES (a Command you can run by name)                      │
│  When you say "onboard [client]", I will:                            │
│    1. Create the client record                                       │
│    2. Send the standard welcome packet                               │
│    3. Schedule a kickoff call within 3 business days                 │
│    4. Set up the billing profile                                     │
│    5. Activate billing  — ⚠ guarded by the rule below               │
│                                                                      │
│  THE GUARDRAIL (a Rule I will always respect)                        │
│    Never activate billing until a signed contract is on file.        │
│    → If no signed contract, I will pause and ask you.                │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Edit step 3:  "within 3 business days"  → [change to…]        │ │
│  │ Edit the rule: [edit]   Add a step: [+]   Remove a step: [×]  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  PROVENANCE (auto-filled, you can't fake it)                         │
│    Captured from: your Birchwood Partners session, [date]           │
│    Author: Maria (verified)    Company: Northwind                    │
│                                                                      │
│        [Save as a draft]        [Save & make available to my team]  │
└──────────────────────────────────────────────────────────────────┘
```

Maria makes one edit — she changes "3 business days" to "2 business days" because her team's
standard is tighter — and she reads the guardrail back to confirm it's right. She clicks
**Save & make available to my team.**

> **What just happened, in governance terms.** Three things were established the moment Maria
> saved, all of which the existing machinery already supplies:
>
> - **Provenance.** The artifact is stamped with _who_ made it and _how it was captured_ — and
>   the "who" is cryptographic, not a typed name. Every record in the substrate is signed by a
>   verified identity that resolves to exactly one person (`01-analysis/04-platform-model.md`
>   §3.3; substrate detail in `.claude/rules/multi-operator-coordination.md` §1). Maria cannot
>   later deny she authored it, and nobody else can claim they did.
> - **Versioning.** The artifact is a draft in a change lifecycle —
>   `pending_review → reviewed → distributed` — that is **append-never-overwrite**, so no future
>   edit silently destroys this version (`01-coc-artifact-system.md` §3b;
>   `.claude/rules/artifact-flow.md` § Proposal Lifecycle).
> - **Two-level attribution for the agent's part.** The agent drafted; Maria approved. The
>   record attributes the draft to _both_ the agent AND the human accountable for it
>   (`04` §3.3: "an agent's output is attributable to the agent AND to the human accountable for
>   it"). The agent is a _producer_, never an _authority_ — a human always approves before
>   anything enters the catalog (`04` §3.2).

### 2.4 Trust classification — how risky is this artifact to run?

Before the artifact is shareable, the platform classifies **how much autonomy it should be
allowed**. This is the L1–L5 posture ladder from the brief (`briefs/01-vision.md` §3e), and it
is moat M2 — the execution-time governance that makes running an artifact safe
(`01-analysis/04-platform-model.md` §7.2). Plain language on screen:

```
┌─ How much should this artifact be trusted to do on its own? ───────┐
│                                                                      │
│  This artifact TOUCHES BILLING. That's sensitive, so I'm            │
│  classifying it cautiously by default:                               │
│                                                                      │
│   ○ "Go ahead"      — runs end to end, no pausing                   │
│   ○ "Ask me once"   — asks once before it starts                    │
│   ● "Step through"  — pauses at each step      ◄ recommended default │
│                                                                      │
│  You can raise the trust later, once you've seen it run cleanly      │
│  a few times. New or sensitive artifacts start cautious.             │
└──────────────────────────────────────────────────────────────────┘
```

> **Why default-cautious.** These three buttons are the same plain-language postures from User
> Flow 01; each maps to one engine rung, pinned internally and never shown to the user
> (engine-internal: "Go ahead" = L5 `AUTONOMOUS`, "Ask me once" = L4 `DELEGATING`, "Step through"
> = L3 `SUPERVISED` — `04` §1.2). The brake is real but it's a _default_, not a _lock_
> (`04` §7.3 con: "a consumer who runs every unvetted artifact on 'Go ahead' defeats the brake").
> The platform defaults sensitive artifacts to "Step through" (pause every step) and lets trust
> rise with proven runs — but a determined user can over-trust. The honest framing: the posture
> ladder _reduces_ the blast radius of a bad artifact; it does not _eliminate_ it.

**End of Stage A.** Maria did her work once. The platform proposed a command + a rule, she
edited them in plain language, the artifact is stored with provenance, a version history, and a
trust classification. **No code, no engineer, no Git.** This capture-and-review surface is one
of the net-new builds (`01-coc-artifact-system.md` §7b.4); everything _underneath_ it —
the codify loop, the proposal lifecycle, the signed provenance — already runs.

---

## 3. STAGE B — Share within the org: the personalization + engagement loop

This is the stage that **ignites first** and has **no cold-start problem**, because the producer
and the consumer are the _same organization_ — Northwind authors, Northwind consumes, so there
is no chicken-and-egg of two unknown parties both having to show up (`06` §8.4;
`04` §6.3: "supply = demand = same customer").

### 3.1 Devin discovers and runs Maria's artifact

A week later Devin, on Maria's team, gets his own new client. He doesn't know Maria captured a
process. He just states intent — and the platform surfaces her artifact:

```
Devin:  New client — Tideway Logistics. How do we onboard them?

agent-work:  Your team has a saved process for this: "Onboard a new client"
        (by Maria, used 4 times, runs cleanly). Want me to run it?

        It includes your team's guardrail: billing won't activate until the
        signed contract is on file. I'll pause at each step the first time
        so you can see what it does.   [Run it]  [Show me the steps first]
```

Devin runs it. Because it's his first time, it runs on **"Step through"** (the trust
classification from §2.4 travels _with_ the artifact). He watches it work, approves each step,
and — at the billing step — the rule fires exactly as designed: the contract isn't in yet, so
the agent pauses and asks. Devin confirms the contract arrived, billing activates.

> **What compounded.** Devin got Maria's expertise without a meeting, a wiki-hunt, or a
> "hey, how do we do onboarding again?" Slack message. This is the **PERSONALIZATION** behavior
> — the org's way of working now _lives_ in the platform, and every saved process raises the
> switching cost (`06` §4.2: "the org's way-of-working now LIVES here"). It is the strongest
> _retention_ engine of the five behaviors (`06` §7 rank #3).

### 3.2 Devin's correction flows back — the engagement (knowledge-contribution) loop

Devin's client has an unusual wrinkle: Tideway requires a data-processing agreement (DPA)
before the welcome packet goes out. Devin handles it manually and tells the agent why. **That
correction is captured** — the same `/codify`-from-observed-work mechanism that captured Maria's
original process now captures Devin's refinement (`06` §3.1, the learning loop; the comms wedge
runs this loop end-to-end today, `04` §2.2):

```
┌─ A teammate refined a shared process ──────────────────────────────┐
│                                                                      │
│  Devin handled a case your "Onboard a new client" process didn't    │
│  cover: some clients need a data-processing agreement (DPA) before   │
│  the welcome packet.                                                  │
│                                                                      │
│  Suggested improvement (Maria, you own this artifact — your call):   │
│    Add an optional step 1.5: "If client requires a DPA, send and     │
│    confirm it before the welcome packet."                            │
│                                                                      │
│        [Review & accept]    [Decline]    [Ask Devin to clarify]      │
└──────────────────────────────────────────────────────────────────┘
```

Maria accepts. The artifact is now **version 2**, with Devin attributed for the improvement,
and the version history preserved (append-never-overwrite, `01-coc-artifact-system.md` §3b).
The next person who runs it gets the better version automatically.

> **The flywheel, in one company.** Capture → use → correct → improve → re-use. This is the
> **two transactions composing into one flywheel** the platform model names: the published
> artifact (transaction B) and the knowledge contribution that refines it (transaction D)
> (`04` §2.2). Crucially, **the consumer is also a producer** — Devin consumed _and_ improved,
> as work exhaust, with no separate authoring step (`04` §4.3, §3.2: "the largest producer
> cohort produces for free"). This is what makes the loop compounding, not merely additive.

### 3.3 Honest limits of Stage B

- **Process-level capture is unproven at this depth.** The comms wedge proves the learning loop
  for _answers_ (data-level: question → answer). Generalizing it to capture _processes_ (a
  multi-step command + a rule, as in §2.2) is asserted, not yet demonstrated
  (`06` §3.3 con; `04` §2.2 con). If process-capture turns out much harder than answer-capture,
  the platform's biggest supply engine slows to hand-authoring speed. **This is a real risk, not
  a glossed one.**
- **Depth dies at the last 20%, unless transparency rescues it.** A simple onboarding is within
  reach; a genuinely complex, judgment-heavy process may exceed what no-code capture can hold
  (`06` §2.3, the "last 20%" caution). The platform's escape hatch is that the transparent,
  interveneable substrate (moat M1) makes even a deep process _legible_ and _correctable_ — but
  that is the riskiest claim in the whole thesis, and it must be proven, not asserted (`06` §2.3).

**End of Stage B.** Northwind now has a small, growing library of its own processes, each
captured from real work, each improving as the team uses it. **This alone is a sticky,
revenue-bearing product** — even if Stage C never ships, the company's know-how now compounds
instead of walking out the door (`06` §8.5: "M4 is upside, not survival-critical").

---

## 4. STAGE C — Share across orgs: the governed marketplace (M4)

This is the prize and the hard part. Northwind's onboarding process is good. Cascade — a
_different company_ — would love to not reinvent it. The platform's job is to make running
**another company's process inside your company, against your real data** as safe as installing
a reviewed app (`04` §1, anchor sentence).

> **The honest gate, restated where it bites.** Everything in Stages A and B reuses machinery
> that runs in production for _one organization_ (`01-coc-artifact-system.md` §0). Stage C
> requires the **genuinely-new 5%**: a trust model for **untrusted publishers**. The existing
> threat model is _bounded-trust_ — "the adversary is a legitimate team member with repo write
> access" (`01-coc-artifact-system.md` §7c.1; substrate at
> `.claude/rules/multi-operator-coordination.md` § threat model). A cross-org marketplace faces
> publishers you have **never met and have no shared enrollment with**. Signed-artifact
> provenance from an _external_ publisher is **not yet modeled** (`01-coc-artifact-system.md`
> §7c.1). This is the **#1 thing to resolve before committing to the cross-org marketplace**
> (`04` §9.1). The walk below shows what the surface _will_ look like, and marks the new design
> at each point.

### 4.1 Publish — the org's outward gate + the disclosure scrub

Cross-org publishing is **not** something an individual does on a whim. It goes through the
**Northwind admin**, who governs what leaves the company. On the admin's screen:

```
┌─ Publish "Onboard a new client" to the marketplace? ───────────────┐
│                                                                      │
│  Author: Maria (verified) · Northwind     Version: 2                 │
│  Internal usage: 11 runs, 0 failures, last 30 days                   │
│                                                                      │
│  BEFORE THIS LEAVES NORTHWIND, I scrubbed it for anything private:   │
│    ✓ No client names found (Birchwood, Tideway → genericized)        │
│    ✓ No internal system paths or credentials                         │
│    ✓ No employee personal data                                       │
│    ⚠ One line mentions "our DPA template" — [review]  [genericize]   │
│                                                                      │
│  LICENSE for outside companies:                                      │
│    ● Free to use, attribution required (recommended for goodwill)    │
│    ○ Paid — set a price          ○ Internal-only (don't publish)     │
│                                                                      │
│  TRUST CLASS shown to consumers: L3 (touches billing — sensitive)    │
│                                                                      │
│        [Publish to marketplace]            [Keep internal]           │
└──────────────────────────────────────────────────────────────────┘
```

Two pieces of this are **already built and load-bearing**:

- **The disclosure scrub.** The existing system runs a mandatory **disclosure-scrub on intake**
  before any artifact is distributed, precisely because a shared artifact reaches many consumers
  and any client/operator identifier must be genericized first
  (`01-coc-artifact-system.md` §2b "Intake Disclosure Scrub";
  `.claude/rules/artifact-flow.md` § Intake Disclosure Scrub;
  `.claude/rules/upstream-issue-hygiene.md` MUST-2). This is _exactly_ the cross-org safety gate
  — the machinery exists; it gets pointed at the org boundary instead of the repo boundary
  (`01-coc-artifact-system.md` §7a.4).
- **Human-classifies-every-change.** Publishing is **curated, not open**. A human at the
  publishing org gates what goes out — automated suggestions are allowed, automated _placement_
  is not (`01-coc-artifact-system.md` §2b; `04` §7.1 "curated, not open"). You cannot run a
  stranger's payroll process on caveat-emptor (`04` §7.1).

Two pieces are **net-new**:

- **Licensing + attribution for shared work artifacts.** Provenance capture exists; _licensing_
  (free/paid/attribution-required) for a third-party work artifact is unbuilt
  (`01-coc-artifact-system.md` §7c.3). The screen above shows the _target_; the mechanism is to
  be built.
- **The cross-org distribution boundary itself.** Today every consumer is a clone of _one_ Git
  remote under one organization (`01-coc-artifact-system.md` §7b.1). Org-A-authors →
  org-B-consumes with no shared remote is the publish/subscribe surface that does not exist yet
  (estimated ~3–5 autonomous sessions, _gated on the trust model landing first_,
  `01-coc-artifact-system.md` §7d).

### 4.2 Discover — Sofia finds the artifact at another company

Sofia, at Cascade, is setting up onboarding. She searches the marketplace — and here is another
net-new surface: **discovery/search does not exist today** (today discovery is a config manifest
plus semantic matching, `01-coc-artifact-system.md` §7b.2). The reusable foundation is that
artifacts already carry a semantic description that doubles as a discovery signal
(`01-coc-artifact-system.md` §7b.2). Sofia's screen:

```
┌─ Marketplace: "client onboarding" ─────────────────────────────────┐
│                                                                      │
│  ▸ Onboard a new client            by Northwind (verified org)      │
│      ★★★★☆  used by 23 companies · 0 recalls · free w/ attribution  │
│      Trust class: L3 (touches billing) · License: attribution req.  │
│      Provenance: captured from real work · author verified          │
│                                                                      │
│  ▸ Client intake + KYC             by FinServ Co (verified org)     │
│      ★★★☆☆  used by 8 companies · 1 recalled version · paid          │
│                                                                      │
│  ▸ quick-onboard                   ⚠ UNVERIFIED PUBLISHER           │
│      no usage history · provenance unverified                        │
│      → running this requires extra confirmation (see below)         │
└──────────────────────────────────────────────────────────────────┘
```

### 4.3 The untrusted-publisher gate (the genuinely-new trust model)

Sofia picks Northwind's artifact (a **verified** org). But the screen also shows an
**unverified** one — and how the platform treats it is the heart of the net-new design. When
Sofia clicks the verified Northwind artifact:

```
┌─ Before you run Northwind's "Onboard a new client" ────────────────┐
│                                                                      │
│  PROVENANCE — what we can prove about this artifact:                 │
│    ✓ Published by Northwind, a VERIFIED organization                 │
│    ✓ Authored by a verified person at Northwind                      │
│    ✓ Captured from real work (not hand-typed)                        │
│    ✓ 23 companies run it · 0 recalls · 11 internal runs before publish│
│                                                                      │
│  WHAT IT WILL DO IN *YOUR* COMPANY:                                  │
│    • Create client records · send packets · schedule calls           │
│    • Touch your billing system  ← this is why it's most-cautious     │
│                                                                      │
│  HOW IT WILL RUN HERE (your brake — you choose):                     │
│    ● "Step through" (recommended for a process new to you)           │
│    ○ "Ask me once"    ○ "Go ahead" (only after you trust it)         │
│                                                                      │
│    [Install & run on "Step through"]      [Don't install]            │
└──────────────────────────────────────────────────────────────────┘
```

And when Sofia (or anyone) hovers the **unverified** artifact, the gate is sharply different:

```
┌─ ⚠ This artifact is from an UNVERIFIED publisher ──────────────────┐
│                                                                      │
│  We CANNOT prove who made this, or that it came from real work.     │
│  It has no usage history. It may be fine. It may be malicious.       │
│                                                                      │
│  If you proceed, it runs on "Step through" (pause every step) — you  │
│  cannot raise it to "Go ahead" until it has a verified track record. │
│  It will run in a restricted sandbox first, against test data only.  │
│                                                                      │
│        [I understand the risk — sandbox-run it]   [Cancel]          │
└──────────────────────────────────────────────────────────────────┘
```

> **What is proven vs. what is new here.** The **consumer-side brake** (run a stranger's
> artifact cautiously, on "Step through", in a sandbox) is the existing posture model (M2) applied at the
> install boundary (`04` §4.2 "governed at install AND at run"). That is reusable. What is
> **new** is _establishing the publisher's trustworthiness in the first place_ when there is no
> shared enrollment authority. The existing substrate proves identity for _enrolled_ operators
> (signing keys, a roster, a 2-of-N quorum — `.claude/rules/multi-operator-coordination.md` §1).
> An _external_ publisher is not on anyone's roster. The likely shape — flagged but not chosen —
> is "aegis-shape runtime records, anchored against the consuming tenant's own identity provider
> instead of a shared Git remote" (`04` §9.6, citing the synthesis-to-be-built;
> aegis at `~/repos/dev/aegis`). **The closest existing precedent** for the asymmetry the
> marketplace needs is the aegis fork-relationship rule: the generic registry artifact stays
> generic; org-specific overrides are allowed; improvements can flow _up_ to the generic, but
> one org's client-specific data must never leak _down_ to others
> (`01-coc-artifact-system.md` §7c.2; `~/repos/dev/aegis/.claude/rules/aegis-fork-relationship.md`).
> This asymmetric publish/consume governance is the exact shape — and it already exists as a
> baseline rule in the commercial fork — but wiring it to _untrusted external_ publishers is the
> design that must be done **first, before the registry surface**, because it constrains that
> surface (`01-coc-artifact-system.md` §7d; `04` §7.3).

### 4.4 Variant overlay — Sofia adapts it to Cascade without forking off

Cascade's process is _almost_ Northwind's, but Cascade's billing rule is stricter: no billing
until contract **and** a deposit. Sofia doesn't want to rebuild the artifact; she wants
Northwind's as a base with one local override. The platform's **variant-overlay** engine does
exactly this — and it is **already built**, generalizing from its current language/CLI axis to
an org-default-vs-org-override axis (`01-coc-artifact-system.md` §7a.3, §7b.1, estimated
~1 session of mechanical work, §7d):

```
┌─ Adapt "Onboard a new client" for Cascade ─────────────────────────┐
│                                                                      │
│  Base (from Northwind — kept in sync if they improve it):           │
│    Rule: no billing until signed contract on file                    │
│                                                                      │
│  Cascade's override (yours, stays private to Cascade):               │
│    Rule: no billing until signed contract AND deposit received       │
│    ↳ This REPLACES Northwind's billing rule for Cascade only.        │
│                                                                      │
│  Everything else inherits from Northwind's base automatically.       │
│        [Save Cascade's version]                                      │
└──────────────────────────────────────────────────────────────────┘
```

> **Why this is powerful and safe at once.** Overlay semantics are _replacement / addition /
> global-only_ (`01-coc-artifact-system.md` §2a; `.claude/rules/artifact-flow.md` § Variant
> Overlay Semantics): Cascade's billing rule _replaces_ Northwind's for Cascade only; the rest
> is inherited. When Northwind improves the base (say, the DPA step from §3.2), Cascade gets the
> improvement automatically — **without** losing its local override, and **without** Cascade's
> private deposit rule ever leaking back to Northwind (the asymmetric, upstream-generic-only
> direction, §4.3). This is the controlled-permeability the platform must hold: isolation strong
> enough to protect each tenant, permeable enough to deliberately share when the org chooses
> (`06` §4.3, the permanent tension; `04` §9.5).

### 4.5 Recall — pulling a bad artifact back from everyone

Six weeks later, a flaw surfaces: under a rare timing condition, an early version of Northwind's
artifact could schedule the kickoff call before the client record fully saved, creating a
duplicate. Northwind needs to **pull it back from every company running it.** The platform has
this primitive **already, shipping** — the obsoletion mechanism, "the ONLY mechanism by which
30+ downstream repos can purge stale artifacts," is the cross-org "recall a bad artifact"
primitive the marketplace needs (`01-coc-artifact-system.md` §2d; `04` §4.2). On Northwind
admin's screen:

```
┌─ Recall "Onboard a new client" v2? ────────────────────────────────┐
│                                                                      │
│  Reason (shown to every consumer): "Rare duplicate-record bug at     │
│  the scheduling step. Upgrade to v3 (fixed) or pause use."           │
│                                                                      │
│  This will, on every consuming company's next sync:                  │
│    • Mark v2 recalled (it stops being runnable)                      │
│    • Offer v3 as the safe replacement                                │
│    • Preserve each company's local overrides (e.g. Cascade's deposit │
│      rule carries forward to v3 untouched)                            │
│                                                                      │
│  23 companies affected · 0 of their private data is touched          │
│        [Issue recall]                    [Cancel]                    │
└──────────────────────────────────────────────────────────────────┘
```

Sofia, at Cascade, sees the recall on her next session — loud, plain-language, with the safe
upgrade path one click away. Her deposit-rule override survives the upgrade.

> **Why recall is the trust keystone for an untrusted-publisher catalog.** A marketplace that
> lets strangers publish _must_ be able to un-publish instantly and universally, or one bad
> artifact poisons every consumer with no remedy. Recall is the consumer's protection against a
> producer who turns malicious or buggy _after the fact_ (`04` §4.2). It is the single piece of
> the cross-org trust story that is **already production-grade** — which is itself a real
> competitive advantage: existing skills/MCP marketplaces are "publish/consume directories"
> that lack governed recall (`06` §8.2, citing `07` §9e).

---

## 5. The governance spine, gathered in one place

Pulling the five governance properties out of the walk, with their honest build status:

| Property                         | What it does (plain)                                                                      | On screen at | Build status                                                                                          |
| -------------------------------- | ----------------------------------------------------------------------------------------- | ------------ | ----------------------------------------------------------------------------------------------------- |
| **Provenance**                   | Proves _who_ made it + _how_ (captured from real work), cryptographically                 | §2.3, §4.3   | **Exists** — signed identity substrate (`04` §3.3; `.claude/rules/multi-operator-coordination.md` §1) |
| **Trust classification (L1–L5)** | How much autonomy the artifact gets; default-cautious for sensitive ones                  | §2.4, §4.3   | **Exists** — posture model M2 (`04` §7.2; `briefs/01-vision.md` §3e)                                  |
| **Disclosure scrub**             | Strips client names / private data before an artifact leaves the org                      | §4.1         | **Exists** — intake scrub (`01-coc-artifact-system.md` §2b; `.claude/rules/artifact-flow.md`)         |
| **Untrusted-publisher gate**     | Treats unknown publishers with sharply higher caution (sandbox, locked to "Step through") | §4.3         | **NET-NEW** — the load-bearing 5%, unbuilt + unmodeled (`01-coc-artifact-system.md` §7c.1; `04` §9.1) |
| **Licensing + attribution**      | Free / paid / attribution-required for cross-org artifacts                                | §4.1         | **NET-NEW** — provenance exists, licensing unbuilt (`01-coc-artifact-system.md` §7c.3)                |
| **Variant overlay**              | Adapt a shared artifact locally without forking; inherit upstream fixes                   | §4.4         | **Exists** — overlay engine, ~1 session to add org axis (`01-coc-artifact-system.md` §7a.3, §7d)      |
| **Recall / obsoletion**          | Pull a bad artifact from every consumer on next sync                                      | §4.5         | **Exists** — obsoletion primitive, production-grade (`01-coc-artifact-system.md` §2d)                 |

> **The pattern in this table is the whole strategic story.** Almost everything is **already
> built** — provenance, posture, scrub, overlay, recall. The two NET-NEW items both cluster on
> the _cross-org untrusted_ boundary, and the untrusted-publisher gate is the one that **must be
> designed before the marketplace surface**, because it constrains it (`04` §7.3; `06` §8.3).
> This is the 80/15/5 split made concrete: ~80% reusable, ~15% adapt (org axis, discovery
> surface), ~5% genuinely new (untrusted publishers, licensing) — `01-coc-artifact-system.md` §7.

---

## 6. Recommendation, implications, and the honest trade-off

Per `.claude/rules/recommendation-quality.md` (recommend, don't enumerate) and
`.claude/rules/autonomous-execution.md` (autonomous cycles, never human-days):

**Recommendation: build Stages A + B first as a complete, shippable within-org artifact economy;
design the untrusted-publisher trust model in parallel as a standalone research track; open
Stage C (cross-org) only after both land.** This is the two-stage ignition the network-effects
analysis already recommends (`06` §8.1), expressed as a build order.

**What this means for you (implications):**

- **You ship a sticky product fast.** Stages A + B reuse production machinery plus two net-new
  surfaces (non-coder capture/review + process-level codify generalization). Estimated:
  taxonomy generalization ~1 session, org-axis overlay ~1 session (mechanical, high feedback
  loop, `01-coc-artifact-system.md` §7d); the non-coder authoring surface and process-capture
  generalization are the larger net-new pieces and should be sharded per
  `.claude/rules/autonomous-execution.md` (≤500 LOC load-bearing / ≤5–10 invariants per shard).
- **The big network effect (cross-org) is preserved, not abandoned — it is sequenced.** The
  trust model is a greenfield, novel-architecture decision (~2–3× first-session factor); the
  registry/publish-subscribe surface is ~3–5 sessions but **gated on the trust model landing
  first** (`01-coc-artifact-system.md` §7d).
- **A halt at any stage still leaves a viable product** — Stage B alone is a per-org know-how
  asset worth real money (`06` §8.6 pro).

**Symmetric cons (real, not glossed):**

- **The load-bearing 5% is genuinely unbuilt and unmodeled.** If the untrusted-publisher trust
  model proves intractable, M4 stays a within-org effect and the platform's network-effect
  strength collapses to collaboration (#2) — strong, but not category-defining
  (`06` §8.6 con; `04` §7.3).
- **Process-level capture is unproven.** Stage A's whole premise — that the platform can capture
  a _process_ (not just an answer) from observed work — is asserted, not demonstrated
  (`06` §3.3; `04` §2.2). The seed-catalog thesis depends on it.
- **Curation may not scale.** The human-classifies-every-change gate works for one org's repos;
  at thousands of cross-org publishers, a human-classify bottleneck does not obviously survive
  and may need reputation-weighting or partial automation — unresolved (`04` §7.3, §9.2).
- **A competitor could occupy the cross-org-governance whitespace first** while Sequor proves
  the within-org loop. The mitigation is that the trust/provenance layer is the hard part and
  the platform's DNA is uniquely matched to it — "a head start on the hard part" is an advantage,
  not a guarantee (`06` §8.6 con).

---

## 7. Where the proven machinery ends and the new design begins (the one-screen summary)

```
PROVEN, RUNS TODAY (one org, code artifacts)        →  generalize to general work
  • capture-from-observed-work (codify loop)            (~1 session: taxonomy)
  • proposal lifecycle + versioning (append-only)
  • signed provenance + two-level attribution
  • disclosure scrub on intake
  • variant overlay (replace/add/inherit)              (~1 session: org axis)
  • recall / obsoletion (purge from all consumers)
  • posture-graded run (L3/L4/L5)  — moat M2

NET-NEW, MUST BE BUILT                               →  build order
  • non-coder capture + plain-language review screen     Stage A surface
  • process-level (not just answer-level) capture         (research risk, §3.3)
  • cross-org publish/subscribe surface + discovery       (~3–5 sessions, gated)
  • licensing + attribution for shared artifacts
  • UNTRUSTED-PUBLISHER TRUST MODEL  ◄ the load-bearing 5%; design FIRST
       (no shared enrollment; external signed provenance; sandbox + locked-L3;
        aegis-shape runtime records anchored to consumer's own IdP — §4.3)
```

The flow is honest to its own thesis: **the within-org artifact economy is a near-term build on
proven rails; the cross-org marketplace is the durable moat, and it waits — deliberately — on
the one trust mechanism nobody, including Sequor, has built yet** (`06` §8.3, §8.4; `04` §7.3,
§9.1).

---

## 8. Sources consulted

- Brief: `briefs/01-vision.md` (§3g artifacts shared across orgs; §3a non-coder; §3e posture; §3f transparency; §1b processes vary co-to-co)
- Artifact machinery: `01-analysis/01-research/01-coc-artifact-system.md` (§1 taxonomy; §2 splitter/variant/recall; §2d obsoletion; §3 codify lifecycle; §7 cross-org synthesis + 80/15/5; §7c genuinely-new untrusted-publisher; §7d sizing)
- Platform model: `01-analysis/04-platform-model.md` (§2 core transaction B+D; §3 producers + attribution; §4 consumers + governed-at-install/run; §7 curated marketplace + own-vs-rent layers; §7.3 cons; §9 open questions)
- Network effects: `01-analysis/06-network-effects.md` (§2–6 five behaviors; §7 ranking; §8 two-stage ignition + cold-start; §8.6 symmetric pros/cons)
- Ecosystem DNA (by path): loom `~/repos/loom`; pact `~/repos/terrene/contrib/pact`; eatp `~/repos/loom/kailash-py`; aegis `~/repos/dev/aegis` (fork-relationship asymmetry precedent)
- COC rules (by path): `.claude/rules/artifact-flow.md` (proposal lifecycle, intake scrub, variant overlay), `.claude/rules/multi-operator-coordination.md` (signed identity substrate), `.claude/rules/upstream-issue-hygiene.md` (disclosure redaction), `.claude/rules/recommendation-quality.md`, `.claude/rules/autonomous-execution.md`, `.claude/rules/cross-cli-artifact-hygiene.md`
