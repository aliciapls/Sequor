# Red-Team 03 — Plans + User Flows: Flow-Through, Coherence, Sharding, Honesty

> **Scope.** Adversarial review of `02-plans/` (5 files) and `03-user-flows/` (5 files), with the
> central question from `/analyze`: **does the analysis + the user flows FLOW INTO the plans, and do
> the plans + flows form a coherent, complete, honestly-scoped build?** Graded against the brief
> (`briefs/01-vision.md`) as the authoritative requirement surface, the analysis layer
> (`01-analysis/02`–`09` + `01-research/01`–`09`), and the target-state specs (`specs/`).
>
> **Method.** Every finding carries: unique ID · SEVERITY · exact location · what's wrong · WHY it
> matters · concrete fix. Genuine GAPs are distinguished from stylistic nits. Honesty already present
> in the docs is credited, not re-flagged. First-principles check on the build sequence is in §F.

---

## A. SUMMARY VERDICT

**FIXES-NEEDED.** The plans and flows are unusually strong on grounding, symmetric pros/cons, honesty
about the hard parts (M1 cascade, untrusted-publisher, runtime spike are all confronted, not
hand-waved), and the analysis→plans→flows chain is largely intact and traceable. But there are
**two HIGH cross-document contradictions** (a posture-label collision that the plans themselves warn
against, reproduced verbatim inside a flow; and a flow→spec coverage gap), **one BLOCKING traceability
gap that is structural** (the C4 cross-system-reach and C6 untrusted-publisher capabilities — both
named load-bearing — have no dedicated design plan, only roadmap prose, so the hardest non-M1/M2 work
is under-specified relative to its risk), and a cluster of MEDIUM coherence/coverage issues. None of
these are fatal to the thesis; all are fixable before `/todos`.

**Count by severity:** BLOCKING 1 · HIGH 4 · MEDIUM 9 · LOW 6.

---

## B. FLOW-THROUGH: does analysis + user flows FLOW INTO the plans?

The `/analyze` requirement is the load-bearing test. Verdict per direction:

### B.1 Analysis → Plans (mostly intact, two gaps)

Every plan cites specific analysis sections and the chain resolves. Spot-checked:

- Plan 01 (architecture) ← analysis 07 + 08 + research 03/04/05. Resolves.
- Plan 02 (roadmap) ← analysis 08 + 09 + 03 + research 09. Resolves.
- Plan 03 (cascade) ← analysis 07 + research 06 + research 03. Resolves.
- Plan 04 (posture) ← research 04 + 03 + analysis 07. Resolves.
- Plan 05 (comms) ← research 09 + analysis 04. Resolves.

**GAP (see F1-HIGH):** analysis files **02-value-propositions** and **05-aaa-framework** are cited by
ZERO plan and ZERO flow (`grep` confirmed). Either they are dead analysis (work that produced nothing
downstream) or the plans silently dropped a value-frame the analysis built. A clean `/analyze` should
have every analysis conclusion either flow into a plan or be explicitly retired.

### B.2 User flows → Plans (every flow has a building plan — but two are thin)

| User flow                     | Building plan                              | Coverage                 |
| ----------------------------- | ------------------------------------------ | ------------------------ |
| 01 objective→output           | Plan 01 §9 + Plan 04 + Plan 03             | Full (composes M1+M2+M4) |
| 02 retrace+cascade            | Plan 03 (cascade)                          | Full — 1:1 with the plan |
| 03 team collaboration         | **NO dedicated plan** (Plan 01 §5 L6 only) | **Thin — see F4-HIGH**   |
| 04 artifact authoring/sharing | **NO dedicated plan** (Plan 01 §6 L5 only) | **Thin — see F4-HIGH**   |
| 05 comms wedge                | Plan 05 (comms integration)                | Full — 1:1 with the plan |

**The asymmetry is the finding.** M1 (cascade) and M2 (posture) each got a full dedicated design plan
(Plan 03, Plan 04) AND a user flow. M3 (coordination) and M4 (artifacts) got a _user flow_ each but
only an _architecture-section_ (Plan 01 §5, §6) — no design-grade plan. The user flow for M4 (Flow 04)
is in fact MORE detailed than any plan covering M4. A flow that out-specs its own plan is the inversion
of the intended `/analyze` order (analysis→plan→flow).

### B.3 Plans → Specs (the forward link is intact)

`specs/_index.md` has a target-state spec for every moat/layer the plans describe
(`platform-overview`, `transparency-and-provenance`, `intervention-and-versioning`,
`trust-posture-and-governance`, `coordination-and-teams`, `artifact-system-and-registry`,
`connectors-and-integration`). The runtime-ownership spike (C0) is referenced in 4 specs. Forward
traceability is good. (Spec _content_ accuracy is a separate red-team scope; not graded here.)

---

## C. BLOCKING

### F0-BLOCKING — C4 (cross-system reach) and C6 (untrusted-publisher trust model) are named load-bearing but have NO design plan, only roadmap prose

**Location.** Plan 02 §7 (C4), §9 (C6); Plan 01 §6.4, §7 (architecture-level only). Contrast: M1 has
Plan 03 (full design), M2 has Plan 04 (full design).

**What's wrong.** The roadmap (Plan 02 §10.4 cons; §14) and the risk analysis (analysis 09 §4) both
state that **C4 (one agent across ≥2 formerly-siloed systems)** is "the paradigm-shift proof" and
**C6 (untrusted-publisher trust model)** is "the genuinely-new 5% that gates the entire registry" and
"must be designed FIRST." These are, by the documents' own ranking, the two hardest pieces after M1.
Yet neither has a design-grade plan. C4 lives as ~1.5 pages of roadmap (Plan 02 §7) plus an
architecture section (Plan 01 §7). C6 lives as ~1.5 pages of roadmap (Plan 02 §9) plus Plan 01 §6.4.
Flow 04 §4.3 actually carries MORE design substance on the untrusted-publisher gate than Plan 01/02
do — the _flow_ is doing the _plan's_ job.

**Why it matters.** The brief's core thesis is the **inversion** (agent as integration layer across N
systems — brief §1, §3). C4 is the _only_ proof of that inversion; comms explicitly does NOT prove it
(Plan 05 §6.1; Flow 05 §7.1 — both honest about this). If the platform has a full design plan for the
cascade engine but only roadmap bullets for "can one agent actually orchestrate ERP→document under
governance + least-privilege," the plan set is deepest exactly where the analysis says risk is _not_
uniquely concentrated and shallowest on the thesis-defining proof. C6 is worse: the docs say "design
this FIRST because it constrains the registry," but there is no design — just the instruction to
design it. An instruction to design is not a design. Per `spec-accuracy.md`/`zero-tolerance.md`
discipline ("implement, don't document the gap"), naming the hard thing and deferring its design to a
future phase is acceptable ONLY if the deferral is explicit and the gating is enforced — which it is
in prose, but the _absence of the artifact_ leaves `/todos` with nothing shardable for the two
highest-leverage non-M1 builds.

**Fix.** Before `/todos`, produce two design plans matching Plan 03/04 depth:
(1) **Plan 06 — Cross-system orchestration + governed connectors (C4/L1):** the least-privilege
envelope-derivation mechanism (and how it avoids becoming logic-in-tools, the tension analysis 09 §4.3

- Plan 02 §7.4 both flag), the dumb-endpoint connector wrapper contract, the governance-between-agent-
  and-connector enforcement point, sharded per the capacity budget.
  (2) **Plan 07 — Untrusted-publisher trust model (C6/M4):** the design-first artifact the roadmap keeps
  pointing at — external-publisher signed provenance, the cross-tenant-grant model (analysis 09 §4.4
  names this as net-new beyond tenant_id), capability-scoped intake fence, the aegis-fork-asymmetry
  adaptation. This is the one the docs themselves say must exist _before_ the registry surface.
  Alternatively, if the founder accepts these as deferred-by-design, the deferral must be a stated,
  value-anchored entry (per `value-prioritization.md` MUST-2) — not an implicit thinness.

---

## D. HIGH

### F1-HIGH — Analysis 02 (value-propositions) and 05 (AAA framework) flow into NOTHING

**Location.** `01-analysis/02-value-propositions.md`, `01-analysis/05-aaa-framework.md`; absent from
all 5 plans and all 5 flows (`grep -rl` returns empty).

**What's wrong.** Two of the eight analysis deliverables produce zero downstream artifact. The
`/analyze` contract is research→analysis→plans→flows→specs; an analysis file that no plan or flow
consumes is either (a) orphaned work, or (b) a silently dropped frame. The AAA framework (Agent/
Artifact/Automation, presumably) and the value-propositions are exactly the kind of synthesis a plan's
"why this matters for the business" section should rest on — yet the plans rebuild value framing from
analysis 08/09 instead.

**Why it matters.** Same failure shape as `orphan-detection.md` at the analysis layer: a beautifully
written analysis with no consumer is indistinguishable from analysis that was never needed. It also
risks the plans missing a value axis the analysis deliberately built. A reviewer cannot tell whether
the value-props were _superseded_ by 08/09 (fine — say so) or _forgotten_ (a gap).

**Fix.** Either (a) cite analysis 02 + 05 where the plans make value/positioning claims (Plan 01
§11.1, Plan 02 §10.2 are the natural homes), or (b) add a one-line note in those analysis files'
headers stating they were folded into 08/09 and are retained as derivation, not as live inputs.

### F2-HIGH — Flow 03 reproduces the EXACT posture-label collision Plan 04 §1.1 calls a "trap"

**Location.** `03-user-flows/03-team-collaboration.md` line 126 (the posture table):
`| **L4 Supervised** | Ask once before each consequential step | ...`

**What's wrong.** Plan 04 §1.1 ("The numbering trap the brief walks into — flag it loudly") spends a
full section establishing that **L4 = DELEGATING = ONE gate at the plan→execute boundary**, and that
"ask before **each** consequential step" is **L3/SUPERVISED**, NOT L4. The plan's whole §1.2
recommendation exists to prevent this collision. Flow 03 line 126 then writes the brief's wrong
mapping verbatim: it labels L4 "Supervised" (Plan 04: that name belongs to L3) AND assigns it the
per-step behavior ("ask once before **each** consequential step") that Plan 04 explicitly says is L3's
behavior, not L4's. Flow 01 §6 and Flow 04 §2.4 and Flow 05 §3 get it right (L4 = "asks once before it
starts" / "one approval at the plan boundary"). Flow 03 is the outlier and it is internally
self-contradictory too: line 130–133 then describes L4 correctly as "agents draft freely, a
consequential step pauses" — but the table at 126 says "ask once before EACH consequential step,"
which is the L3 semantics.

**Why it matters.** This is the single most concrete coherence defect in the set. A user flow is the
"literal walk" a non-coder reads (`user-flow-validation.md`); shipping the exact label collision the
governing plan was written to prevent means the flow teaches the wrong mental model. Worse, it is the
_team_ flow — the one where a wrong posture (Marcus thinks L4 gates every step; it gates once)
directly changes who-approves-what, the load-bearing safety property of §6 (the intervention climax).

**Fix.** Rewrite Flow 03 line 126 to match Plan 04 §1.2: `| **L4** ("Ask me once") | One approval at
the plan→execute boundary; then auto-approve inside scope | "Check with me once before it runs" |`.
Use the user-facing button names ("Go ahead"/"Ask me once"/"Step through with me") that every other
flow uses, and drop the bare "Supervised" label (Plan 04's whole point: never surface the engine enum
name, especially the one that means the opposite of the brief's intent).

### F3-HIGH — Flow 01 silently uses (L5)/(L4)/(L3) labels without surfacing the numbering trap, and asserts an "L4=Supervised"-adjacent framing

**Location.** `03-user-flows/01-objective-to-output.md` — uses "(L5)", "(L4)", "(L3)" throughout (§4,
§5, §6 table) including "**Ask me once** (L4)" and "**Step through with me** (L3)".

**What's wrong.** Flow 01 maps the buttons correctly to behavior, BUT it stamps them with the bare
"L4"/"L3" engine numbers without the disambiguation Plan 04 insists is mandatory — and the brief
itself (§3e) calls L4 "Supervised" meaning the opposite. Flow 01 §6's table header row "Engine posture
(internal)" correctly says L4=DELEGATING — good — but the rest of the document leads with "L4"/"L3" as
if they were stable user-facing labels. Plan 04 §1.2 cons explicitly warn this mapping "is a convention
we must document and pin, or a future contributor re-introduces the collision." Flow 01 + Flow 03 +
Flow 04 + Flow 05 collectively use the L-numbers four different ways relative to the brief's three.

**Why it matters.** Less severe than F2 (Flow 01's _behavior_ descriptions are correct), but it
propagates the unpinned convention. A non-coder reading Flow 01 ("L4") then Flow 03 ("L4 Supervised =
each step") gets two different meanings for "L4." The brief's own §3e labels (L5/L4/L3) are the ones
the plans say to NOT ship.

**Fix.** Across all flows, lead with the three plain-language button names only; relegate the engine
enum (AUTONOMOUS/DELEGATING/SUPERVISED) to a single "internal" row as Flow 01 §6 already does; and add
one sentence per flow ("the brief's L5/L4/L3 numbers are the _user's autonomy ladder_, not the
engine's internal enum — see Plan 04 §1.1") so the collision is pinned, not silently inherited.

### F4-HIGH — M3 and M4 user flows out-detail their own plans (the analyze→plan→flow order is inverted)

**Location.** Flow 03 (team) vs Plan 01 §5 (the only M3 plan content); Flow 04 (artifacts) vs Plan 01
§6 (the only M4 plan content). See B.2.

**What's wrong.** Per the workspace phase contract, `/analyze` produces plans THEN flows; a flow is
the walk of what the plan specifies. For M3/M4 the relationship is reversed: Flow 03 specifies the
agent-identity enrollment ceremony, two-level attribution, the reap ceremony, the informal-mode
governance boundary, and the SAME-vs-merge per-work-item-type decision in more operational detail than
any plan. Flow 04 specifies the untrusted-publisher gate UX, the disclosure-scrub-at-org-boundary, the
licensing model, and the variant-overlay-for-orgs in more detail than Plan 01 §6.

**Why it matters.** This is the structural twin of F0. When the flow is the deepest artifact, `/todos`
will shard from the flow — but flows are narration, not shardable design (no invariant lists, no
shard maps, no sizing). Plan 03 and Plan 04 give `/todos` shard maps (Plan 03 §6.1, Plan 04 §9.3);
the M3/M4 flows give none. The build will be under-specified for two of four moats.

**Fix.** Promote the design content currently embedded in Flow 03 and Flow 04 into Plan 06/07 (or a
Plan 08 for M3 coordination), each with the invariant list + shard map + sizing that Plan 03/04 model.
Leave the flows as walks that _consume_ those plans. This also resolves F0's C6 half.

---

## E. MEDIUM

### F5-MEDIUM — The cascade cost-preview is "a hard acceptance gate" but its accuracy is unproven and the flows present specific dollar figures

**Location.** Plan 03 §8.4 #3 + Flow 02 §3.2 (the `~$0.12` preview box) + Flow 02 §3.3 (flagged) +
Flow 01 §8 #7.

**What's wrong.** The cost-preview is correctly elevated to a hard gate (good — Plan 02 §8.2, analysis
09 §2.3). Plan 03 §8.4 #3 and Flow 02 §3.3 both honestly flag that the _estimate accuracy_ is an open
design point (LLM cost varies run-to-run). But the flows render concrete numbers (`~40 seconds`,
`about $0.12`, `2 AI calls`) in UI mockups that a non-coder reader will anchor on. The honesty caveat
is present but buried below the mockup.

**Why it matters.** The gate's entire value is trust ("a non-coder must never trigger a big expensive
recompute by accident" — Flow 02 §3.1). If the estimate is routinely wrong, the gate erodes the trust
it exists to build — exactly the legibility failure mode analysis 09 §2.3 names as the M1 canary. The
docs flag this but the mockups undercut the flag.

**Fix.** This is largely already handled (Flow 02 §3.3 + §8 row 3 label it an estimate). Tighten: have
the mockup itself show the "~" and a one-line "estimates can vary" inside the box, not only in prose
below it. And add to Plan 03 §8.4 #3 a _calibration acceptance criterion_ (e.g. "estimate within ±X%
of actual on the comms-wedge fixture before the gate ships") so the open point has a closing condition.

### F6-MEDIUM — "Re-run vs replay" per-step choice is pushed onto the non-coder, and the docs admit it may confuse — but no fallback if it does

**Location.** Plan 03 §4.2 cons (a); Flow 01 §5 + §8 #2; Flow 02 §4.3 + §8.

**What's wrong.** The design surfaces an explicit "re-figure with my edit / keep recorded output"
choice on the edited step (correct — guessing silently is worst, per Plan 03 §4.2). All docs honestly
flag this as a real conceptual burden that "may confuse non-coders" and "is resolved only by testing"
(Flow 02 §8 #2). Good honesty. But there is **no stated fallback** for the case where testing confirms
it DOES confuse — the docs name the risk and stop. A risk this central (it's the second-ranked
usability unknown in three documents) should carry at least a candidate mitigation.

**Why it matters.** Per `recommendation-quality.md`, surfacing a risk without a path under each branch
is a partial recommendation. "We'll test it" is not a mitigation if the test fails. The whole signature
gesture (Step 5) hangs on this choice landing.

**Fix.** Add to Plan 03 §4.2 a fallback branch: e.g., "if user-testing shows the per-step choice
confuses, default to _keep-recorded_ (the conservative path) and move 'regenerate' to an advanced/
explicit affordance, accepting the con that some users get a stale-prose result they must manually
re-trigger." Name the path under the failing branch, per recommendation-quality.

### F7-MEDIUM — Plan 02 sequences C2‖C3 parallel and C4 after, but the single end-to-end demo (§12) needs C3+C4+C5 together — the critical path is longer than the "short time-to-first-capability" headline implies

**Location.** Plan 02 §10.1 (sequence) vs §12 (the demo needs C0+C1+C2+C3+C4+C5) vs §10.2 ("time-to-
first-capability is short").

**What's wrong.** The roadmap headline is "time-to-first-evidence is short and cheap" (C0+C1 ≈ 2–3
cycles). True for _evidence_. But the _capability-proven demo_ (§12) — the actual deliverable that
proves the thesis — requires C0→C5 inclusive, where C3 is "multiple cycles (bulk net-new UX)" and C5
is "~4–6 cycles, MUST shard." The demo's critical path is C0→C1→(C2‖C3)→C4→C5, and C3 (open-ended UX)
plus C5 (the headline engine) dominate. The "short" framing applies to the falsifiers, not the demo;
a reader can conflate them.

**Why it matters.** Not a flaw in the sequence (the sequence is sound — see F-section), but a framing
risk. A founder reading "short time-to-first-capability" alongside "C3 is multiple open-ended cycles
and is the dominant net-new UX" can mis-estimate the path to the demo that actually matters.

**Fix.** In Plan 02 §10.2, separate "time-to-first-_evidence_" (C0+C1, short) from "time-to-
capability-_demo_" (C0→C5, dominated by C3+C5, longer and partly open-ended). Both are already stated
separately in the body; make the headline distinguish them.

### F8-MEDIUM — Flow 03 §3.3 leaves the SAME=halt-vs-merge decision open "per work-item type" — an unbounded, never-finished design surface presented as a v1 flow

**Location.** Flow 03 §3.3 + §10 #2; analysis (02-multi-operator) cited there.

**What's wrong.** The flow honestly flags that SAME-class conflict should halt for system-of-record
writes but merge-surface for collaborative prose, "a per-task-type decision… never finished… ~1–2
cycles per work-item-type family." This is correct analysis but it means the team flow's core
mechanism (claims/conflict-classes) has an _open, unbounded_ policy surface at its heart, with no v1
cut stated. Contrast M1, which got a crisp v1 cut (linear, no branching). M3's conflict policy gets no
equivalent "v1 ships X, defers Y."

**Why it matters.** Without a v1 cut, the team flow is unshippable as specified — every new work-item
type reopens the halt-vs-merge call. The M1 flow shows the right pattern (deliberately-reduced v1);
the M3 flow doesn't apply it.

**Fix.** State a v1 cut in Flow 03 §3.3 / the future Plan 08: "v1 ships SAME→halt universally (the
safe, code-proven default); merge-surface for prose is deferred post-v1, gated on usability evidence,"
mirroring M1's linear-first discipline.

### F9-MEDIUM — Agent-identity enrollment + two-level attribution is net-new "greenfield ~2–3 cycles" and is a prerequisite for BOTH Flow 03 and Flow 04, but appears in neither plan's shard map

**Location.** Flow 03 §5.2 + §9 (net-new); Flow 04 §2.3 (two-level attribution used as if it exists).

**What's wrong.** "Agents get their own enrolled identity → output attributable to agent AND
accountable human" is named net-new greenfield in Flow 03 §5.2/§9. Flow 04 §2.3 then _relies_ on
"two-level attribution" as a delivered property of the artifact-save. This shared prerequisite has no
plan, no shard map, no sizing beyond "~2–3 cycles" buried in a flow. It gates the M3 climax (§6, the
named-human-signs-the-decision gate) AND the M4 provenance claim.

**Why it matters.** A cross-cutting net-new primitive that two flows depend on, with no plan home, is
an orphan-in-waiting: `/todos` may shard the consumers (Flow 03/04 surfaces) without the producer
(the identity ceremony), reproducing the Phase-5.11 pattern at the workspace-planning layer.

**Fix.** Give agent-identity-enrollment + two-level attribution a plan section (in the future M3 plan)
with its own shard, invariant list (the binding must be established at delegation time per Flow 03 §10
#4), and a Tier-2 wiring test requirement — and make Flow 03/04 cite it as a dependency.

### F10-MEDIUM — Plan 05 + Flow 05 prove "posture as mechanism" on comms but explicitly do NOT exercise the brief's user-chosen-posture UX — the gap is honest but leaves the brief's §3e under-proven by the wedge

**Location.** Plan 05 §3.2 (keep posture invisible-by-default), §6.4; Flow 05 §3 [PLATFORM-LENS]

- §7.4.

**What's wrong.** This is _honest_ (credited — see §G), not a defect of honesty. The coherence issue:
the comms wedge is the platform's only live proof surface, and it deliberately does NOT surface the
user-facing L3/L4/L5 choice (to protect comms' non-technical onboarding budget). So the brief's §3e
"user picks posture beforehand" UX is proven by NO shipping surface — it lives only in target-state
Flow 01. The wedge proves the _engine_; nothing proves the _choice UX_ against real users until the
platform build ships it.

**Why it matters.** Analysis 09 §2 ranks non-coder legibility as the dominant M-series risk, and the
posture-choice UX is part of that frontier. The plan set leaves the single most user-facing governance
decision (which button) unvalidated by the one real-user asset. This is acceptable IF stated as a
deliberate deferral with a validation path; currently it's stated as a comms-scope boundary only.

**Fix.** Add to Plan 04 §10 (or the comms plan §6.4) an explicit note: "the posture-choice UX is NOT
validated by the wedge by design; its first real-user validation is the C3 self-service surface — flag
it as a distinct usability bet, not covered by the lighthouse." This connects the comms-boundary
honesty to the C3 build so the gap has an owner.

### F11-MEDIUM — Plan 04 §9.1 and Plan 02 C2 mandate replacing PACT's keyword classifier with an LLM-judged one "on every action," with caching "unproven at scale" — flagged but not sized as a gating spike

**Location.** Plan 04 §9.1 #1 + §10 #2; Plan 02 §5.3; Flow 01 §5 + §8 #3.

**What's wrong.** The LLM-first consequentiality classifier is mandatory (CLAUDE.md Directive 6) and
correctly flagged as carrying real latency/cost (an LLM call per action). The mitigation ("judge once
per step-type, cache") is repeatedly called "unproven at scale." But unlike the runtime-ownership
question, this never gets elevated to a _gating spike_ with a pass/fail criterion — it's a standing
caveat. A per-action LLM call that's too slow/costly would degrade every posture flow (especially L3
step-through, Flow 05 §5 / Flow 01 §5).

**Why it matters.** This is a _known_ hard problem with a _named_ mitigation whose viability is
unproven — exactly the shape that warrants a cheap early spike (like C0/C1), not a perpetual caveat.
Left un-spiked, it surfaces at C2 implementation as a latency wall.

**Fix.** Add a C-step or a sub-spike to Plan 02: "classifier-caching spike — prove per-step-type
verdict caching keeps p95 added latency under [threshold] on the comms-wedge flow, before C2 enforce."
Give it a falsifier, like C0/C1.

### F12-MEDIUM — Storage growth / retention has no v1 policy across three plans that all flag it

**Location.** Plan 01 §11.2 cons; Plan 03 §8.3 row 5 + §8.4 #5; Flow 02 §8 row 5.

**What's wrong.** "Every version kept forever; content-addressing dedupes bytes not version count;
retention policy owed before scale" is flagged in three places — but "before scale" has no trigger and
no v1 stance. The docs defer it without a closing condition.

**Why it matters.** Immutable-version-forever is correct for v1 (simplest correct behavior) but the
deferral is open-ended; an immutable ledger under real comms traffic (the lighthouse) accrues
unbounded storage with no stated review point. `spec-accuracy.md` discipline: a deferred operational
policy needs an owner and a trigger, not just "owed."

**Fix.** State the v1 stance + the trigger: "v1 keeps all versions; a retention/compaction policy is
required before [N versions / [size] / first paying multi-tenant deployment]; tracked as a deferred
item with that trigger." aegis `compaction-checkpoint` is already named as the precedent.

### F13-MEDIUM — Plan 02's "single capability-proven demo" (§12) and Flow 01 both run the 3Q example, but the demo claims C4 (≥2 real systems) while Flow 01's systems are "accounting" + "sales" — which is comms-adjacent, not the heterogeneous ERP/CRM case the risk doc says is the real test

**Location.** Plan 02 §12.2 (demo: "read from records/ledger system, write to document system"); Flow
01 §3 (accounting system + sales system); analysis 09 §1.4 cons + Appendix-B (comms is "easier" than
ERP/CRM; a clean result on the easy case gives false confidence).

**What's wrong.** The demo and Flow 01 both instantiate C4 with two systems that are _read-ledger +
write-document_ — structurally close to comms' single-cluster shape. Analysis 09 explicitly warns that
a clean result on a representative-but-easy case (comms-class) gives "false confidence about the hard
heterogeneous-systems case." The demo's C4 claim ("formerly-siloed systems that needed a human to
bridge them") is technically met by ledger+document but doesn't stress the heterogeneity (auth models,
schema mismatch, write-side governance) that analysis 09 §4 says is the actual risk.

**Why it matters.** The capability-proven demo is the thesis's falsifier. If its C4 instantiation is
soft, a green demo can pass while the genuine cross-system-orchestration risk stays unproven —
precisely the false-confidence trap the risk doc names.

**Fix.** Either (a) state in Plan 02 §12.3 that the demo's C4 is deliberately the _easy_ heterogeneity
case and a harder ERP/CRM-class C4 is a separate, later proof (honest deferral), or (b) instantiate the
demo's two systems as genuinely heterogeneous (e.g., a real ERP read + a CRM write) to actually stress
C4. Option (a) is cheaper and matches the reduced-form discipline; just say it.

---

## F. FIRST-PRINCIPLES: is the build sequence the most elegant decomposition?

The C0→C7 sequence (Plan 02) is, on the whole, **well-reasoned and close to optimal**: cheapest
decisive falsifiers first (C0 runtime spike, C1 single-step replay), most-proven moat next (C2), the
two net-new builds (C3 surface, C5 cascade) in the middle, design-first gate before cross-org (C6),
unproven bets measured last (C7). This correctly front-loads thesis-killers and back-loads
unfalsifiable bets. Credit given.

Three first-principles observations (one is a finding, two are confirmations):

- **F14-MEDIUM — C1 (single-step replay) may be redundant with C0's third check.** C0's falsifier
  includes "re-execute from a prior recorded step with downstream re-derivation" (Plan 02 §3.2); C1
  proves "record one step + replay deterministically" (Plan 02 §4.2). C0 already tests replay-from-step
  as part of the runtime decision. C1 then re-proves a subset on the chosen runtime. This may be
  correct (C0 is throwaway-spike, C1 is on production substrate) but the docs don't distinguish _what
  C1 proves that C0 didn't_ crisply — C1's §4.2 falsifier ("step can't fingerprint stably") is a
  _different_ property (content-addressing) than C0's (loop introspection). **Fix:** state explicitly
  that C1 proves the _content-addressing/fingerprint_ substrate (not re-proving C0's loop-control
  finding); otherwise C1 reads as partial duplication. Minor — the sequence is fine, the framing
  overlaps.

- **Confirmation (not a finding):** the decision to ship C2 (governance) before C5 (cascade) because
  C2 produces the posture-stamped log C5 reads is genuinely elegant — it makes the dependency do
  double duty (de-risk + produce-input). This is the strongest sequencing call in the plan.

- **Confirmation (not a finding):** proving everything on the comms-wedge 4-step graph before
  generalizing is the right reduction — small enough for non-coder legibility to be _achievable_ (the
  named dominant risk). Correct.

**Simpler decomposition considered:** could C3 (the open-ended self-service surface) be deferred past
the capability-proven demo, shrinking the critical path? No — Plan 02 §6.4 correctly couples C3+C5 (the
"last 20%" survives only because transparency makes depth legible), so C3 can't be cut from the demo.
The coupling is real and the sequence respects it. The decomposition is close to optimal; the gaps are
in _plan depth_ (F0/F4) not _sequence_.

---

## G. HONESTY ALREADY PRESENT (credited, NOT re-flagged)

These docs are unusually disciplined about confronting the hard parts. The following are done well and
must not be "fixed":

- **M1 cascade non-determinism** is confronted head-on (Plan 03 §4, Flow 02 §4.3) with the re-run/
  replay/branch trichotomy and the explicit "guessing silently is the worst outcome." Not hand-waved.
- **Untrusted-publisher** is repeatedly and correctly named as the genuinely-new, unbuilt, must-design-
  first 5% (Flow 04 §4.3, Plan 02 §9, Plan 01 §6.4). The honesty is exemplary even though the _design_
  is missing (F0).
- **Runtime-ownership spike (C0)** is correctly elevated to the gating falsifier, with an honest "the
  evidence tilts toward own-the-loop but the spike converts tilt to evidence" (Plan 02 §3.2).
- **Comms proves the spine, not the orchestration** is stated plainly and repeatedly (Plan 05 §6,
  Flow 05 §7) — the lighthouse-vs-harbour boundary is honest, not over-read.
- **Agent-comms hypothesis is a BET, not a USP** — Flow 03 §8 + Plan 02 §11.1 + analysis 09 §3 all
  refuse to stake value on it and ship the informal-mode guardrail. Correct restraint.
- **Linear-retrace-no-branching v1 cut** (Plan 03 §4.3, Flow 02 §2.3, §8) is the right reduced-form
  discipline, with symmetric cons stated. Model behavior for the rest of the plan set (cf. F8).
- **Traceability-not-accountability** caveat travels with every trust claim (Plan 03 §2.3, Plan 04
  §7.4, Flow 01 §4, Flow 02 §1.2). Consistently honest.
- **Orphan-detection discipline** is invoked everywhere governance is reused (Plan 01 §3.5, Plan 02
  C2, Plan 03 §6.1, Plan 04 §9.4 cons) — the right structural defense for PACT's facade-heaviness.

---

## H. LOW (nits, not gaps)

- **F15-LOW.** Flow 05 is titled "05 — User Flow:" while the other four use "User Flow 0N —". Cosmetic
  inconsistency in the flow set's titling.
- **F16-LOW.** Plan 05 is titled "05 — Comms-Wedge Integration Plan" while Plans 01–04 use "Plan 0N —".
  Same cosmetic drift.
- **F17-LOW.** Flow 04 and Flow 02 cite ecosystem repo paths (`~/repos/dev/aegis`, `~/repos/loom`)
  inline. Per `cross-cli-artifact-hygiene.md` these are fine as historical/grounding citations, but
  several appear in prescriptive prose ("the candidate mechanism is loom's..."). Prefer citing the
  rule/concept over the absolute path in prescriptive sentences.
- **F18-LOW.** Plan 02 §13's one-screen ledger is excellent but duplicates Plan 02 §2's diagram +ledger;
  minor redundancy (acceptable as a summary table).
- **F19-LOW.** Flow 01 §3 mockup shows "Estimated cost: about $4" and "$1.80 of $4.00"; Flow 02 shows
  "$0.12". Cross-flow the dollar magnitudes are illustrative but inconsistent enough that a reader may
  treat them as real pricing. Label all UI dollar figures "illustrative."
- **F20-LOW.** The 80/15/5 reuse ratio is asserted in every plan but the exact split shifts subtly
  (Plan 01 §10 vs Plan 04 §0 "~80/15/5" vs Plan 02 §0 "~80% / ~5%"). Pin one canonical statement and
  cite it, rather than restating with drift.

---

## I. DISPOSITION CHECKLIST (for the founder gate)

1. **BLOCKING (F0):** produce design plans for C4 (cross-system/connectors) and C6 (untrusted-
   publisher) at Plan 03/04 depth, OR record them as explicit value-anchored deferrals.
2. **HIGH (F2, F3):** fix the posture-label collision in Flow 03 line 126 and pin the L-number
   convention across all five flows.
3. **HIGH (F1):** wire analysis 02 + 05 into the plans, or mark them folded-into-08/09.
4. **HIGH (F4):** promote M3/M4 flow design-content into plans with shard maps.
5. **MEDIUM cluster (F5–F13):** close each open design point with a v1 stance + trigger/falsifier.
6. **The sequence itself (F-section): SOUND.** Do not re-order. Fix depth, not order.

---

### VERDICT: FIXES-NEEDED — BLOCKING 1 · HIGH 4 · MEDIUM 9 · LOW 6
